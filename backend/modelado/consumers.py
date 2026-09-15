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

from .models import Proyecto, Entidad, Atributo, Relacion
from usuario.models import UserColaborador
from .realtime import get_proyecto_group_name


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
        self.proyecto_id = self.scope.get('url_route', {}).get('kwargs', {}).get('proyecto_id')
        self.room_group_name = get_proyecto_group_name(self.proyecto_id)

        # 1. Validar autenticación
        if not self.user or not self.user.is_authenticated:
            # 4003: Forbidden / No autenticado
            await self.close(code=4003)
            return

        # 2. Validar pertenencia o acceso al proyecto
        tiene_acceso = await self._verificar_acceso_proyecto(self.user.id, self.proyecto_id)
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
                resultado = await self._guardar_snapshot_db(snapshot_data)
                exito = resultado.get("exito", False) if isinstance(resultado, dict) else bool(resultado)
                id_map = resultado.get("id_map", {}) if isinstance(resultado, dict) else {}
                rel_id_map = resultado.get("rel_id_map", {}) if isinstance(resultado, dict) else {}

                # Notificar confirmación al grupo (incluyendo al remitente para remap de IDs)
                await self._group_send(
                    {
                        "type": "pizarra.evento",
                        "evento": "snapshot_guardado",
                        "data": {
                            "exito": exito,
                            "id_map": id_map,
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
                await self._actualizar_nombre_proyecto_db(self.proyecto_id, nombre_limpio)
                await self._group_send(
                    {
                        "type": "pizarra.evento",
                        "evento": "proyecto_renombrado",
                        "data": {
                            "proyecto_id": self.proyecto_id,
                            "nombre": nombre_limpio,
                            "usuario_id": self.user.id,
                            "username": self.user.username
                        }
                    }
                )

    async def pizarra_evento(self, event):
        """
        Manejador de los mensajes emitidos al grupo Redis.
        Serializa y envía el paquete JSON hacia el cliente WebSocket conectado.
        """
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

    # -------------------------------------------------------------
    # MÉTODOS DE ACCESO A BASE DE DATOS (ASYNC)
    # -------------------------------------------------------------
    @database_sync_to_async
    def _actualizar_nombre_proyecto_db(self, proyecto_id, nuevo_nombre):
        """Actualiza el nombre del proyecto en PostgreSQL."""
        try:
            Proyecto.objects.filter(id=proyecto_id).update(nombre=nuevo_nombre)
        except Exception:
            pass

    @database_sync_to_async
    def _verificar_acceso_proyecto(self, user_id, proyecto_id):
        """Verifica si el usuario es dueño o colaborador activo del proyecto."""
        try:
            # 1. ¿Es propietario?
            if Proyecto.objects.filter(id=proyecto_id, propietario_id=user_id).exists():
                return True
            # 2. ¿Es colaborador con estado ACTIVO?
            return UserColaborador.objects.filter(
                proyecto_id=proyecto_id,
                usuario_id=user_id,
                estado=UserColaborador.Estado.ACTIVO
            ).exists()
        except Exception:
            return False

    @database_sync_to_async
    def _guardar_snapshot_db(self, snapshot):
        """
        Persiste el snapshot del diagrama en PostgreSQL:
        1. Sincroniza Entidades (creación con IDs reales para temporales <= 0, actualización y eliminación).
        2. Sincroniza Atributos para cada entidad.
        3. Sincroniza Relaciones (mapeando IDs de origen, destino y clase_asociacion; creando para temporales <= 0).
        4. Actualiza Proyecto.datos_diagrama con los IDs ya mapeados.
        Retorna dict con { 'exito': True, 'id_map': id_map, 'rel_id_map': rel_id_map }
        """
        try:
            if isinstance(snapshot, str):
                snapshot = json.loads(snapshot)
            if not isinstance(snapshot, dict):
                return {"exito": False, "id_map": {}, "rel_id_map": {}}

            with transaction.atomic():
                proyecto = Proyecto.objects.filter(id=self.proyecto_id).first()
                if not proyecto:
                    return {"exito": False, "id_map": {}, "rel_id_map": {}}

                id_map = {}
                rel_id_map = {}
                entidades_procesadas_ids = set()

                # -------------------------------------------------------------
                # 1. SINCRONIZAR ENTIDADES Y SUS ATRIBUTOS
                # -------------------------------------------------------------
                entidades_payload = snapshot.get('entidades')
                if isinstance(entidades_payload, list):
                    for item in entidades_payload:
                        if not isinstance(item, dict):
                            continue
                        raw_id = item.get('id')
                        nombre = (item.get('nombre') or '').strip()
                        estado = item.get('estado') or 'activo'
                        if estado not in Entidad.Estado.values:
                            estado = 'activo'
                        coord_x = float(item.get('coord_x', item.get('x', 0.0)) or 0.0)
                        coord_y = float(item.get('coord_y', item.get('y', 0.0)) or 0.0)
                        ancho = float(item.get('ancho', 200.0) or 200.0)
                        es_intermedia = bool(item.get('es_intermedia', False))
                        atributos_data = item.get('atributos') or []

                        if raw_id is None or int(raw_id) <= 0:
                            # Nueva entidad creada con ID temporal en cliente
                            nueva_ent = Entidad.objects.create(
                                proyecto=proyecto,
                                nombre=nombre,
                                estado=estado,
                                coord_x=coord_x,
                                coord_y=coord_y,
                                ancho=ancho,
                                es_intermedia=es_intermedia
                            )
                            if raw_id is not None:
                                id_map[str(raw_id)] = nueva_ent.id
                            entidades_procesadas_ids.add(nueva_ent.id)
                            ent_obj = nueva_ent
                        else:
                            num_id = int(raw_id)
                            ent_obj = Entidad.objects.filter(id=num_id, proyecto=proyecto).first()
                            if ent_obj:
                                ent_obj.nombre = nombre
                                ent_obj.estado = estado
                                ent_obj.coord_x = coord_x
                                ent_obj.coord_y = coord_y
                                ent_obj.ancho = ancho
                                ent_obj.es_intermedia = es_intermedia
                                ent_obj.save()
                                entidades_procesadas_ids.add(ent_obj.id)
                            else:
                                nueva_ent = Entidad.objects.create(
                                    proyecto=proyecto,
                                    nombre=nombre,
                                    estado=estado,
                                    coord_x=coord_x,
                                    coord_y=coord_y,
                                    ancho=ancho,
                                    es_intermedia=es_intermedia
                                )
                                id_map[str(num_id)] = nueva_ent.id
                                entidades_procesadas_ids.add(nueva_ent.id)
                                ent_obj = nueva_ent

                        # Sincronizar atributos de la entidad
                        if ent_obj:
                            ent_obj.atributos.all().delete()
                            for idx, attr in enumerate(atributos_data):
                                if not isinstance(attr, dict):
                                    continue
                                tipo_val = (attr.get('tipo') or 'string').lower()
                                if tipo_val not in Atributo.Tipo.values:
                                    tipo_val = 'string'
                                Atributo.objects.create(
                                    entidad=ent_obj,
                                    nombre=attr.get('nombre', 'atributo'),
                                    tipo=tipo_val,
                                    es_clave=bool(attr.get('es_clave', False)),
                                    es_nulo=bool(attr.get('es_nulo', False)),
                                    orden=int(attr.get('orden', idx))
                                )

                    # Eliminar de la base de datos las entidades que ya no existen en el diagrama
                    Entidad.objects.filter(proyecto=proyecto).exclude(id__in=entidades_procesadas_ids).delete()

                elif isinstance(snapshot.get('posiciones'), dict):
                    # Fallback si solo se enviaron posiciones
                    for ent_id_str, pos in snapshot['posiciones'].items():
                        try:
                            ent_id = int(ent_id_str)
                            if ent_id > 0 and isinstance(pos, dict):
                                x = pos.get('x')
                                y = pos.get('y')
                                if x is not None and y is not None:
                                    Entidad.objects.filter(id=ent_id, proyecto=proyecto).update(
                                        coord_x=float(x),
                                        coord_y=float(y)
                                    )
                        except (ValueError, TypeError):
                            pass

                # -------------------------------------------------------------
                # 2. SINCRONIZAR RELACIONES
                # -------------------------------------------------------------
                relaciones_payload = snapshot.get('relaciones')
                relaciones_procesadas_ids = set()

                if isinstance(relaciones_payload, list):
                    for r_item in relaciones_payload:
                        if not isinstance(r_item, dict):
                            continue
                        raw_rel_id = r_item.get('id')
                        tipo = r_item.get('tipo') or 'asociacion'
                        if tipo not in Relacion.Tipo.values:
                            tipo = 'asociacion'

                        raw_orig_id = r_item.get('entidad_origen_id')
                        raw_dest_id = r_item.get('entidad_destino_id')
                        if raw_orig_id is None or raw_dest_id is None:
                            continue

                        real_orig_id = id_map.get(str(raw_orig_id), int(raw_orig_id))
                        real_dest_id = id_map.get(str(raw_dest_id), int(raw_dest_id))

                        ent_orig = Entidad.objects.filter(id=real_orig_id, proyecto=proyecto).first()
                        ent_dest = Entidad.objects.filter(id=real_dest_id, proyecto=proyecto).first()
                        if not ent_orig or not ent_dest:
                            continue

                        # Actualizar IDs en el payload para el snapshot JSON
                        r_item['entidad_origen_id'] = real_orig_id
                        r_item['entidad_destino_id'] = real_dest_id
                        if 'clase_asociacion_id' in r_item and r_item['clase_asociacion_id']:
                            real_clase_asoc_id = id_map.get(str(r_item['clase_asociacion_id']), int(r_item['clase_asociacion_id']))
                            r_item['clase_asociacion_id'] = real_clase_asoc_id

                        p_orig = r_item.get('puerto_origen') or ''
                        p_dest = r_item.get('puerto_destino') or ''
                        nom_rel = r_item.get('nombre_relacion') or ''
                        card_orig = r_item.get('cardinalidad_origen') or ('1' if tipo != 'herencia' else '')
                        card_dest = r_item.get('cardinalidad_destino') or ('1' if tipo != 'herencia' else '')

                        if raw_rel_id is None or int(raw_rel_id) <= 0:
                            nueva_rel = Relacion(
                                proyecto=proyecto,
                                entidad_origen=ent_orig,
                                entidad_destino=ent_dest,
                                nombre_relacion=nom_rel,
                                tipo=tipo,
                                cardinalidad_origen=card_orig,
                                cardinalidad_destino=card_dest,
                                puerto_origen=p_orig,
                                puerto_destino=p_dest
                            )
                            nueva_rel.full_clean()
                            nueva_rel.save()
                            if raw_rel_id is not None:
                                rel_id_map[str(raw_rel_id)] = nueva_rel.id
                            r_item['id'] = nueva_rel.id
                            relaciones_procesadas_ids.add(nueva_rel.id)
                        else:
                            num_rel_id = int(raw_rel_id)
                            rel_obj = Relacion.objects.filter(id=num_rel_id, proyecto=proyecto).first()
                            if rel_obj:
                                rel_obj.entidad_origen = ent_orig
                                rel_obj.entidad_destino = ent_dest
                                rel_obj.nombre_relacion = nom_rel
                                rel_obj.tipo = tipo
                                rel_obj.cardinalidad_origen = card_orig
                                rel_obj.cardinalidad_destino = card_dest
                                rel_obj.puerto_origen = p_orig
                                rel_obj.puerto_destino = p_dest
                                rel_obj.full_clean()
                                rel_obj.save()
                                relaciones_procesadas_ids.add(rel_obj.id)
                            else:
                                nueva_rel = Relacion(
                                    proyecto=proyecto,
                                    entidad_origen=ent_orig,
                                    entidad_destino=ent_dest,
                                    nombre_relacion=nom_rel,
                                    tipo=tipo,
                                    cardinalidad_origen=card_orig,
                                    cardinalidad_destino=card_dest,
                                    puerto_origen=p_orig,
                                    puerto_destino=p_dest
                                )
                                nueva_rel.full_clean()
                                nueva_rel.save()
                                rel_id_map[str(num_rel_id)] = nueva_rel.id
                                r_item['id'] = nueva_rel.id
                                relaciones_procesadas_ids.add(nueva_rel.id)

                    # Eliminar de la base de datos las relaciones que ya no existen
                    Relacion.objects.filter(proyecto=proyecto).exclude(id__in=relaciones_procesadas_ids).delete()

                # -------------------------------------------------------------
                # 3. ACTUALIZAR SNAPSHOT JSON EN PROYECTO CON IDS REALES
                # -------------------------------------------------------------
                if isinstance(snapshot.get('entidades'), list):
                    for e in snapshot['entidades']:
                        if isinstance(e, dict) and str(e.get('id')) in id_map:
                            e['id'] = id_map[str(e['id'])]

                if isinstance(snapshot.get('posiciones'), dict):
                    pos_actualizadas = {}
                    for k, v in snapshot['posiciones'].items():
                        str_k = str(k)
                        real_k = str(id_map.get(str_k, str_k))
                        pos_actualizadas[real_k] = v
                    snapshot['posiciones'] = pos_actualizadas

                proyecto.datos_diagrama = snapshot
                proyecto.save(update_fields=['datos_diagrama', 'fecha_actualizacion'])

                return {
                    "exito": True,
                    "id_map": {str(k): v for k, v in id_map.items()},
                    "rel_id_map": {str(k): v for k, v in rel_id_map.items()}
                }
        except Exception as e:
            print(f"[SNAPSHOT_ERROR] Error persistiendo snapshot: {e}")
            return {"exito": False, "id_map": {}, "rel_id_map": {}}
