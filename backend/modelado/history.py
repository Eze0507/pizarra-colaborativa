"""Historial personal sobre el diagrama compartido, bajo el bloqueo de Proyecto.

Los frames del cliente delimitan acciones, nunca acreditan un estado anterior.
Antes/después se leen del ORM dentro de la misma transacción del snapshot.
Undo aplica un parche con precondiciones por campo, nunca un snapshot antiguo.
"""
from copy import deepcopy
from datetime import timedelta
import hashlib
import json
import logging
import math
import unicodedata
import uuid

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from .consistency import read_authoritative_state, validate_expected_revision, StaleRevision
from .models import (Proyecto, Entidad, Atributo, Operacion, ParametroOperacion, Relacion,
                     DiagramHistoryOperation as History, DiagramHistoryReceipt as Receipt, DiagramEditLock)
from .permissions import ProjectAction, require_project_action, user_can_project_action
from .realtime import notificar_evento_proyecto_sync
from .snapshot_writer import SnapshotWriter

TABLES = ('entidades', 'atributos', 'operaciones', 'parametros', 'relaciones')
MODELS = dict(zip(TABLES, (Entidad, Atributo, Operacion, ParametroOperacion, Relacion)))
MAPS = dict(zip(TABLES, ('id_map', 'attr_id_map', 'operation_id_map', 'parameter_id_map', 'rel_id_map')))
LIMIT = 50


class HistoryError(ValueError):
    def __init__(self, message, code='history_conflict', **details):
        super().__init__(message)
        self.code = code
        self.details = details


def history_error(exc):
    if isinstance(exc, PermissionDenied):
        return {'exito': False, 'codigo': 'permission_denied', 'mensaje': str(exc)}
    if isinstance(exc, (ValueError, ValidationError)):
        result = {'exito': False, 'codigo': getattr(exc, 'code', 'invalid_snapshot'), 'mensaje': str(exc)}
        result.update(getattr(exc, 'details', {}))
        if isinstance(exc, StaleRevision):
            result['current_revision'] = exc.current_revision
        return result
    logging.getLogger(__name__).exception('No se confirmó la operación de historial')
    return {'exito': False, 'codigo': 'write_failed', 'mensaje': 'No se confirmó el cambio. Recupera el estado de Django antes de continuar.'}


def normalize(value):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFD', str(value)) if unicodedata.category(c) != 'Mn').lower().split())


def current_state(project_id):
    authoritative = read_authoritative_state(project_id)
    state = {table: {} for table in TABLES}
    for item in authoritative.entities:
        entity = deepcopy(item)
        attrs = entity.pop('atributos', [])
        operations = entity.pop('operaciones', [])
        entity['estado'] = item.get('estado') or 'activo'
        state['entidades'][str(entity['id'])] = entity
        for attr in attrs:
            state['atributos'][str(attr['id'])] = {**attr, 'entidad_id': entity['id']}
        for operation in operations:
            params = operation.pop('parametros', [])
            state['operaciones'][str(operation['id'])] = {**operation, 'entidad_id': entity['id']}
            for param in params:
                state['parametros'][str(param['id'])] = {**param, 'operacion_id': operation['id']}
    visuals = {str(r['id']): r for r in authoritative.visual_snapshot.get('relaciones', [])}
    for item in authoritative.relations:
        relation = deepcopy(item)
        # vertices y puertos pertenecen al diagrama; origen_bloqueado/destino_bloqueado
        # son restricciones de anclaje de JointJS, no bloqueos de colaboradores.
        for key in ('vertices', 'origen_bloqueado', 'destino_bloqueado'):
            if key in visuals.get(str(item['id']), {}):
                relation[key] = deepcopy(visuals[str(item['id'])][key])
        state['relaciones'][str(item['id'])] = relation
    return state


def to_snapshot(state):
    entities = []
    for entity in state['entidades'].values():
        value = deepcopy(entity)
        value['atributos'] = sorted([without_parent(a, 'entidad_id') for a in state['atributos'].values() if a['entidad_id'] == entity['id']], key=lambda a: (a['orden'], a['id']))
        value['operaciones'] = []
        for operation in sorted(state['operaciones'].values(), key=lambda o: (o['orden'], o['id'])):
            if operation['entidad_id'] != entity['id']:
                continue
            op = without_parent(operation, 'entidad_id')
            op['parametros'] = sorted([without_parent(p, 'operacion_id') for p in state['parametros'].values() if p['operacion_id'] == op['id']], key=lambda p: (p['orden'], p['id']))
            value['operaciones'].append(op)
        entities.append(value)
    return {'entidades': entities, 'relaciones': deepcopy(list(state['relaciones'].values())),
            'posiciones': {str(e['id']): {'x': e['coord_x'], 'y': e['coord_y']} for e in entities}}


def without_parent(row, parent):
    result = deepcopy(row)
    result.pop(parent, None)
    return result


def changes(before, after):
    return {table: [key for key in sorted(set(before[table]) | set(after[table]))
                    if before[table].get(key) != after[table].get(key)] for table in TABLES}


def apply_patch(current, source, target):
    result = deepcopy(current)
    for table, keys in changes(source, target).items():
        for key in keys:
            old, new, actual = source[table].get(key), target[table].get(key), current[table].get(key)
            if old is None or new is None:
                if actual != old:
                    raise HistoryError(f'El elemento {table} #{key} cambió. Se conservó el trabajo actual.')
                if new is None:
                    result[table].pop(key, None)
                else:
                    result[table][key] = deepcopy(new)
            else:
                if actual is None:
                    raise HistoryError(f'El elemento {table} #{key} ya no existe.')
                for field in set(old) | set(new):
                    if old.get(field) == new.get(field):
                        continue
                    if actual.get(field) != old.get(field):
                        raise HistoryError(f'{table} #{key}: la propiedad {field} fue modificada posteriormente.')
                    if field in new:
                        result[table][key][field] = deepcopy(new[field])
                    else:
                        result[table][key].pop(field, None)
    validate_state(result)
    return result


def validate_state(state):
    """Dependencias, identidades, tipos UML y relaciones duplicadas antes de escribir."""
    entities = state['entidades']
    for table, rows in state.items():
        for row in rows.values():
            for field in ('tipo_referencia_id', 'retorno_referencia_id'):
                if row.get(field) is not None and str(row[field]) not in entities:
                    raise HistoryError('Falta un clasificador referenciado. No se modificó el diagrama.')
            if table in ('atributos', 'operaciones') and str(row['entidad_id']) not in entities:
                raise HistoryError('La clase contenedora falta o contiene trabajo posterior de otro usuario.')
            if table == 'parametros' and str(row['operacion_id']) not in state['operaciones']:
                raise HistoryError('Falta el método de un parámetro.')
    seen = set()
    for row in state['relaciones'].values():
        for field in ('entidad_origen_id', 'entidad_destino_id', 'clase_asociacion_id'):
            if row.get(field) is not None and str(row[field]) not in entities:
                raise HistoryError('Una relación depende de una clase que ya no existe o fue modificada.')
        signature = relation_signature(row)
        if signature in seen:
            raise HistoryError('La restauración produciría una relación duplicada.')
        seen.add(signature)


def relation_signature(row):
    return tuple(row.get(k) or '' for k in ('entidad_origen_id', 'entidad_destino_id', 'tipo', 'nombre_relacion', 'puerto_origen', 'puerto_destino', 'rol_origen', 'rol_destino'))


def check_locks(project, user, before, after):
    affected = changes(before, after)
    ids = set(affected['entidades'])
    for state in (before, after):
        for table in ('atributos', 'operaciones'):
            ids.update(str(state[table][key]['entidad_id']) for key in affected[table] if key in state[table])
        for key in affected['parametros']:
            param = state['parametros'].get(key)
            op = state['operaciones'].get(str(param['operacion_id'])) if param else None
            if op:
                ids.add(str(op['entidad_id']))
        for key in affected['relaciones']:
            rel = state['relaciones'].get(key, {})
            ids.update(str(rel[k]) for k in ('entidad_origen_id', 'entidad_destino_id', 'clase_asociacion_id') if rel.get(k))
    if DiagramEditLock.objects.filter(project=project, entity_id__in=ids, expires_at__gt=timezone.now()).exclude(user=user).exists():
        raise HistoryError('Un colaborador está editando un elemento afectado. Intenta nuevamente al finalizar su edición.', 'element_locked')


def record(project, user, before, after, request_id, index=0, kind='edit', description='Editar diagrama', base_revision=None):
    affected = changes(before, after)
    if not any(affected.values()):
        return None
    History.objects.filter(project=project, user=user, status=History.Status.UNDONE).update(status=History.Status.INVALID)
    entry = History.objects.create(project=project, user=user, before=deepcopy(before), after=deepcopy(after),
                                   affected=affected, request_id=request_id, batch_index=index, kind=kind,
                                   description=description[:250], base_revision=base_revision if base_revision is not None else project.revision - 1,
                                   confirmed_revision=project.revision)
    keep = list(History.objects.filter(project=project, user=user).order_by('-id').values_list('id', flat=True)[:LIMIT])
    History.objects.filter(project=project, user=user).exclude(id__in=keep).delete()
    return entry


def fingerprint(payload):
    try:
        data = json.dumps(payload, sort_keys=True, ensure_ascii=False, allow_nan=False)
    except (ValueError, TypeError) as exc:
        raise HistoryError('La solicitud contiene valores inválidos.', 'invalid_snapshot') from exc
    if len(data.encode('utf-8')) > 8_000_000:
        raise HistoryError('El lote de operaciones supera el tamaño permitido.', 'invalid_snapshot')
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def receipt(project, user, request_id, digest):
    if not isinstance(request_id, str) or not 1 <= len(request_id) <= 100:
        raise HistoryError('request_id debe identificar la solicitud.', 'invalid_request_id')
    previous = Receipt.objects.filter(project=project, user=user, request_id=request_id).first()
    if previous:
        if previous.fingerprint != digest:
            raise HistoryError('request_id ya fue utilizado con otro contenido.', 'idempotency_mismatch')
        return {**deepcopy(previous.result), 'replayed': True}
    return None


def remap_snapshot(snapshot, maps):
    data = deepcopy(snapshot)
    def remap(row, table):
        row['id'] = maps.get(MAPS[table], {}).get(str(row.get('id')), row.get('id'))
        for field in ('tipo_referencia_id', 'retorno_referencia_id', 'entidad_origen_id', 'entidad_destino_id', 'clase_asociacion_id'):
            if row.get(field) is not None:
                row[field] = maps.get('id_map', {}).get(str(row[field]), row[field])
    for e in data.get('entidades', []):
        remap(e, 'entidades')
        for a in e.get('atributos', []):
            remap(a, 'atributos')
        for o in e.get('operaciones', []):
            remap(o, 'operaciones')
            for p in o.get('parametros', []):
                remap(p, 'parametros')
    for r in data.get('relaciones', []):
        remap(r, 'relaciones')
    if isinstance(data.get('posiciones'), dict):
        data['posiciones'] = {str(maps.get('id_map', {}).get(k, k)): v for k, v in data['posiciones'].items()}
    return data


def validate_snapshot(snapshot, project):
    if not isinstance(snapshot, dict):
        raise HistoryError('Snapshot inválido.', 'invalid_snapshot')
    seen = {table: set() for table in TABLES}
    def validate_row(row, table, parent=None):
        if not isinstance(row, dict) or isinstance(row.get('id'), bool) or not isinstance(row.get('id'), int) or row['id'] == 0:
            raise HistoryError('Cada elemento debe tener un identificador entero único.', 'invalid_snapshot')
        key = row['id']
        if key in seen[table]:
            raise HistoryError('Identificadores duplicados en el snapshot.', 'invalid_snapshot')
        seen[table].add(key)
        if key > 0:
            obj = MODELS[table].objects.filter(pk=key).first()
            if obj is None:
                raise HistoryError('Un ID persistente ya no existe. Recarga el diagrama.', 'history_conflict')
            owner_project = obj.proyecto_id if table in ('entidades', 'relaciones') else (obj.operacion.entidad.proyecto_id if table == 'parametros' else obj.entidad.proyecto_id)
            parent_id = obj.operacion_id if table == 'parametros' else getattr(obj, 'entidad_id', None)
            if owner_project != project.id or (parent is not None and parent_id != parent):
                raise HistoryError('El ID no pertenece al diagrama o contenedor autorizado.', 'invalid_snapshot')
        for field in ('coord_x', 'coord_y', 'ancho'):
            if field in row and (isinstance(row[field], bool) or not isinstance(row[field], (int, float)) or not math.isfinite(row[field])):
                raise HistoryError('Dimensiones o coordenadas inválidas.', 'invalid_snapshot')
    for table in ('entidades', 'relaciones'):
        if table in snapshot and not isinstance(snapshot[table], list):
            raise HistoryError('Las colecciones del snapshot deben ser listas.', 'invalid_snapshot')
    for e in snapshot.get('entidades', []):
        validate_row(e, 'entidades')
        if 'tipo_clasificador' in e and e['tipo_clasificador'] not in Entidad.TipoClasificador.values:
            raise HistoryError('Clasificador UML inválido.', 'invalid_snapshot')
        if not isinstance(e.get('nombre', ''), str) or len(e.get('nombre', '')) > 150 or e.get('ancho', 200) <= 0:
            raise HistoryError('Nombre o ancho de clase inválido.', 'invalid_snapshot')
        for a in e.get('atributos', []):
            validate_row(a, 'atributos', e['id'])
        for o in e.get('operaciones', []):
            validate_row(o, 'operaciones', e['id'])
            for p in o.get('parametros', []):
                validate_row(p, 'parametros', o['id'])
    entity_ids = seen['entidades'] if 'entidades' in snapshot else set(project.entidades.values_list('id', flat=True))
    for r in snapshot.get('relaciones', []):
        validate_row(r, 'relaciones')
        if r.get('tipo', 'asociacion') not in Relacion.Tipo.values:
            raise HistoryError('Tipo de relación UML inválido.', 'invalid_snapshot')
        if 'vertices' in r and (not isinstance(r['vertices'], list) or len(r['vertices']) > 1000 or any(
                not isinstance(v, dict) or any(isinstance(v.get(k), bool) or not isinstance(v.get(k), (int, float)) or not math.isfinite(v[k]) for k in ('x', 'y')) for v in r['vertices'])):
            raise HistoryError('Los vértices de la relación son inválidos.', 'invalid_snapshot')
        if any(r.get(k) not in entity_ids for k in ('entidad_origen_id', 'entidad_destino_id')) or (r.get('clase_asociacion_id') and r['clase_asociacion_id'] not in entity_ids):
            raise HistoryError('La relación tiene extremos inexistentes.', 'invalid_snapshot')
    for e in snapshot.get('entidades', []):
        members = e.get('atributos', []) + e.get('operaciones', [])
        members += [p for o in e.get('operaciones', []) for p in o.get('parametros', [])]
        for member in members:
            for field in ('tipo_referencia_id', 'retorno_referencia_id'):
                if member.get(field) is not None and member[field] not in entity_ids:
                    raise HistoryError('La referencia UML no pertenece al diagrama.', 'invalid_snapshot')


def save_snapshot(project_id, user, snapshot, expected_revision, request_id=None, operations=None):
    if isinstance(snapshot, str):
        snapshot = json.loads(snapshot)
    # Clientes antiguos siguen acreditando un solo límite: el guardado completo.
    request_id = request_id or f'legacy-{uuid.uuid4()}'
    digest = fingerprint({'snapshot': snapshot, 'operations': operations, 'revision': expected_revision, 'action': 'save'})
    with transaction.atomic():
        project = Proyecto.objects.select_for_update().get(pk=project_id)
        require_project_action(user, project, ProjectAction.WRITE)
        previous = receipt(project, user, request_id, digest)
        if previous:
            return previous
        if project.revision != validate_expected_revision(expected_revision):
            raise StaleRevision(project.revision)
        frames = operations if operations is not None else [{'snapshot': snapshot, 'description': 'Editar diagrama'}]
        if not isinstance(frames, list) or not 1 <= len(frames) <= 100 or any(not isinstance(f, dict) or not isinstance(f.get('snapshot'), dict) for f in frames):
            raise HistoryError('El lote debe contener entre 1 y 100 acciones completas.', 'invalid_operations')
        if frames[-1]['snapshot'] != snapshot:
            raise HistoryError('El último límite de acción no coincide con el snapshot final.', 'invalid_operations')
        maps = {name: {} for name in MAPS.values()}
        base = project.revision
        for index, frame in enumerate(frames):
            before = current_state(project_id)
            candidate = remap_snapshot(frame['snapshot'], maps)
            validate_snapshot(candidate, project)
            result = SnapshotWriter(project_id, user).persist(candidate, base)
            if not result.get('exito'):
                raise HistoryError('No se confirmó el snapshot.', 'write_failed')
            for name in maps:
                maps[name].update(result[name])
            after = current_state(project_id)
            validate_state(after)
            check_locks(project, user, before, after)
            project.revision = base + 1
            record(project, user, before, after, request_id, index, description=str(frame.get('description') or 'Editar diagrama'), base_revision=base)
            # Un lote confirma una revisión; las acciones tienen orden independiente.
            Proyecto.objects.filter(pk=project_id).update(revision=base)
        Proyecto.objects.filter(pk=project_id).update(revision=base + 1)
        result = {'exito': True, **maps, 'revision': base + 1, 'request_id': request_id, 'proyecto_id': project_id}
        Receipt.objects.create(project=project, user=user, request_id=request_id, fingerprint=digest, result=result)
        return result


def seed_restored_ids(project, current, target):
    """Solo datos históricos del servidor pueden resucitar IDs; nunca IDs del cliente."""
    for table in TABLES:
        for key in set(target[table]) - set(current[table]):
            if MODELS[table].objects.filter(pk=key).exists():
                raise HistoryError('El identificador histórico ya está ocupado.')
    # Las referencias entre clases se asignan por el escritor después de crearlas.
    for key in set(target['entidades']) - set(current['entidades']):
        data = deepcopy(target['entidades'][key])
        Entidad.objects.create(proyecto=project, **data)
    for table in ('atributos', 'operaciones', 'parametros', 'relaciones'):
        fields = {f.attname for f in MODELS[table]._meta.concrete_fields}
        for key in set(target[table]) - set(current[table]):
            data = {k: v for k, v in target[table][key].items() if k in fields}
            if table == 'relaciones':
                data['proyecto_id'] = project.id
            MODELS[table].objects.create(**data)


def deleted_candidates(entries, command):
    candidates = []
    kind = command.get('kind', 'any')
    table_for = {'entity': 'entidades', 'attribute': 'atributos', 'method': 'operaciones', 'relationship': 'relaciones'}
    allowed = (table_for[kind],) if kind in table_for else ('entidades', 'atributos', 'operaciones', 'relaciones')
    for entry in entries:
        for table in allowed:
            for key in sorted(set(entry.before[table]) - set(entry.after[table])):
                row = entry.before[table][key]
                name = row.get('nombre', row.get('nombre_relacion') or row.get('tipo', ''))
                if command.get('name') and normalize(name) != normalize(command['name']):
                    continue
                if command.get('owner'):
                    owner = entry.before['entidades'].get(str(row.get('entidad_id')), {})
                    if normalize(owner.get('nombre', '')) != normalize(command['owner']):
                        continue
                if command.get('endpoints'):
                    endpoints = [entry.before['entidades'].get(str(row.get(k)), {}).get('nombre', '') for k in ('entidad_origen_id', 'entidad_destino_id')]
                    if sorted(map(normalize, endpoints)) != sorted(map(normalize, command['endpoints'])):
                        continue
                if command.get('operation_id') and str(entry.operation_id) != command['operation_id']:
                    continue
                candidates.append((entry, table, key, name))
        if candidates and command.get('latest'):
            break
    # El mismo elemento puede haberse eliminado varias veces: usar la eliminación más reciente.
    unique = {}
    for candidate in candidates:
        unique.setdefault((candidate[1], candidate[2]), candidate)
    return list(unique.values())


def restore_target(current, entries, command):
    candidates = deleted_candidates(entries, command)
    if not candidates:
        raise HistoryError('No hay una eliminación recuperable en tus últimas 50 operaciones de este diagrama. No se recuperan cambios anteriores a la implementación.', 'history_not_found')
    if len(candidates) > 1:
        raise HistoryError('Hay varias eliminaciones posibles. Indica el tipo y la clase contenedora, o selecciona una operación.', 'history_ambiguous', candidates=[{'operation_id': str(e.operation_id), 'kind': t, 'id': k, 'name': n} for e, t, k, n in candidates])
    entry, table, key, name = candidates[0]
    if key in current[table]:
        raise HistoryError('El elemento ya existe; no se creó un duplicado.')
    target = deepcopy(current)
    row = deepcopy(entry.before[table][key])
    if table != 'relaciones':
        parent_field = 'entidad_id' if table in ('atributos', 'operaciones') else None
        if any(normalize(r.get('nombre', '')) == normalize(name) and (not parent_field or r[parent_field] == row[parent_field]) for r in current[table].values()):
            raise HistoryError('Ya existe un elemento con ese nombre en el contenedor.')
    target[table][key] = row
    warnings = []
    if table == 'entidades':
        for child_table in ('atributos', 'operaciones'):
            for child_key, child in entry.before[child_table].items():
                if child['entidad_id'] == row['id']:
                    target[child_table][child_key] = deepcopy(child)
        for rel_key, rel in entry.before['relaciones'].items():
            if row['id'] not in [rel.get(k) for k in ('entidad_origen_id', 'entidad_destino_id', 'clase_asociacion_id')]:
                continue
            endpoints_ok = all(rel.get(k) is None or str(rel[k]) in target['entidades'] for k in ('entidad_origen_id', 'entidad_destino_id', 'clase_asociacion_id'))
            if not endpoints_ok or rel_key in target['relaciones'] or any(relation_signature(r) == relation_signature(rel) for r in target['relaciones'].values()):
                warnings.append(f'Relación #{rel_key} omitida: extremos ausentes o relación existente.')
            else:
                target['relaciones'][rel_key] = deepcopy(rel)
    if table in ('entidades', 'operaciones'):
        restored_methods = set(target['operaciones']) - set(current['operaciones'])
        for param_key, param in entry.before['parametros'].items():
            if str(param['operacion_id']) in restored_methods:
                target['parametros'][param_key] = deepcopy(param)
    validate_state(target)
    return target, warnings, f'Restaurar {name}'


def history_payload(project, user, current=None):
    current = current if current is not None else current_state(project.id)
    entries = list(History.objects.filter(project=project, user=user).order_by('-id'))
    undo = next((e for e in entries if e.status == History.Status.APPLIED), None)
    redo = next((e for e in reversed(entries) if e.status == History.Status.UNDONE), None)
    def available(entry, backwards):
        if not entry:
            return False
        try:
            target = apply_patch(current, entry.after if backwards else entry.before, entry.before if backwards else entry.after)
            check_locks(project, user, current, target)
            return True
        except HistoryError:
            return False
    editable = user_can_project_action(user, project, ProjectAction.WRITE)
    return {'proyecto_id': project.id, 'revision': project.revision, 'limit': LIMIT,
            'canUndo': editable and available(undo, True), 'canRedo': editable and available(redo, False),
            'operations': [{'operation_id': str(e.operation_id), 'kind': e.kind, 'description': e.description,
                            'status': e.status, 'order': e.id, 'base_revision': e.base_revision,
                            'confirmed_revision': e.confirmed_revision, 'created_at': e.created_at.isoformat(), 'affected': e.affected} for e in entries]}


def load_history(project_id, user):
    with transaction.atomic():
        project = Proyecto.objects.select_for_update().get(pk=project_id)
        require_project_action(user, project, ProjectAction.READ)
        return history_payload(project, user)


def execute_history(project_id, user, command, expected_revision, request_id):
    digest = fingerprint({'action': 'history', 'command': command, 'revision': expected_revision})
    with transaction.atomic():
        project = Proyecto.objects.select_for_update().get(pk=project_id)
        require_project_action(user, project, ProjectAction.WRITE)
        previous = receipt(project, user, request_id, digest)
        if previous:
            # El recibo acredita el resultado; el cliente recarga el estado vigente.
            return previous
        if project.revision != validate_expected_revision(expected_revision):
            raise StaleRevision(project.revision)
        current = current_state(project_id)
        action = command.get('action')
        entries = History.objects.filter(project=project, user=user)
        warnings = []
        entry = None
        if action in ('undo', 'redo'):
            entry = entries.filter(status=History.Status.APPLIED if action == 'undo' else History.Status.UNDONE).order_by('-id' if action == 'undo' else 'id').first()
            if not entry:
                raise HistoryError('No hay operaciones disponibles en tu historial conservado.', 'history_not_found')
            target = apply_patch(current, entry.after if action == 'undo' else entry.before, entry.before if action == 'undo' else entry.after)
            description = 'Cambio deshecho.' if action == 'undo' else 'Cambio rehecho.'
        elif action == 'restore':
            target, warnings, description = restore_target(current, entries.exclude(status=History.Status.INVALID).order_by('-id'), command)
        else:
            raise HistoryError('Comando de historial inválido.', 'invalid_command')
        check_locks(project, user, current, target)
        seed_restored_ids(project, current, target)
        result = SnapshotWriter(project_id, user).persist(to_snapshot(target), project.revision)
        if not result.get('exito'):
            raise HistoryError('No se confirmó la reversión.', 'write_failed')
        project.refresh_from_db()
        after = current_state(project_id)
        if after != target:
            raise HistoryError('No se pudo conservar íntegramente el estado UML solicitado.')
        if entry:
            entry.status = History.Status.UNDONE if action == 'undo' else History.Status.APPLIED
            entry.save(update_fields=['status'])
        else:
            record(project, user, current, after, request_id, kind='restore', description=description)
        result = {**result, 'proyecto_id': project_id, 'request_id': request_id, 'mensaje': description,
                  'warnings': warnings, 'history': history_payload(project, user, after)}
        Receipt.objects.create(project=project, user=user, request_id=request_id, fingerprint=digest, result=result)
        transaction.on_commit(lambda: notificar_evento_proyecto_sync(project_id, 'history.updated', {
            'proyecto_id': project_id, 'revision': project.revision, 'usuario_id': user.id, 'request_id': request_id,
        }), robust=True)
        return result


def acquire_lock(project_id, user, entity_id, connection, release=False):
    with transaction.atomic():
        project = Proyecto.objects.select_for_update().get(pk=project_id)
        require_project_action(user, project, ProjectAction.WRITE)
        locks = DiagramEditLock.objects.filter(project=project, entity_id=entity_id)
        if release:
            locks.filter(user=user, connection=connection).delete()
            return True
        locks.filter(expires_at__lte=timezone.now()).delete()
        if locks.exclude(user=user, connection=connection).exists():
            return False
        DiagramEditLock.objects.update_or_create(project=project, entity_id=entity_id,
            defaults={'user': user, 'connection': connection, 'expires_at': timezone.now() + timedelta(seconds=45)})
        return True
