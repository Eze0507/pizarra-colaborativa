"""Escritor ?nico de snapshots ORM; compartido por autosave e historial."""
import json
from copy import deepcopy
from django.db import transaction
from .models import Proyecto, Entidad, Atributo, Operacion, ParametroOperacion, Relacion
from .permissions import ProjectAction, user_id_can_project_action
from .consistency import lock_project_for_write


class SnapshotWriter:
    def __init__(self, project_id, user):
        self.proyecto_id = project_id
        self.user = user

    @staticmethod
    def _entero_positivo(value):
        try:
            parsed = int(value)
            return parsed if parsed > 0 else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _entero_orden(value, default):
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return default

    def _resolver_tipo_referencia(self, proyecto, raw_id, id_map):
        if raw_id in (None, ''):
            return None
        mapped_id = id_map.get(str(raw_id), self._entero_positivo(raw_id))
        if not mapped_id:
            return None
        return Entidad.objects.filter(pk=mapped_id, proyecto=proyecto).first()

    def _sincronizar_detalle_clasificador(
        self,
        proyecto,
        entidad,
        atributos_data,
        operaciones_data,
        id_map,
        attr_id_map,
        operation_id_map,
        parameter_id_map,
    ):
        """Sincroniza el contrato UML anidado sin reemplazar IDs persistentes."""
        atributos_procesados = set()
        for index, data in enumerate(atributos_data if isinstance(atributos_data, list) else []):
            if not isinstance(data, dict):
                continue
            raw_id = data.get('id')
            persisted_id = self._entero_positivo(raw_id)
            atributo = Atributo.objects.filter(pk=persisted_id, entidad=entidad).first()
            atributo_nuevo = atributo is None
            if not atributo:
                atributo = Atributo(entidad=entidad)
            atributo.nombre = str(data.get('nombre') or 'atributo').strip()
            atributo.tipo = str(data.get('tipo') or 'string').strip()
            if atributo_nuevo or 'tipo_referencia_id' in data:
                atributo.tipo_referencia = self._resolver_tipo_referencia(
                    proyecto, data.get('tipo_referencia_id'), id_map
                )
            if atributo_nuevo or 'visibilidad' in data:
                atributo.visibilidad = data.get('visibilidad') or 'private'
            if atributo_nuevo or 'es_estatico' in data:
                atributo.es_estatico = bool(data.get('es_estatico', False))
            atributo.es_clave = bool(data.get('es_clave', False))
            atributo.es_nulo = bool(data.get('es_nulo', False))
            if atributo_nuevo or 'valor_predeterminado' in data:
                atributo.valor_predeterminado = str(data.get('valor_predeterminado') or '')
            atributo.orden = self._entero_orden(data.get('orden'), index)
            atributo.full_clean()
            atributo.save()
            if persisted_id != atributo.id and raw_id is not None:
                attr_id_map[str(raw_id)] = atributo.id
            data['id'] = atributo.id
            atributos_procesados.add(atributo.id)
        entidad.atributos.exclude(id__in=atributos_procesados).delete()

        if operaciones_data is None:
            return

        operaciones_procesadas = set()
        for index, data in enumerate(operaciones_data if isinstance(operaciones_data, list) else []):
            if not isinstance(data, dict):
                continue
            raw_id = data.get('id')
            persisted_id = self._entero_positivo(raw_id)
            operacion = Operacion.objects.filter(pk=persisted_id, entidad=entidad).first()
            if not operacion:
                operacion = Operacion(entidad=entidad)
            operacion.nombre = str(data.get('nombre') or 'operacion').strip()
            operacion.visibilidad = data.get('visibilidad') or 'public'
            operacion.tipo_retorno = str(data.get('tipo_retorno') or 'void').strip()
            operacion.retorno_referencia = self._resolver_tipo_referencia(
                proyecto, data.get('retorno_referencia_id'), id_map
            )
            operacion.orden = self._entero_orden(data.get('orden'), index)
            operacion.es_estatico = bool(data.get('es_estatico', False))
            operacion.es_abstracto = bool(data.get('es_abstracto', False))
            operacion.full_clean()
            operacion.save()
            if persisted_id != operacion.id and raw_id is not None:
                operation_id_map[str(raw_id)] = operacion.id
            data['id'] = operacion.id
            operaciones_procesadas.add(operacion.id)

            parametros_procesados = set()
            parametros_data = data.get('parametros') if 'parametros' in data else None
            if parametros_data is None:
                continue
            for param_index, param_data in enumerate(
                parametros_data if isinstance(parametros_data, list) else []
            ):
                if not isinstance(param_data, dict):
                    continue
                raw_param_id = param_data.get('id')
                persisted_param_id = self._entero_positivo(raw_param_id)
                parametro = ParametroOperacion.objects.filter(
                    pk=persisted_param_id, operacion=operacion
                ).first()
                if not parametro:
                    parametro = ParametroOperacion(operacion=operacion)
                parametro.nombre = str(param_data.get('nombre') or 'parametro').strip()
                parametro.tipo = str(param_data.get('tipo') or 'string').strip()
                parametro.tipo_referencia = self._resolver_tipo_referencia(
                    proyecto, param_data.get('tipo_referencia_id'), id_map
                )
                parametro.orden = self._entero_orden(param_data.get('orden'), param_index)
                parametro.full_clean()
                parametro.save()
                if persisted_param_id != parametro.id and raw_param_id is not None:
                    parameter_id_map[str(raw_param_id)] = parametro.id
                param_data['id'] = parametro.id
                parametros_procesados.add(parametro.id)
            operacion.parametros.exclude(id__in=parametros_procesados).delete()
        entidad.operaciones.exclude(id__in=operaciones_procesadas).delete()

    def persist(self, snapshot, expected_revision):
        """
        Persiste el snapshot del diagrama en PostgreSQL:
        1. Sincroniza Entidades (creación con IDs reales para temporales <= 0, actualización y eliminación).
        2. Sincroniza Atributos para cada entidad.
        3. Sincroniza Relaciones (mapeando IDs de origen, destino y clase_asociacion; creando para temporales <= 0).
        4. Actualiza Proyecto.datos_diagrama con los IDs ya mapeados.
        Retorna dict con { 'exito': True, 'id_map': id_map, 'rel_id_map': rel_id_map }
        """
        try:
            snapshot = deepcopy(snapshot)
            if isinstance(snapshot, str):
                snapshot = json.loads(snapshot)
            if not isinstance(snapshot, dict):
                return {"exito": False, "id_map": {}, "rel_id_map": {}}

            with transaction.atomic():
                proyecto = lock_project_for_write(self.proyecto_id, expected_revision)
                if not user_id_can_project_action(
                    self.user.id, proyecto.id, ProjectAction.WRITE
                ):
                    return {"exito": False, "id_map": {}, "rel_id_map": {}}

                id_map = {}
                attr_id_map = {}
                operation_id_map = {}
                parameter_id_map = {}
                rel_id_map = {}
                entidades_procesadas_ids = set()
                entidades_para_detalle = []

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
                        operaciones_data = item.get('operaciones') if 'operaciones' in item else None
                        tipo_clasificador = item.get('tipo_clasificador') or Entidad.TipoClasificador.CLASE
                        if tipo_clasificador not in Entidad.TipoClasificador.values:
                            tipo_clasificador = Entidad.TipoClasificador.CLASE
                        abstracto = bool(item.get('abstracto', False))

                        if raw_id is None or int(raw_id) <= 0:
                            # Nueva entidad creada con ID temporal en cliente
                            nueva_ent = Entidad.objects.create(
                                proyecto=proyecto,
                                nombre=nombre,
                                estado=estado,
                                coord_x=coord_x,
                                coord_y=coord_y,
                                ancho=ancho,
                                es_intermedia=es_intermedia,
                                tipo_clasificador=tipo_clasificador,
                                abstracto=abstracto,
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
                                if 'tipo_clasificador' in item:
                                    ent_obj.tipo_clasificador = tipo_clasificador
                                if 'abstracto' in item:
                                    ent_obj.abstracto = abstracto
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
                                    es_intermedia=es_intermedia,
                                    tipo_clasificador=tipo_clasificador,
                                    abstracto=abstracto,
                                )
                                id_map[str(num_id)] = nueva_ent.id
                                entidades_procesadas_ids.add(nueva_ent.id)
                                ent_obj = nueva_ent

                        if ent_obj:
                            entidades_para_detalle.append(
                                (item, ent_obj, atributos_data, operaciones_data)
                            )

                    for item, ent_obj, atributos_data, operaciones_data in entidades_para_detalle:
                        self._sincronizar_detalle_clasificador(
                            proyecto,
                            ent_obj,
                            atributos_data,
                            operaciones_data,
                            id_map,
                            attr_id_map,
                            operation_id_map,
                            parameter_id_map,
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

                        # Resolver entidad intermedia si es clase de asociación
                        ent_clase_asoc = None
                        if r_item.get('clase_asociacion_id'):
                            ent_clase_asoc = Entidad.objects.filter(
                                id=r_item['clase_asociacion_id'],
                                proyecto=proyecto
                            ).first()

                        p_orig = r_item.get('puerto_origen') or ''
                        p_dest = r_item.get('puerto_destino') or ''
                        nom_rel = r_item.get('nombre_relacion') or ''
                        card_orig = r_item.get('cardinalidad_origen') or ''
                        card_dest = r_item.get('cardinalidad_destino') or ''
                        rol_orig = r_item.get('rol_origen') or ''
                        rol_dest = r_item.get('rol_destino') or ''
                        nav_orig = bool(r_item.get('navegable_origen', False))
                        nav_dest = bool(r_item.get('navegable_destino', False))

                        if raw_rel_id is None or int(raw_rel_id) <= 0:
                            nueva_rel = Relacion(
                                proyecto=proyecto,
                                entidad_origen=ent_orig,
                                entidad_destino=ent_dest,
                                clase_asociacion=ent_clase_asoc,
                                nombre_relacion=nom_rel,
                                tipo=tipo,
                                cardinalidad_origen=card_orig,
                                cardinalidad_destino=card_dest,
                                puerto_origen=p_orig,
                                puerto_destino=p_dest,
                                rol_origen=rol_orig,
                                rol_destino=rol_dest,
                                navegable_origen=nav_orig,
                                navegable_destino=nav_dest,
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
                                rel_obj.clase_asociacion = ent_clase_asoc
                                rel_obj.nombre_relacion = nom_rel
                                rel_obj.tipo = tipo
                                rel_obj.cardinalidad_origen = card_orig
                                rel_obj.cardinalidad_destino = card_dest
                                rel_obj.puerto_origen = p_orig
                                rel_obj.puerto_destino = p_dest
                                if 'rol_origen' in r_item:
                                    rel_obj.rol_origen = rol_orig
                                if 'rol_destino' in r_item:
                                    rel_obj.rol_destino = rol_dest
                                if 'navegable_origen' in r_item:
                                    rel_obj.navegable_origen = nav_orig
                                if 'navegable_destino' in r_item:
                                    rel_obj.navegable_destino = nav_dest
                                rel_obj.full_clean()
                                rel_obj.save()
                                relaciones_procesadas_ids.add(rel_obj.id)
                            else:
                                nueva_rel = Relacion(
                                    proyecto=proyecto,
                                    entidad_origen=ent_orig,
                                    entidad_destino=ent_dest,
                                    clase_asociacion=ent_clase_asoc,
                                    nombre_relacion=nom_rel,
                                    tipo=tipo,
                                    cardinalidad_origen=card_orig,
                                    cardinalidad_destino=card_dest,
                                    puerto_origen=p_orig,
                                    puerto_destino=p_dest,
                                    rol_origen=rol_orig,
                                    rol_destino=rol_dest,
                                    navegable_origen=nav_orig,
                                    navegable_destino=nav_dest,
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
                proyecto.revision += 1
                proyecto.save(update_fields=['datos_diagrama', 'revision', 'fecha_actualizacion'])

                return {
                    "exito": True,
                    "id_map": {str(k): v for k, v in id_map.items()},
                    "attr_id_map": {str(k): v for k, v in attr_id_map.items()},
                    "operation_id_map": {str(k): v for k, v in operation_id_map.items()},
                    "parameter_id_map": {str(k): v for k, v in parameter_id_map.items()},
                    "rel_id_map": {str(k): v for k, v in rel_id_map.items()},
                    "revision": proyecto.revision,
                }
        except Exception:
            raise
