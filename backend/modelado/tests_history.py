from copy import deepcopy
from datetime import timedelta
from unittest.mock import patch
from unittest import skipUnless
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import uuid

from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction, connection, connections
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .consumers import PizarraConsumer
from .history import (save_snapshot, execute_history, load_history, current_state, to_snapshot,
                      HistoryError, StaleRevision, acquire_lock)
from .models import (Proyecto, Entidad, Atributo, Operacion, ParametroOperacion, Relacion,
                     DiagramHistoryOperation as History, DiagramHistoryReceipt as Receipt, DiagramEditLock)
from usuario.models import UserColaborador

User = get_user_model()


def entity(id=-1, name='unidad'):
    return {'id': id, 'nombre': name, 'estado': 'activo', 'coord_x': 72, 'coord_y': 104, 'ancho': 280,
            'tipo_clasificador': 'clase', 'abstracto': False, 'es_intermedia': False,
            'atributos': [{'id': id * 10 - 1, 'nombre': 'dirección', 'tipo': 'string', 'visibilidad': 'private',
                           'es_clave': False, 'es_nulo': True, 'es_estatico': False, 'orden': 0,
                           'valor_predeterminado': 'sin dirección', 'tipo_referencia_id': None}],
            'operaciones': [{'id': id * 10 - 2, 'nombre': 'registrar', 'tipo_retorno': 'void', 'retorno_referencia_id': None,
                             'es_estatico': False, 'es_abstracto': False, 'visibilidad': 'public', 'orden': 0,
                             'parametros': [{'id': id * 10 - 3, 'nombre': 'valor', 'tipo': 'string', 'orden': 0, 'tipo_referencia_id': None}]}]}


def diagram():
    return {'entidades': [entity(), entity(-2, 'producto')], 'relaciones': [
        {'id': -40, 'entidad_origen_id': -1, 'entidad_destino_id': -2, 'nombre_relacion': 'contiene',
         'tipo': 'asociacion', 'cardinalidad_origen': '1', 'cardinalidad_destino': '0..*',
         'puerto_origen': 'right-1', 'puerto_destino': 'left-0', 'rol_origen': 'unidad', 'rol_destino': 'productos',
         'navegable_origen': False, 'navegable_destino': True, 'vertices': [{'x': 30, 'y': 40}]}]}


class HistoryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='history-owner')
        self.other = User.objects.create_user(username='history-editor')
        self.project = Proyecto.objects.create(propietario=self.user, nombre='History')
        UserColaborador.objects.create(usuario=self.other, proyecto=self.project, rol='editor', estado='activo')
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.url = f'/api/modelado/proyectos/{self.project.id}/historial/'

    def save(self, snapshot, user=None, operations=None, request_id=None):
        self.project.refresh_from_db()
        return save_snapshot(self.project.id, user or self.user, snapshot, self.project.revision, request_id or str(uuid.uuid4()), operations)

    def command(self, action='undo', user=None, **kwargs):
        self.project.refresh_from_db()
        return execute_history(self.project.id, user or self.user, {'action': action, **kwargs}, self.project.revision, str(uuid.uuid4()))

    def snapshot(self):
        return to_snapshot(current_state(self.project.id))

    def populate(self):
        self.save(diagram())
        return self.snapshot()

    def delete_unit(self):
        snap = self.populate()
        unit = next(e for e in snap['entidades'] if e['nombre'] == 'unidad')
        snap['entidades'].remove(unit)
        snap['relaciones'] = []
        self.save(snap)
        return unit

    def test_compound_create_undo_redo_preserves_all_original_ids_and_properties(self):
        self.populate()
        original = current_state(self.project.id)
        self.command()
        self.assertFalse(Entidad.objects.exists())
        self.assertEqual(History.objects.count(), 1)
        self.command('redo')
        self.assertEqual(original, current_state(self.project.id))
        self.assertEqual(History.objects.count(), 1)
        self.assertEqual(Receipt.objects.count(), 3)

    def test_delete_class_undo_restores_attributes_methods_parameters_visuals_and_relation(self):
        self.populate()
        original = current_state(self.project.id)
        self.save({'entidades': [], 'relaciones': []})
        self.command()
        self.assertEqual(original, current_state(self.project.id))

    def test_member_relation_and_property_edits_are_reversible(self):
        self.populate()
        for change in ('attribute', 'method', 'parameter', 'relation', 'rename', 'move', 'resize', 'multiplicity', 'role', 'navigation', 'port'):
            with self.subTest(change=change):
                before = current_state(self.project.id)
                snap = self.snapshot()
                e, r = snap['entidades'][0], snap['relaciones'][0]
                if change == 'attribute': e['atributos'] = []
                if change == 'method': e['operaciones'] = []
                if change == 'parameter': e['operaciones'][0]['parametros'] = []
                if change == 'relation': snap['relaciones'] = []
                if change == 'rename': e['nombre'] = 'renombrada'
                if change == 'move': e['coord_x'] += 77
                if change == 'resize': e['ancho'] += 88
                if change == 'multiplicity': r['cardinalidad_origen'] = '0..1'
                if change == 'role': r['rol_destino'] = 'items'
                if change == 'navigation': r['navegable_origen'] = True
                if change == 'port': r['puerto_origen'] = 'top-0'
                self.save(snap)
                after = current_state(self.project.id)
                self.command()
                self.assertEqual(before, current_state(self.project.id))
                self.command('redo')
                self.assertEqual(after, current_state(self.project.id))
                self.command()

    def test_batch_preserves_three_logical_boundaries_and_uses_one_revision(self):
        first = {'entidades': [entity()], 'relaciones': []}
        first['entidades'][0]['atributos'] = []
        second = deepcopy(first)
        second['entidades'][0]['atributos'] = entity()['atributos']
        third = deepcopy(second)
        third['entidades'][0]['coord_x'] = 500
        self.save(third, operations=[{'snapshot': s} for s in (first, second, third)])
        self.assertEqual(History.objects.count(), 3)
        self.project.refresh_from_db()
        self.assertEqual(self.project.revision, 1)
        self.command()
        self.assertEqual(Entidad.objects.get().coord_x, 72)
        self.assertEqual(Atributo.objects.count(), 1)
        self.command()
        self.assertEqual(Atributo.objects.count(), 0)
        self.assertEqual(Entidad.objects.count(), 1)
        self.command()
        self.assertEqual(Entidad.objects.count(), 0)
        for _ in range(3): self.command('redo')
        self.assertEqual(Entidad.objects.get().coord_x, 500)

    def test_new_action_invalidates_redo_persistently(self):
        self.populate()
        self.command()
        self.save({'entidades': [entity(-3, 'cliente')], 'relaciones': []})
        self.assertFalse(load_history(self.project.id, self.user)['canRedo'])
        self.assertEqual(History.objects.first().status, History.Status.INVALID)
        with self.assertRaises(HistoryError): self.command('redo')

    def test_noop_does_not_create_history_or_invalidate_redo(self):
        self.populate()
        self.command()
        self.save(self.snapshot())
        self.assertEqual(History.objects.count(), 1)
        self.assertTrue(load_history(self.project.id, self.user)['canRedo'])

    def test_specific_restore_preserves_independent_later_actions_and_is_undoable(self):
        unit = self.delete_unit()
        snapshot = self.snapshot()
        snapshot['entidades'].append(entity(-3, 'cliente'))
        self.save(snapshot)
        result = self.command('restore', kind='entity', name='UNIDAD')
        self.assertFalse(result['warnings'])
        self.assertEqual(set(Entidad.objects.values_list('nombre', flat=True)), {'unidad', 'producto', 'cliente'})
        self.assertEqual(Entidad.objects.get(nombre='unidad').id, unit['id'])
        self.assertEqual(Relacion.objects.count(), 1)
        self.assertEqual(Operacion.objects.get(entidad_id=unit['id']).parametros.count(), 1)
        self.command()
        self.assertFalse(Entidad.objects.filter(nombre='unidad').exists())
        self.assertTrue(Entidad.objects.filter(nombre='cliente').exists())

    def test_restore_attribute_method_and_relationship(self):
        self.populate()
        for table, kind, name in [('atributos', 'attribute', 'dirección'), ('operaciones', 'method', 'registrar'), ('relaciones', 'relationship', 'contiene')]:
            with self.subTest(kind=kind):
                snap = self.snapshot()
                unit = next(e for e in snap['entidades'] if e['nombre'] == 'unidad')
                if table == 'relaciones': snap[table] = []
                else: unit[table] = []
                self.save(snap)
                command = {'kind': kind, 'name': name}
                if table != 'relaciones': command['owner'] = 'unidad'
                self.command('restore', **command)
                self.assertTrue(current_state(self.project.id)[table])

    def test_restore_skips_missing_relation_endpoints_and_reports(self):
        self.delete_unit()
        self.save({'entidades': [], 'relaciones': []})
        result = self.command('restore', kind='entity', name='unidad')
        self.assertEqual(len(result['warnings']), 1)
        self.assertTrue(Entidad.objects.filter(nombre='unidad').exists())
        self.assertFalse(Relacion.objects.exists())

    def test_restore_ambiguous_and_missing_are_readonly(self):
        self.populate()
        snap = self.snapshot()
        for e in snap['entidades']: e['atributos'] = []
        self.save(snap)
        for command, code in [({'name': 'dirección'}, 'history_ambiguous'), ({'name': 'fantasma'}, 'history_not_found')]:
            with self.subTest(code=code):
                before = current_state(self.project.id)
                with self.assertRaises(HistoryError) as exc: self.command('restore', **command)
                self.assertEqual(exc.exception.code, code)
                self.assertEqual(before, current_state(self.project.id))
        self.command('restore', name='dirección', owner='unidad')

    def test_restore_latest_entity_and_relationship_by_endpoint_names(self):
        self.delete_unit()
        self.command('restore', kind='entity', latest=True)
        snap = self.snapshot()
        snap['relaciones'] = []
        self.save(snap)
        self.command('restore', kind='relationship', endpoints=['producto', 'unidad'])
        self.assertEqual(Relacion.objects.count(), 1)

    def test_no_duplicate_restore_or_restore_without_parent(self):
        unit = self.delete_unit()
        with self.assertRaises(HistoryError): self.command('restore', kind='attribute', name='dirección', owner='unidad')
        self.command('restore', kind='entity', name='unidad')
        with self.assertRaises(HistoryError): self.command('restore', kind='entity', name='unidad')
        self.assertEqual(Entidad.objects.filter(id=unit['id']).count(), 1)

    def test_history_survives_new_sessions_and_reading_never_changes_diagram(self):
        self.delete_unit()
        before = current_state(self.project.id)
        revision = Proyecto.objects.get(pk=self.project.id).revision
        for _ in range(3):
            client = APIClient()
            client.force_authenticate(User.objects.get(pk=self.user.pk))
            response = client.get(self.url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['revision'], revision)
            self.assertEqual(len(response.data['operations']), 2)
            self.assertEqual(current_state(self.project.id), before)
        self.command('restore', name='unidad')
        self.command()
        self.assertTrue(APIClientWithUser(self.user).get(self.url).data['canRedo'])
        self.command('redo')
        self.assertTrue(Entidad.objects.filter(nombre='unidad').exists())

    def test_users_and_diagrams_are_isolated_and_current_permissions_enforced(self):
        self.populate()
        self.assertEqual(load_history(self.project.id, self.other)['operations'], [])
        with self.assertRaises(HistoryError): self.command(user=self.other)
        other_project = Proyecto.objects.create(propietario=self.user, nombre='Other')
        self.assertEqual(load_history(other_project.id, self.user)['operations'], [])
        forbidden = APIClientWithUser(User.objects.create_user(username='outsider'))
        self.assertEqual(forbidden.get(self.url).status_code, 403)
        UserColaborador.objects.filter(usuario=self.other).update(rol='visualizador')
        response = APIClientWithUser(self.other).post(self.url, {'command': {'action': 'undo'}, 'request_id': 'viewer', 'expected_revision': 1}, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.get(self.url, {'usuario_id': self.other.id}).data['operations'][0]['status'], 'aplicada')

    def test_collaborator_attribute_prevents_undo_creation(self):
        self.save({'entidades': [entity()], 'relaciones': []})
        snap = self.snapshot()
        snap['entidades'][0]['atributos'].append({**entity()['atributos'][0], 'id': -90, 'nombre': 'remoto'})
        self.save(snap, self.other)
        before = current_state(self.project.id)
        self.assertFalse(load_history(self.project.id, self.user)['canUndo'])
        with self.assertRaises(HistoryError): self.command()
        self.assertEqual(before, current_state(self.project.id))
        self.assertTrue(Atributo.objects.filter(nombre='remoto').exists())

    def test_independent_remote_field_survives_undo(self):
        self.populate()
        snap = self.snapshot()
        snap['entidades'][0]['coord_x'] = 900
        self.save(snap)
        snap = self.snapshot()
        snap['entidades'][0]['nombre'] = 'cambio_remoto'
        self.save(snap, self.other)
        self.command()
        e = Entidad.objects.get(nombre='cambio_remoto')
        self.assertEqual(e.coord_x, 72)
        self.assertEqual(History.objects.filter(user=self.other).count(), 1)

    def test_remote_relationship_and_same_field_changes_block_undo(self):
        self.populate()
        snap = self.snapshot()
        snap['entidades'][0]['coord_x'] = 900
        self.save(snap)
        snap = self.snapshot()
        snap['entidades'][0]['coord_x'] = 1000
        self.save(snap, self.other)
        with self.assertRaises(HistoryError): self.command()
        self.assertEqual(Entidad.objects.order_by('id').first().coord_x, 1000)

    def test_current_locks_block_and_expire_without_restoring_old_locks(self):
        self.populate()
        eid = Entidad.objects.first().id
        self.assertTrue(acquire_lock(self.project.id, self.other, eid, 'connection'))
        with self.assertRaises(HistoryError) as exc: self.command()
        self.assertEqual(exc.exception.code, 'element_locked')
        DiagramEditLock.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        self.command()
        self.command('redo')
        self.assertFalse(Entidad.objects.exclude(estado='activo').exists())
        self.assertFalse(DiagramEditLock.objects.filter(expires_at__gt=timezone.now()).exists())

    def test_request_receipts_prevent_duplicate_save_and_history_even_with_stale_revision(self):
        snap = diagram()
        first = save_snapshot(self.project.id, self.user, snap, 0, 'same-save')
        second = save_snapshot(self.project.id, self.user, snap, 0, 'same-save')
        self.assertTrue(second['replayed'])
        self.assertEqual(second['revision'], first['revision'])
        self.assertEqual(History.objects.count(), 1)
        self.assertEqual(Entidad.objects.count(), 2)
        command = {'action': 'undo'}
        execute_history(self.project.id, self.user, command, 1, 'same-undo')
        execute_history(self.project.id, self.user, command, 1, 'same-undo')
        self.assertEqual(Proyecto.objects.get(pk=self.project.id).revision, 2)
        self.assertEqual(History.objects.count(), 1)
        with self.assertRaises(HistoryError) as exc: save_snapshot(self.project.id, self.user, {}, 0, 'same-save')
        self.assertEqual(exc.exception.code, 'idempotency_mismatch')

    def test_stale_revision_rejected_without_receipt_or_mutation(self):
        self.populate()
        with self.assertRaises(StaleRevision): execute_history(self.project.id, self.user, {'action': 'undo'}, 0, 'stale')
        self.assertFalse(Receipt.objects.filter(request_id='stale').exists())
        self.assertEqual(Entidad.objects.count(), 2)

    def test_failure_in_history_rolls_back_entire_snapshot_and_batch(self):
        with patch('modelado.history.record', side_effect=RuntimeError('history write failed')):
            with self.assertRaises(RuntimeError): self.save(diagram())
        self.assertFalse(Entidad.objects.exists())
        self.assertFalse(History.objects.exists())
        self.assertFalse(Receipt.objects.exists())
        self.assertEqual(Proyecto.objects.get(pk=self.project.id).revision, 0)
        good = {'entidades': [entity()], 'relaciones': []}
        bad = deepcopy(good)
        bad['relaciones'] = [{'id': -900, 'entidad_origen_id': -1, 'entidad_destino_id': -8}]
        with self.assertRaises(HistoryError): self.save(bad, operations=[{'snapshot': good}, {'snapshot': bad}])
        self.assertFalse(Entidad.objects.exists())
        self.assertFalse(History.objects.exists())

    def test_invalid_final_boundary_ids_references_and_uml_are_rejected(self):
        bad = diagram()
        bad['entidades'][0]['atributos'][0]['tipo_referencia_id'] = 999999
        with self.assertRaises(HistoryError): self.save(bad)
        with self.assertRaises(HistoryError): self.save(diagram(), operations=[{'snapshot': {}}])
        bad = diagram()
        bad['entidades'].append(deepcopy(bad['entidades'][0]))
        with self.assertRaises(HistoryError): self.save(bad)
        bad = diagram()
        bad['relaciones'][0]['cardinalidad_origen'] = 'invalido'
        with self.assertRaises(Exception): self.save(bad)
        self.assertFalse(History.objects.exists())
        self.assertFalse(Entidad.objects.exists())

    def test_deep_copies_and_unique_database_constraints(self):
        snap = diagram()
        result = self.save(snap)
        saved = deepcopy(History.objects.first().after)
        snap['entidades'][0]['atributos'].clear()
        self.assertEqual(History.objects.first().after, saved)
        receipt = Receipt.objects.first()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Receipt.objects.create(project=self.project, user=self.user, request_id=receipt.request_id, fingerprint='a', result={})
        op = History.objects.first()
        with self.assertRaises(IntegrityError), transaction.atomic():
            History.objects.create(project=self.project, user=self.user, request_id=op.request_id, batch_index=0,
                before={}, after={}, base_revision=0, confirmed_revision=result['revision'], description='duplicado')

    def test_retention_prunes_oldest_operation_and_keeps_receipts_and_other_users(self):
        original = diagram()
        self.save(original, request_id='first')
        self.save({'entidades': [], 'relaciones': []})
        for i in range(51):
            snap = self.snapshot()
            if not snap['entidades']: snap['entidades'] = [entity(-100, 'cliente')]
            snap['entidades'][0]['coord_x'] = i
            self.save(snap)
        self.assertEqual(History.objects.filter(user=self.user).count(), 50)
        self.assertTrue(Receipt.objects.filter(request_id='first').exists())
        with self.assertRaises(HistoryError): self.command('restore', name='unidad')
        self.command()
        self.command('redo')
        replay = save_snapshot(self.project.id, self.user, original, 0, 'first')
        self.assertTrue(replay['replayed'])
        self.assertFalse(Entidad.objects.filter(nombre='unidad').exists())

    def test_preimplementation_deletions_are_not_invented(self):
        Entidad.objects.create(proyecto=self.project, nombre='antigua').delete()
        with self.assertRaises(HistoryError): self.command('restore', name='antigua')
        self.assertFalse(Entidad.objects.exists())

    def test_post_commit_broadcast_and_no_broadcast_on_failed_write(self):
        self.populate()
        with patch('modelado.history.notificar_evento_proyecto_sync') as notify:
            with self.captureOnCommitCallbacks(execute=True) as callbacks:
                self.command()
                notify.assert_not_called()
            self.assertEqual(len(callbacks), 1)
            notify.assert_called_once()
            self.assertEqual(notify.call_args.args[1], 'history.updated')


def APIClientWithUser(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


class HistoryWebsocketTests(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ws-history')
        self.project = Proyecto.objects.create(propietario=self.user, nombre='WS history')

    def test_snapshot_retry_returns_same_receipt_without_broadcasting_duplicate(self):
        async def scenario():
            app = PizarraConsumer.as_asgi()
            socket = WebsocketCommunicator(app, '/ws/')
            socket.scope['user'] = self.user
            socket.scope['url_route'] = {'kwargs': {'proyecto_id': self.project.id}}
            connected, _ = await socket.connect()
            self.assertTrue(connected)
            await socket.receive_json_from()
            payload = {'accion': 'guardar_snapshot', 'datos_diagrama': diagram(), 'expected_revision': 0, 'request_id': 'lost-ack'}
            await socket.send_json_to(payload)
            ack = await socket.receive_json_from()
            self.assertEqual(ack['accion'], 'snapshot_guardado')
            await socket.send_json_to(payload)
            retry = await socket.receive_json_from()
            self.assertTrue(retry['replayed'])
            self.assertEqual(retry['revision'], ack['revision'])
            await socket.disconnect()
        async_to_sync(scenario)()
        self.assertEqual(History.objects.count(), 1)
        self.assertEqual(Entidad.objects.count(), 2)

    def test_confirmed_undo_reaches_both_collaborators_after_commit(self):
        other = User.objects.create_user(username='ws-history-other')
        UserColaborador.objects.create(usuario=other, proyecto=self.project, rol='editor', estado='activo')
        save_snapshot(self.project.id, self.user, diagram(), 0, 'seed')
        async def scenario():
            async def connect(user):
                socket = WebsocketCommunicator(PizarraConsumer.as_asgi(), '/ws/')
                socket.scope['user'] = user
                socket.scope['url_route'] = {'kwargs': {'proyecto_id': self.project.id}}
                await socket.connect()
                await socket.receive_json_from()
                return socket
            owner_socket = await connect(self.user)
            other_socket = await connect(other)
            await owner_socket.receive_json_from()
            result = await database_sync_to_async(execute_history)(self.project.id, self.user, {'action': 'undo'}, 1, 'shared-undo')
            for socket in (owner_socket, other_socket):
                event = await socket.receive_json_from()
                self.assertEqual(event['accion'], 'history.updated')
                self.assertEqual(event['revision'], result['revision'])
            await owner_socket.disconnect()
            await other_socket.disconnect()
        async_to_sync(scenario)()
        self.assertFalse(Entidad.objects.exists())
        self.assertFalse(History.objects.filter(user=other).exists())


class HistoryMigrationTests(TransactionTestCase):
    def test_additive_migration_preserves_existing_diagram(self):
        executor = MigrationExecutor(connection)
        executor.migrate([('modelado', '0013_proyecto_revision')])
        try:
            user = User.objects.create_user(username='migration-history')
            project = Proyecto.objects.create(propietario=user, nombre='Existing')
            entity = Entidad.objects.create(proyecto=project, nombre='Preservada')
            executor = MigrationExecutor(connection)
            executor.migrate([('modelado', '0014_diagrameditlock_diagramhistoryoperation_and_more')])
            self.assertEqual(Entidad.objects.get(pk=entity.pk).nombre, 'Preservada')
            self.assertFalse(History.objects.exists())
            self.assertEqual(Proyecto.objects.get(pk=project.pk).revision, 0)
        finally:
            MigrationExecutor(connection).migrate([('modelado', '0014_diagrameditlock_diagramhistoryoperation_and_more')])


@skipUnless(connection.vendor == 'postgresql', 'Concurrencia real requiere PostgreSQL')
class HistoryConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='concurrent-history')
        self.project = Proyecto.objects.create(propietario=self.user, nombre='Concurrent history')

    def race(self, ids):
        barrier = Barrier(2)
        def write(request_id):
            try:
                barrier.wait(timeout=10)
                return save_snapshot(self.project.id, self.user, diagram(), 0, request_id)
            except StaleRevision:
                return 'stale'
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(write, request_id) for request_id in ids]
            return [f.result(timeout=20) for f in futures]

    def test_concurrent_different_requests_cannot_overwrite_each_other(self):
        result = self.race(['first-client', 'second-client'])
        self.assertEqual(result.count('stale'), 1)
        self.assertEqual(History.objects.count(), 1)
        self.assertEqual(Proyecto.objects.get(pk=self.project.id).revision, 1)

    def test_concurrent_duplicate_requests_share_one_receipt_and_one_change(self):
        result = self.race(['same-request', 'same-request'])
        self.assertEqual(sum(bool(r.get('replayed')) for r in result), 1)
        self.assertEqual(History.objects.count(), 1)
        self.assertEqual(Receipt.objects.count(), 1)
        self.assertEqual(Entidad.objects.count(), 2)
