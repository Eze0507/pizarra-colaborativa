"""
Consumer WebSocket para la pizarra colaborativa en tiempo real.
Gestiona:
1. Autenticación de colaboradores y validación de permisos de acceso al proyecto.
2. Eventos efímeros (mover_entidad, cursor_posicion) como PURA RETRANSMISIÓN por Redis (0 consultas a PostgreSQL).
3. Exclusión mutua (bloquear_entidad, desbloquear_entidad) para evitar colisiones de edición.
4. Evento de persistencia controlada (guardar_snapshot) tras inactividad (debounce) en PostgreSQL.
"""
import json
from django.db import transaction
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Proyecto, Entidad, Atributo, Operacion, ParametroOperacion, Relacion
from .permissions import ProjectAction, user_id_can_project_action
from .realtime import get_proyecto_group_name
from .consistency import InvalidExpectedRevision, StaleRevision, lock_project_for_write


def sanitize_keys_to_str(obj):
    """
    Convierte recursivamente todas las claves de diccionarios a cadenas (str)
    para cumplir con strict_map_key=True de msgpack en RedisChannelLayer.
    """
    if isinstance(obj, dict):
        return {str(k): sanitize_keys_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_keys_to_str(elem) for elem in obj]
    return obj


class PizarraConsumer(AsyncWebsocketConsumer):
    """
    Consumer asíncrono para coordinar la interacción concurrente
    en la pizarra virtual de un proyecto específico.
    """
    # Registro en memoria por proyecto: proyecto_id (str) -> { channel_name: { usuario_id, username, first_name, email } }
    _conexiones_por_proyecto = {}
    _acciones_cliente = frozenset({
        'mover_entidad', 'entidad_movida', 'cursor_posicion', 'cursor_movido',
        'bloquear_entidad', 'entidad_bloqueada', 'desbloquear_entidad', 'entidad_desbloqueada',
        'crear_entidad', 'entidad_creada', 'actualizar_entidad', 'entidad_actualizada',
        'eliminar_entidad', 'entidad_eliminada', 'crear_relacion', 'relacion_creada',
        'actualizar_relacion', 'relacion_actualizada', 'eliminar_relacion', 'relacion_eliminada',
        'guardar_snapshot', 'guardar_snapshot_diagrama', 'renombrar_proyecto', 'proyecto_renombrado',
    })
    _acciones_estructurales_pendientes = frozenset({
        'crear_entidad', 'entidad_creada', 'actualizar_entidad', 'entidad_actualizada',
        'eliminar_entidad', 'entidad_eliminada', 'crear_relacion', 'relacion_creada',
        'actualizar_relacion', 'relacion_actualizada', 'eliminar_relacion', 'relacion_eliminada',
    })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.proyecto_id = None
        self.room_group_name = None
        self.user = None
        # Conjunto de entidades bloqueadas por esta conexión para liberación automática al salir
        self.bloqueos_activos = set()

    async def _group_send(self, event):
        """
        Envía un mensaje al grupo Redis asegurando que todos los diccionarios
        tengan exclusivamente claves string para evitar errores de msgpack (strict_map_key=True).
        """
        sanitized = sanitize_keys_to_str(event)
        await self.channel_layer.group_send(self.room_group_name, sanitized)

    async def connect(self):
        self.user = self.scope.get('user')
        raw_proyecto_id = self.scope.get('url_route', {}).get('kwargs', {}).get('proyecto_id')
        try:
            # re_path entrega los grupos capturados como texto. El contrato REST/WS
            # publica proyecto_id como numero y el frontend lo compara estrictamente.
            self.proyecto_id = int(raw_proyecto_id)
        except (TypeError, ValueError):
            await self.close(code=4003)
            return
        self.room_group_name = get_proyecto_group_name(self.proyecto_id)

        # 1. Validar autenticación
        if not self.user or not self.user.is_authenticated:
            # 4003: Forbidden / No autenticado
            await self.close(code=4003)
            return

        # 2. Validar pertenencia o acceso al proyecto
        tiene_acceso = await self._verificar_permiso_proyecto(ProjectAction.READ)
        if not tiene_acceso:
            await self.close(code=4003)
            return

        # 3. Unirse al grupo Redis del proyecto
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # 4. Aceptar la conexión WebSocket
        await self.accept()

        # 5. Registrar conexión de usuario en la sala
        proyecto_key = str(self.proyecto_id)
        if proyecto_key not in PizarraConsumer._conexiones_por_proyecto:
            PizarraConsumer._conexiones_por_proyecto[proyecto_key] = {}

        PizarraConsumer._conexiones_por_proyecto[proyecto_key][self.channel_name] = {
            "usuario_id": self.user.id,
            "username": self.user.username,
            "first_name": self.user.first_name or "",
            "email": self.user.email or ""
        }

        # 6. Enviar al usuario conectado la lista de usuarios actualmente en la sala
        usuarios_unicos = {}
        for conn in PizarraConsumer._conexiones_por_proyecto[proyecto_key].values():
            u_id = conn["usuario_id"]
            if u_id not in usuarios_unicos:
                usuarios_unicos[u_id] = conn

        await self.send(text_data=json.dumps({
            "accion": "usuarios_conectados",
            "evento": "usuarios_conectados",
            "usuarios": list(usuarios_unicos.values()),
            "data": {
                "usuarios": list(usuarios_unicos.values())
            }
        }))

        # 7. Notificar presencia al grupo de colaboradores (omitiendo remitente)
        await self._group_send(
            {
                "type": "pizarra.evento",
                "evento": "colaborador_unido",
                "omitir_remitente": True,
                "remitente_channel": self.channel_name,
                "data": {
                    "usuario_id": self.user.id,
                    "username": self.user.username,
                    "first_name": self.user.first_name,
                    "email": self.user.email
                }
            }
        )

    async def disconnect(self, close_code):
        if self.room_group_name:
            await self._release_connection_locks()
            # 1. Liberar automáticamente cualquier entidad bloqueada por este usuario (Exclusión mutua)
            if self.bloqueos_activos:
                for entidad_id in list(self.bloqueos_activos):
                    await self._group_send(
                        {
                            "type": "pizarra.evento",
                            "evento": "entidad_desbloqueada",
                            "data": {
                                "entidad_id": entidad_id,
                                "desbloqueado_por": self.user.username if self.user else "desconocido",
                                "motivo": "desconexion_colaborador"
                            }
                        }
                    )
                self.bloqueos_activos.clear()

            # 2. Desregistrar conexión y notificar si ya no tiene más canales activos en este proyecto
            proyecto_key = str(self.proyecto_id)
            quedan_del_usuario = False
            if proyecto_key in PizarraConsumer._conexiones_por_proyecto:
                PizarraConsumer._conexiones_por_proyecto[proyecto_key].pop(self.channel_name, None)
                quedan_del_usuario = any(
                    c["usuario_id"] == self.user.id
                    for c in PizarraConsumer._conexiones_por_proyecto[proyecto_key].values()
                )
                if not PizarraConsumer._conexiones_por_proyecto[proyecto_key]:
                    del PizarraConsumer._conexiones_por_proyecto[proyecto_key]

            if not quedan_del_usuario and self.user and self.user.is_authenticated:
                await self._group_send(
                    {
                        "type": "pizarra.evento",
                        "evento": "colaborador_salido",
                        "data": {
                            "usuario_id": self.user.id,
                            "username": self.user.username
                        }
                    }
                )

            # 3. Abandonar el grupo en Redis
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data=None, bytes_data=None):
        """
        Punto de entrada de mensajes WebSocket desde el cliente.
        Separa estrictamente los eventos efímeros (sin BD) del evento de persistencia (snapshot).
        """
        if not text_data:
            return

        try:
            payload = json.loads(text_data)
        except Exception:
            return

        accion = (
            payload.get('accion') or
            payload.get('action') or
            payload.get('evento') or
            payload.get('type')
        )

        if not isinstance(accion, str) or accion not in self._acciones_cliente:
            await self.send(text_data=json.dumps({
                "accion": "comando_rechazado",
                "detail": "El comando WebSocket no está permitido.",
            }))
            return

        if not await self._verificar_permiso_proyecto(ProjectAction.WRITE):
            if not await self._verificar_permiso_proyecto(ProjectAction.READ):
                await self._revocar_conexion()
            else:
                await self.send(text_data=json.dumps({
                    "accion": "permiso_denegado",
                    "detail": "Tu rol permite consultar el diagrama, pero no modificarlo.",
                }))
            return

        # Los cambios estructurales ya existen localmente en JointJS, pero no se
        # publican como autoridad hasta que guardar_snapshot confirme el lote.
        if accion in self._acciones_estructurales_pendientes:
            return

        # -------------------------------------------------------------
        # A. EVENTOS EFÍMEROS: PURA RETRANSMISIÓN (0 CONSULTAS A LA BD)
        # -------------------------------------------------------------
        if accion in ('mover_entidad', 'entidad_movida'):
            # Movimiento en vivo durante el drag: retransmisión instantánea a Redis
            x = payload.get('x') if payload.get('x') is not None else payload.get('coord_x')
            y = payload.get('y') if payload.get('y') is not None else payload.get('coord_y')
            entidad_id = payload.get("entidad_id")

            if entidad_id is not None and x is not None and y is not None:
                await self._group_send(
                    {
                        "type": "pizarra.evento",
                        "evento": "mover_entidad",
                        "omitir_remitente": True,
                        "remitente_channel": self.channel_name,
                        "data": {
                            "entidad_id": entidad_id,
                            "x": x,
                            "y": y,
                            "coord_x": x,
                            "coord_y": y,
                            "usuario_id": self.user.id
                        }
                    }
                )

        elif accion in ('cursor_posicion', 'cursor_movido'):
            # Movimiento del puntero del ratón: retransmisión instantánea a Redis
            await self._group_send(
                {
                    "type": "pizarra.evento",
                    "evento": "cursor_movido",
                    "omitir_remitente": True,
                    "remitente_channel": self.channel_name,
                    "data": {
                        "usuario_id": self.user.id,
                        "username": self.user.username,
                        "x": payload.get("x"),
                        "y": payload.get("y")
                    }
                }
            )

        # -------------------------------------------------------------
        # B. EXCLUSIÓN MUTUA: BLOQUEO Y DESBLOQUEO DE EDICIÓN
        # -------------------------------------------------------------
        elif accion in ('bloquear_entidad', 'entidad_bloqueada'):
            entidad_id = payload.get("entidad_id")
            if entidad_id is not None:
                if not await self._edit_lock(entidad_id):
                    await self.send(text_data=json.dumps({"accion": "comando_rechazado", "codigo": "element_locked", "mensaje": "Otro colaborador está editando este elemento."}))
                    return
                self.bloqueos_activos.add(entidad_id)
                await self._group_send(
                    {
                        "type": "pizarra.evento",
                        "evento": "entidad_bloqueada",
                        "data": {
                            "entidad_id": entidad_id,
                            "usuario_id": self.user.id,
                            "bloqueado_por": {
                                "usuario_id": self.user.id,
                                "username": self.user.username
                            }
                        }
                    }
                )

        elif accion in ('desbloquear_entidad', 'entidad_desbloqueada'):
            entidad_id = payload.get("entidad_id")
            if entidad_id is not None:
                await self._edit_lock(entidad_id, release=True)
                self.bloqueos_activos.discard(entidad_id)
                await self._group_send(
                    {
                        "type": "pizarra.evento",
                        "evento": "entidad_desbloqueada",
                        "data": {
                            "entidad_id": entidad_id,
                            "usuario_id": self.user.id,
                            "desbloqueado_por": self.user.username
                        }
                    }
                )

        # -------------------------------------------------------------
        # C. CREACIÓN, ACTUALIZACIÓN Y ELIMINACIÓN DE ENTIDADES EN RAM
        # -------------------------------------------------------------
        elif accion in ('crear_entidad', 'entidad_creada'):
            entidad_data = payload.get("entidad") or payload.get("data")
            if entidad_data:
                await self._group_send(
                    {
                        "type": "pizarra.evento",
                        "evento": "entidad_creada",
                        "omitir_remitente": True,
                        "remitente_channel": self.channel_name,
                        "data": {
                            "entidad": entidad_data,
                            "usuario_id": self.user.id,
                            "username": self.user.username
                        }
                    }
                )

        elif accion in ('actualizar_entidad', 'entidad_actualizada'):
            entidad_data = payload.get("entidad") or payload.get("data")
            if entidad_data:
                await self._group_send(
                    {
                        "type": "pizarra.evento",
                        "evento": "entidad_actualizada",
                        "omitir_remitente": True,
                        "remitente_channel": self.channel_name,
                        "data": {
                            "entidad": entidad_data,
                            "usuario_id": self.user.id,
                            "username": self.user.username
                        }
                    }
                )

        elif accion in ('eliminar_entidad', 'entidad_eliminada'):
            entidad_id = payload.get("entidad_id")
            if entidad_id is not None:
                await self._group_send(
                    {
                        "type": "pizarra.evento",
                        "evento": "entidad_eliminada",
                        "omitir_remitente": True,
                        "remitente_channel": self.channel_name,
                        "data": {
                            "entidad_id": entidad_id,
                            "usuario_id": self.user.id,
                            "username": self.user.username
                        }
                    }
                )

        # -------------------------------------------------------------
        # D. CREACIÓN Y ELIMINACIÓN DE RELACIONES EN RAM (0 CONSULTAS SQL)
        # -------------------------------------------------------------
        elif accion in ('crear_relacion', 'relacion_creada'):
            relacion_data = payload.get("relacion") or payload.get("data")
            if relacion_data:
                await self._group_send(
                    {
                        "type": "pizarra.evento",
                        "evento": "relacion_creada",
                        "omitir_remitente": True,
                        "remitente_channel": self.channel_name,
                        "data": {
                            "relacion": relacion_data,
                            "usuario_id": self.user.id,
                            "username": self.user.username
                        }
                    }
                )

        elif accion in ('eliminar_relacion', 'relacion_eliminada'):
            relacion_id = payload.get("relacion_id")
            if relacion_id is not None:
                await self._group_send(
                    {
                        "type": "pizarra.evento",
                        "evento": "relacion_eliminada",
                        "omitir_remitente": True,
                        "remitente_channel": self.channel_name,
                        "data": {
                            "relacion_id": relacion_id,
                            "usuario_id": self.user.id,
                            "username": self.user.username
                        }
                    }
                )

        elif accion in ('actualizar_relacion', 'relacion_actualizada'):
            relacion_data = payload.get("relacion") or payload.get("data")
            if relacion_data:
                await self._group_send(
                    {
                        "type": "pizarra.evento",
                        "evento": "relacion_actualizada",
                        "omitir_remitente": True,
                        "remitente_channel": self.channel_name,
                        "data": {
                            "relacion": relacion_data,
                            "usuario_id": self.user.id,
                            "username": self.user.username
                        }
                    }
                )

        # -------------------------------------------------------------
        # E. EVENTO DE PERSISTENCIA (EL DEBOUNCE): GUARDAR SNAPSHOT
        # -------------------------------------------------------------
        elif accion in ('guardar_snapshot', 'guardar_snapshot_diagrama'):
            snapshot_data = (
                payload.get("snapshot") or
                payload.get("datos_diagrama") or
                payload.get("data")
            )
            if snapshot_data is not None:
                # Guardar en base de datos PostgreSQL
                request_id = payload.get("request_id")
                resultado = await self._guardar_snapshot_db(
                    snapshot_data, payload.get("expected_revision"), request_id, payload.get("operations")
                )
                exito = resultado.get("exito", False) if isinstance(resultado, dict) else bool(resultado)
                id_map = resultado.get("id_map", {}) if isinstance(resultado, dict) else {}
                attr_id_map = resultado.get("attr_id_map", {}) if isinstance(resultado, dict) else {}
                operation_id_map = resultado.get("operation_id_map", {}) if isinstance(resultado, dict) else {}
                parameter_id_map = resultado.get("parameter_id_map", {}) if isinstance(resultado, dict) else {}
                rel_id_map = resultado.get("rel_id_map", {}) if isinstance(resultado, dict) else {}

                # Notificar confirmación al grupo (incluyendo al remitente para remap de IDs)
                if not exito:
                    await self.send(text_data=json.dumps({
                        "accion": "comando_rechazado",
                        "exito": False,
                        "codigo": resultado.get("codigo", "snapshot_rejected"),
                        "mensaje": resultado.get("mensaje", "No se confirmó el guardado."),
                        "current_revision": resultado.get("current_revision"),
                        "request_id": request_id,
                        "proyecto_id": self.proyecto_id,
                    }))
                    return
                if resultado.get('replayed'):
                    await self.send(text_data=json.dumps({
                        **resultado, "accion": "snapshot_guardado", "usuario_id": self.user.id,
                    }))
                    return
                await self._group_send(
                    {
                        "type": "pizarra.evento",
                        "evento": "snapshot_guardado",
                        "data": {
                            "exito": exito,
                            "revision": resultado["revision"],
                            "request_id": request_id,
                            "proyecto_id": self.proyecto_id,
                            "id_map": id_map,
                            "attr_id_map": attr_id_map,
                            "operation_id_map": operation_id_map,
                            "parameter_id_map": parameter_id_map,
                            "rel_id_map": rel_id_map,
                            "usuario_id": self.user.id,
                            "timestamp": payload.get("timestamp")
                        }
                    }
                )

        # -------------------------------------------------------------
        # F. RENOMBRAR PROYECTO EN TIEMPO REAL
        # -------------------------------------------------------------
        elif accion in ('renombrar_proyecto', 'proyecto_renombrado'):
            nuevo_nombre = payload.get("nombre") or payload.get("nuevo_nombre")
            if nuevo_nombre and self.proyecto_id:
                nombre_limpio = str(nuevo_nombre).strip()
                resultado = await self._actualizar_nombre_proyecto_db(
                    self.proyecto_id, nombre_limpio, payload.get("expected_revision")
                )
                if resultado.get("exito"):
                    await self._group_send(
                        {
                            "type": "pizarra.evento",
                            "evento": "proyecto_renombrado",
                            "data": {
                                "proyecto_id": self.proyecto_id,
                                "nombre": nombre_limpio,
                                "revision": resultado["revision"],
                                "request_id": payload.get("request_id"),
                                "usuario_id": self.user.id,
                                "username": self.user.username
                            }
                        }
                    )
                else:
                    await self.send(text_data=json.dumps({
                        "accion": "comando_rechazado", "exito": False,
                        "codigo": resultado.get("codigo"),
                        "mensaje": resultado.get("mensaje"),
                        "current_revision": resultado.get("current_revision"),
                        "request_id": payload.get("request_id"),
                    }))

    async def pizarra_evento(self, event):
        """
        Manejador de los mensajes emitidos al grupo Redis.
        Serializa y envía el paquete JSON hacia el cliente WebSocket conectado.
        """
        if not await self._verificar_permiso_proyecto(ProjectAction.READ):
            await self._revocar_conexion()
            return

        # Filtro de remitente para evitar eco propio en movimiento/cursor/creación/edición
        if event.get("omitir_remitente") and event.get("remitente_channel") == self.channel_name:
            return

        evento = event.get("evento")
        data = event.get("data") or {}

        payload = {
            "accion": evento,
            "evento": evento,
            "data": data,
            **data
        }
        await self.send(text_data=json.dumps(payload))

    async def access_revoked(self, event):
        """Cierra solo los sockets del usuario retirado del proyecto."""
        if int(event.get("usuario_id", -1)) == self.user.id:
            await self._revocar_conexion()

    async def _revocar_conexion(self):
        await self.send(text_data=json.dumps({
            "accion": "access.revoked",
            "evento": "access.revoked",
            "detail": "Tu acceso a este proyecto fue revocado.",
        }))
        await self.close(code=4003)

    # -------------------------------------------------------------
    # MÉTODOS DE ACCESO A BASE DE DATOS (ASYNC)
    # -------------------------------------------------------------
    @database_sync_to_async
    def _actualizar_nombre_proyecto_db(self, proyecto_id, nuevo_nombre, expected_revision):
        """Actualiza el nombre del proyecto en PostgreSQL."""
        try:
            with transaction.atomic():
                project = lock_project_for_write(proyecto_id, expected_revision)
                if not user_id_can_project_action(self.user.id, proyecto_id, ProjectAction.WRITE):
                    return {"exito": False, "codigo": "permission_denied", "mensaje": "Permiso denegado."}
                project.nombre = nuevo_nombre
                project.revision += 1
                project.save(update_fields=["nombre", "revision", "fecha_actualizacion"])
                return {"exito": True, "revision": project.revision}
        except InvalidExpectedRevision as exc:
            return {"exito": False, "codigo": exc.code, "mensaje": str(exc)}
        except StaleRevision as exc:
            return {"exito": False, "codigo": exc.code, "mensaje": str(exc), "current_revision": exc.current_revision}
        except Exception:
            return {"exito": False, "codigo": "write_failed", "mensaje": "No se pudo renombrar el proyecto."}

    @database_sync_to_async
    def _verificar_permiso_proyecto(self, action):
        """Evalúa la política central contra el estado vigente en base de datos."""
        try:
            return user_id_can_project_action(self.user.id, self.proyecto_id, action)
        except Exception:
            return False

    @database_sync_to_async
    def _guardar_snapshot_db(self, snapshot, expected_revision, request_id=None, operations=None):
        from .history import save_snapshot, history_error
        try:
            return save_snapshot(self.proyecto_id, self.user, snapshot, expected_revision, request_id, operations)
        except Exception as exc:
            return history_error(exc)

    @database_sync_to_async
    def _edit_lock(self, entity_id, release=False):
        from .history import acquire_lock
        return acquire_lock(self.proyecto_id, self.user, entity_id, self.channel_name, release)

    @database_sync_to_async
    def _release_connection_locks(self):
        from .models import DiagramEditLock
        DiagramEditLock.objects.filter(project_id=self.proyecto_id, connection=self.channel_name).delete()
