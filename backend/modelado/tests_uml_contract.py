from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from modelado.consumers import PizarraConsumer
from modelado.models import Atributo, Entidad, Operacion, ParametroOperacion, Proyecto, Relacion
from modelado.serializers import EntidadDiagramaSerializer, RelacionDiagramaSerializer
from generador.services.xmi_exporter import XMIExporter
from generador.services.xmi_importer import XMIImporter
from usuario.models import UserColaborador


User = get_user_model()


class UmlContractModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='uml-owner', password='test')
        self.project = Proyecto.objects.create(propietario=self.owner, nombre='UML')

    def test_legacy_classifier_defaults_are_backward_compatible(self):
        legacy = Entidad.objects.create(proyecto=self.project, nombre='Cliente')
        attribute = Atributo.objects.create(
            entidad=legacy, nombre='nombre', tipo=Atributo.Tipo.STRING, orden=1
        )

        data = EntidadDiagramaSerializer(legacy).data

        self.assertEqual(data['tipo_clasificador'], Entidad.TipoClasificador.CLASE)
        self.assertFalse(data['abstracto'])
        self.assertEqual(data['operaciones'], [])
        self.assertEqual(data['atributos'][0]['id'], attribute.id)
        self.assertEqual(data['atributos'][0]['visibilidad'], 'private')
        self.assertEqual(data['atributos'][0]['valor_predeterminado'], '')

    def test_class_interface_entity_attributes_operations_and_type_references_round_trip(self):
        domain = Entidad.objects.create(
            proyecto=self.project,
            nombre='Pedido',
            tipo_clasificador=Entidad.TipoClasificador.ENTIDAD_PERSISTENTE,
        )
        contract = Entidad.objects.create(
            proyecto=self.project,
            nombre='Pagable',
            tipo_clasificador=Entidad.TipoClasificador.INTERFAZ,
            abstracto=True,
        )
        Entidad.objects.create(
            proyecto=self.project,
            nombre='BasePedido',
            tipo_clasificador=Entidad.TipoClasificador.CLASE,
            abstracto=True,
        )
        attribute = Atributo.objects.create(
            entidad=domain,
            nombre='pagable',
            tipo='Pagable',
            tipo_referencia=contract,
            visibilidad='protected',
            es_estatico=True,
            valor_predeterminado='null',
            orden=3,
        )
        operation = Operacion.objects.create(
            entidad=domain,
            nombre='procesar',
            visibilidad='public',
            tipo_retorno='Pagable',
            retorno_referencia=contract,
            orden=2,
            es_abstracto=True,
        )
        parameter = ParametroOperacion.objects.create(
            operacion=operation,
            nombre='entrada',
            tipo='Pagable',
            tipo_referencia=contract,
            orden=1,
        )

        data = EntidadDiagramaSerializer(domain).data

        self.assertEqual(data['tipo_clasificador'], 'entidad_persistente')
        self.assertEqual(data['atributos'][0]['id'], attribute.id)
        self.assertEqual(data['atributos'][0]['tipo_referencia_id'], contract.id)
        self.assertEqual(data['operaciones'][0]['id'], operation.id)
        self.assertEqual(data['operaciones'][0]['retorno_referencia_id'], contract.id)
        self.assertEqual(data['operaciones'][0]['parametros'][0]['id'], parameter.id)
        self.assertEqual(
            data['operaciones'][0]['parametros'][0]['tipo_referencia_id'], contract.id
        )

    def test_all_relation_kinds_preserve_endpoint_semantics(self):
        source = Entidad.objects.create(proyecto=self.project, nombre='Origen')
        target = Entidad.objects.create(proyecto=self.project, nombre='Destino')

        for index, relation_type in enumerate(Relacion.Tipo.values):
            relation = Relacion.objects.create(
                proyecto=self.project,
                entidad_origen=source,
                entidad_destino=target,
                tipo=relation_type,
                cardinalidad_origen='1',
                cardinalidad_destino='0..*',
                rol_origen=f'origen{index}',
                rol_destino=f'destino{index}',
                navegable_origen=index % 2 == 0,
                navegable_destino=index % 2 == 1,
            )
            data = RelacionDiagramaSerializer(relation).data
            self.assertEqual(data['tipo'], relation_type)
            self.assertEqual(data['cardinalidad_origen'], '1')
            self.assertEqual(data['cardinalidad_destino'], '0..*')
            self.assertEqual(data['rol_origen'], f'origen{index}')
            self.assertEqual(data['rol_destino'], f'destino{index}')

    def test_existing_xmi_round_trip_keeps_legacy_contract(self):
        source = Entidad.objects.create(proyecto=self.project, nombre='Cliente')
        target = Entidad.objects.create(proyecto=self.project, nombre='Pedido')
        Atributo.objects.create(
            entidad=source, nombre='id', tipo=Atributo.Tipo.LONG, es_clave=True, orden=1
        )
        Relacion.objects.create(
            proyecto=self.project,
            entidad_origen=source,
            entidad_destino=target,
            tipo=Relacion.Tipo.ASOCIACION,
            cardinalidad_origen='1',
            cardinalidad_destino='0..*',
        )
        xml = XMIExporter(self.project).exportar_xml()
        imported_project = Proyecto.objects.create(propietario=self.owner, nombre='Importado')

        result = XMIImporter(imported_project).importar_xml(xml, reemplazar_existente=True)

        self.assertGreaterEqual(result['entidades_creadas'], 2)
        imported = imported_project.entidades.get(nombre='Cliente')
        self.assertEqual(
            imported.tipo_clasificador,
            Entidad.TipoClasificador.ENTIDAD_PERSISTENTE,
        )
        self.assertFalse(imported.abstracto)
        self.assertEqual(imported.operaciones.count(), 0)
        imported_id = imported.atributos.get(nombre='id')
        self.assertEqual(imported_id.tipo, Atributo.Tipo.LONG)
        self.assertTrue(imported_id.es_clave)
        self.assertEqual(result['claves_explicitamente_importadas'], 1)

    def test_reimport_preserves_unambiguous_persistent_key(self):
        existing = Entidad.objects.create(
            proyecto=self.project,
            nombre='Cliente',
            tipo_clasificador=Entidad.TipoClasificador.ENTIDAD_PERSISTENTE,
        )
        Atributo.objects.create(
            entidad=existing,
            nombre='uuid',
            tipo=Atributo.Tipo.STRING,
            es_clave=True,
            orden=1,
        )
        donor = Proyecto.objects.create(propietario=self.owner, nombre='Donante')
        donor_entity = Entidad.objects.create(proyecto=donor, nombre='Cliente')
        Atributo.objects.create(
            entidad=donor_entity,
            nombre='uuid',
            tipo=Atributo.Tipo.STRING,
            es_clave=False,
            orden=1,
        )
        xml = XMIExporter(donor).exportar_xml()

        result = XMIImporter(self.project).importar_xml(xml, reemplazar_existente=True)

        imported = self.project.entidades.get(nombre='Cliente')
        imported_key = imported.atributos.get(nombre='uuid')
        self.assertEqual(
            imported.tipo_clasificador,
            Entidad.TipoClasificador.ENTIDAD_PERSISTENTE,
        )
        self.assertTrue(imported_key.es_clave)
        self.assertFalse(imported_key.es_nulo)
        self.assertEqual(result['claves_preservadas'], 1)

    def test_extended_xmi_round_trip_preserves_supported_uml_semantics(self):
        interface = Entidad.objects.create(
            proyecto=self.project, nombre='Pagable',
            tipo_clasificador=Entidad.TipoClasificador.INTERFAZ, abstracto=True,
        )
        domain = Entidad.objects.create(
            proyecto=self.project, nombre='Pedido',
            tipo_clasificador=Entidad.TipoClasificador.ENTIDAD_PERSISTENTE,
        )
        Atributo.objects.create(
            entidad=domain, nombre='contrato', tipo='Pagable', tipo_referencia=interface,
            visibilidad='protected', es_estatico=True, valor_predeterminado='null', orden=1,
        )
        operation = Operacion.objects.create(
            entidad=domain, nombre='pagar', tipo_retorno='Pagable',
            retorno_referencia=interface, es_abstracto=True, orden=1,
        )
        ParametroOperacion.objects.create(
            operacion=operation, nombre='entrada', tipo='Pagable',
            tipo_referencia=interface, orden=1,
        )
        Relacion.objects.create(
            proyecto=self.project, entidad_origen=domain, entidad_destino=interface,
            tipo=Relacion.Tipo.IMPLEMENTACION,
        )

        xml = XMIExporter(self.project).exportar_xml()
        imported_project = Proyecto.objects.create(propietario=self.owner, nombre='Importado UML')
        XMIImporter(imported_project).importar_xml(xml, reemplazar_existente=True)

        imported_interface = imported_project.entidades.get(nombre='Pagable')
        imported_domain = imported_project.entidades.get(nombre='Pedido')
        self.assertEqual(imported_interface.tipo_clasificador, Entidad.TipoClasificador.INTERFAZ)
        self.assertTrue(imported_interface.abstracto)
        attribute = imported_domain.atributos.get(nombre='contrato')
        self.assertEqual(attribute.tipo_referencia, imported_interface)
        self.assertEqual(attribute.visibilidad, 'protected')
        self.assertTrue(attribute.es_estatico)
        self.assertEqual(attribute.valor_predeterminado, 'null')
        imported_operation = imported_domain.operaciones.get(nombre='pagar')
        self.assertEqual(imported_operation.retorno_referencia, imported_interface)
        self.assertTrue(imported_operation.es_abstracto)
        self.assertEqual(imported_operation.parametros.get(nombre='entrada').tipo_referencia, imported_interface)
        self.assertTrue(imported_project.relaciones.filter(
            entidad_origen=imported_domain, entidad_destino=imported_interface,
            tipo=Relacion.Tipo.IMPLEMENTACION,
        ).exists())


class UmlContractApiTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='api-owner', password='test')
        self.viewer = User.objects.create_user(username='api-viewer', password='test')
        self.outsider = User.objects.create_user(username='api-outsider', password='test')
        self.project = Proyecto.objects.create(propietario=self.owner, nombre='API UML')
        UserColaborador.objects.create(
            proyecto=self.project,
            usuario=self.viewer,
            rol=UserColaborador.Rol.VISUALIZADOR,
            estado=UserColaborador.Estado.ACTIVO,
        )
        entity = Entidad.objects.create(
            proyecto=self.project,
            nombre='Contrato',
            tipo_clasificador=Entidad.TipoClasificador.INTERFAZ,
        )
        Operacion.objects.create(entidad=entity, nombre='ejecutar', orden=1)
        self.client = APIClient()
        self.url = f'/api/modelado/proyectos/{self.project.id}/diagrama/'

    def test_initial_load_exposes_contract_to_authorized_readers_only(self):
        for user in (self.owner, self.viewer):
            self.client.force_authenticate(user=user)
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['entidades'][0]['tipo_clasificador'], 'interfaz')
            self.assertEqual(response.data['entidades'][0]['operaciones'][0]['nombre'], 'ejecutar')

        self.client.force_authenticate(user=self.outsider)
        self.assertEqual(self.client.get(self.url).status_code, 403)


class UmlSnapshotPersistenceTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.owner = User.objects.create_user(username='ws-uml-owner', password='test')
        self.viewer = User.objects.create_user(username='ws-uml-viewer', password='test')
        self.project = Proyecto.objects.create(propietario=self.owner, nombre='WS UML')
        UserColaborador.objects.create(
            proyecto=self.project,
            usuario=self.viewer,
            rol=UserColaborador.Rol.VISUALIZADOR,
            estado=UserColaborador.Estado.ACTIVO,
        )

    async def open_socket(self, user):
        socket = WebsocketCommunicator(PizarraConsumer.as_asgi(), '/ws/test/')
        socket.scope['user'] = user
        socket.scope['url_route'] = {'kwargs': {'proyecto_id': self.project.id}}
        connected, _ = await socket.connect()
        self.assertTrue(connected)
        await socket.receive_json_from()
        return socket

    @database_sync_to_async
    def stored_contract(self):
        entities = list(Entidad.objects.filter(proyecto=self.project).order_by('id'))
        relation = Relacion.objects.get(proyecto=self.project)
        domain = next(item for item in entities if item.nombre == 'Pedido')
        attribute = domain.atributos.get()
        operation = domain.operaciones.get()
        parameter = operation.parametros.get()
        return {
            'entity_ids': [item.id for item in entities],
            'attribute_id': attribute.id,
            'attribute_ref': attribute.tipo_referencia_id,
            'attribute_semantics': (
                attribute.visibilidad,
                attribute.es_estatico,
                attribute.valor_predeterminado,
            ),
            'operation_id': operation.id,
            'return_ref': operation.retorno_referencia_id,
            'parameter_id': parameter.id,
            'parameter_ref': parameter.tipo_referencia_id,
            'relation_id': relation.id,
            'relation_type': relation.tipo,
            'roles': (relation.rol_origen, relation.rol_destino),
            'navigation': (relation.navegable_origen, relation.navegable_destino),
        }

    def test_snapshot_round_trip_remaps_then_preserves_all_stable_ids(self):
        async def scenario():
            socket = await self.open_socket(self.owner)
            snapshot = {
                'entidades': [
                    {
                        'id': -1, 'nombre': 'Pedido', 'tipo_clasificador': 'entidad_persistente',
                        'abstracto': False, 'atributos': [{
                            'id': -11, 'nombre': 'pagable', 'tipo': 'Pagable',
                            'tipo_referencia_id': -2, 'visibilidad': 'protected',
                            'es_estatico': True, 'valor_predeterminado': 'null', 'orden': 1,
                        }],
                        'operaciones': [{
                            'id': -21, 'nombre': 'procesar', 'tipo_retorno': 'Pagable',
                            'retorno_referencia_id': -2, 'orden': 1,
                            'parametros': [{
                                'id': -31, 'nombre': 'entrada', 'tipo': 'Pagable',
                                'tipo_referencia_id': -2, 'orden': 1,
                            }],
                        }],
                    },
                    {
                        'id': -2, 'nombre': 'Pagable', 'tipo_clasificador': 'interfaz',
                        'abstracto': True, 'atributos': [], 'operaciones': [],
                    },
                ],
                'relaciones': [{
                    'id': -41, 'tipo': 'implementacion', 'entidad_origen_id': -1,
                    'entidad_destino_id': -2, 'cardinalidad_origen': '1',
                    'cardinalidad_destino': '1', 'rol_origen': 'implementador',
                    'rol_destino': 'contrato', 'navegable_origen': False,
                    'navegable_destino': True,
                }],
            }
            await socket.send_json_to({'accion': 'guardar_snapshot', 'snapshot': snapshot, 'expected_revision': 0})
            result = await socket.receive_json_from()
            self.assertTrue(result['exito'])
            self.assertEqual(set(result['id_map']), {'-1', '-2'})
            self.assertEqual(set(result['attr_id_map']), {'-11'})
            self.assertEqual(set(result['operation_id_map']), {'-21'})
            self.assertEqual(set(result['parameter_id_map']), {'-31'})
            first = await self.stored_contract()
            self.assertEqual(first['attribute_ref'], result['id_map']['-2'])
            self.assertEqual(first['return_ref'], result['id_map']['-2'])
            self.assertEqual(first['parameter_ref'], result['id_map']['-2'])
            self.assertEqual(first['relation_type'], 'implementacion')
            self.assertEqual(first['roles'], ('implementador', 'contrato'))
            self.assertEqual(first['navigation'], (False, True))

            snapshot['entidades'][0]['id'] = result['id_map']['-1']
            snapshot['entidades'][1]['id'] = result['id_map']['-2']
            snapshot['entidades'][0]['atributos'][0]['id'] = result['attr_id_map']['-11']
            snapshot['entidades'][0]['atributos'][0]['tipo_referencia_id'] = result['id_map']['-2']
            operation = snapshot['entidades'][0]['operaciones'][0]
            operation['id'] = result['operation_id_map']['-21']
            operation['retorno_referencia_id'] = result['id_map']['-2']
            operation['parametros'][0]['id'] = result['parameter_id_map']['-31']
            operation['parametros'][0]['tipo_referencia_id'] = result['id_map']['-2']
            snapshot['relaciones'][0]['id'] = result['rel_id_map']['-41']
            snapshot['relaciones'][0]['entidad_origen_id'] = result['id_map']['-1']
            snapshot['relaciones'][0]['entidad_destino_id'] = result['id_map']['-2']
            await socket.send_json_to({'accion': 'guardar_snapshot', 'snapshot': snapshot, 'expected_revision': 1})
            second_result = await socket.receive_json_from()
            self.assertTrue(second_result['exito'])
            second = await self.stored_contract()
            self.assertEqual(first, second)

            legacy_snapshot = {
                'entidades': [
                    {
                        'id': snapshot['entidades'][0]['id'],
                        'nombre': 'Pedido',
                        'atributos': [{
                            'id': snapshot['entidades'][0]['atributos'][0]['id'],
                            'nombre': 'pagable', 'tipo': 'Pagable', 'orden': 1,
                        }],
                    },
                    {
                        'id': snapshot['entidades'][1]['id'],
                        'nombre': 'Pagable', 'atributos': [],
                    },
                ],
                'relaciones': [{
                    'id': snapshot['relaciones'][0]['id'],
                    'tipo': 'implementacion',
                    'entidad_origen_id': snapshot['relaciones'][0]['entidad_origen_id'],
                    'entidad_destino_id': snapshot['relaciones'][0]['entidad_destino_id'],
                    'cardinalidad_origen': '1', 'cardinalidad_destino': '1',
                }],
            }
            await socket.send_json_to({
                'accion': 'guardar_snapshot', 'snapshot': legacy_snapshot, 'expected_revision': 2
            })
            legacy_result = await socket.receive_json_from()
            self.assertTrue(legacy_result['exito'])
            self.assertEqual(first, await self.stored_contract())
            await socket.disconnect()

        async_to_sync(scenario)()

    def test_viewer_cannot_persist_extended_snapshot(self):
        async def scenario():
            socket = await self.open_socket(self.viewer)
            await socket.send_json_to({
                'accion': 'guardar_snapshot',
                'snapshot': {'entidades': [], 'relaciones': []},
            })
            response = await socket.receive_json_from()
            self.assertEqual(response['accion'], 'permiso_denegado')
            await socket.disconnect()

        async_to_sync(scenario)()
