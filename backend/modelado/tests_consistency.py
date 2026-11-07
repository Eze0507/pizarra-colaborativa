from copy import deepcopy
from unittest.mock import patch

from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from .consistency import read_authoritative_state, validate_expected_revision
from .consumers import PizarraConsumer
from .models import Entidad, Operacion, Proyecto
from usuario.models import UserColaborador


User = get_user_model()


class RevisionRestTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="revision-owner", password="test")
        self.project = Proyecto.objects.create(propietario=self.owner, nombre="Revision")
        self.client = APIClient()
        self.client.force_authenticate(self.owner)
        self.detail = f"/api/modelado/proyectos/{self.project.id}/"
        self.diagram = f"/api/modelado/proyectos/{self.project.id}/diagrama/"
        self.validation = f"/api/modelado/proyectos/{self.project.id}/validacion/"

    def test_initial_revision_and_reads_do_not_increment(self):
        self.assertEqual(self.project.revision, 0)
        self.assertEqual(self.client.get(self.diagram).data["proyecto"]["revision"], 0)
        validation = self.client.get(self.validation, {"perfil": "uml"})
        self.assertEqual(validation.data["revision"], 0)
        exported = self.client.get(
            f"/api/generador/proyectos/{self.project.id}/exportar-xml/"
        )
        self.assertEqual(exported.status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(self.project.revision, 0)

    def test_rest_write_requires_exact_revision_and_increments_once(self):
        missing = self.client.patch(self.detail, {"nombre": "Sin revision"}, format="json")
        self.assertEqual(missing.status_code, 400)
        with patch("modelado.views.notificar_evento_proyecto_sync") as notify:
            with self.captureOnCommitCallbacks(execute=True):
                accepted = self.client.patch(
                    self.detail,
                    {"nombre": "Confirmado", "expected_revision": 0},
                    format="json",
                )
        notify.assert_called_once_with(
            self.project.id,
            "diagram.updated",
            {"proyecto_id": self.project.id, "revision": 1, "usuario_id": self.owner.id},
        )
        self.assertEqual(accepted.status_code, 200)
        self.assertEqual(accepted.data["revision"], 1)
        stale = self.client.patch(
            self.detail, {"nombre": "Obsoleto", "expected_revision": 0}, format="json"
        )
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(stale.data["current_revision"], 1)
        self.project.refresh_from_db()
        self.assertEqual((self.project.nombre, self.project.revision), ("Confirmado", 1))

    def test_snapshot_cannot_be_written_through_project_patch(self):
        original = deepcopy(self.project.datos_diagrama)
        response = self.client.patch(
            self.detail,
            {"datos_diagrama": {"entidades": [{"id": 999}]}, "expected_revision": 0},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.project.refresh_from_db()
        self.assertEqual(self.project.datos_diagrama, original)
        self.assertEqual(self.project.revision, 0)

    def test_expected_revision_rejects_bool_string_and_negative(self):
        for value in (True, "0", -1, None):
            with self.assertRaises(ValueError):
                validate_expected_revision(value)

    def test_authoritative_read_removes_ghosts_and_prefers_orm_coordinates(self):
        entity = Entidad.objects.create(
            proyecto=self.project, nombre="Pedido", coord_x=80, coord_y=90, ancho=240
        )
        Operacion.objects.create(entidad=entity, nombre="procesar", tipo_retorno="void")
        self.project.datos_diagrama = {
            "desconocido": {"preservado": True},
            "posiciones": {str(entity.id): {"x": 1, "y": 2}, "999": {"x": 3, "y": 4}},
            "entidades": [
                {"id": entity.id, "coord_x": 1, "coord_y": 2, "ancho": 100, "color": "blue"},
                {"id": 999, "nombre": "Fantasma"},
            ],
        }
        self.project.save(update_fields=["datos_diagrama"])
        state = read_authoritative_state(self.project.id)
        self.assertEqual(state.visual_snapshot["posiciones"], {
            str(entity.id): {"x": 80.0, "y": 90.0}
        })
        self.assertEqual(len(state.visual_snapshot["entidades"]), 1)
        visual = state.visual_snapshot["entidades"][0]
        self.assertEqual(
            (visual["id"], visual["coord_x"], visual["coord_y"], visual["ancho"], visual["color"]),
            (entity.id, 80.0, 90.0, 240.0, "blue"),
        )
        self.assertEqual(visual["operaciones"][0]["nombre"], "procesar")
        self.assertTrue(state.visual_snapshot["desconocido"]["preservado"])

    def test_xmi_import_uses_revision(self):
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <xmi:XMI xmlns:xmi="http://schema.omg.org/spec/XMI/2.1" xmlns:uml="http://schema.omg.org/spec/UML/2.1">
          <uml:Model xmi:type="uml:Model" xmi:id="m1" name="M">
            <packagedElement xmi:type="uml:Class" xmi:id="c1" name="Pedido"/>
          </uml:Model>
        </xmi:XMI>'''
        url = f"/api/generador/proyectos/{self.project.id}/importar-xml/"
        accepted = self.client.post(
            url, {"contenido_xml": xml, "expected_revision": 0}, format="json"
        )
        self.assertEqual(accepted.status_code, 200)
        self.assertEqual(accepted.data["revision"], 1)
        stale = self.client.post(
            url, {"contenido_xml": xml, "expected_revision": 0}, format="json"
        )
        self.assertEqual(stale.status_code, 409)


class RevisionWebSocketTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.owner = User.objects.create_user(username="revision-ws", password="test")
        self.editor = User.objects.create_user(username="revision-ws-editor", password="test")
        self.project = Proyecto.objects.create(propietario=self.owner, nombre="WS")
        UserColaborador.objects.create(
            proyecto=self.project,
            usuario=self.editor,
            rol=UserColaborador.Rol.EDITOR,
            estado=UserColaborador.Estado.ACTIVO,
        )

    async def open_socket(self, user=None, route_project_id=None):
        socket = WebsocketCommunicator(PizarraConsumer.as_asgi(), "/ws/test/")
        socket.scope["user"] = user or self.owner
        socket.scope["url_route"] = {
            "kwargs": {
                "proyecto_id": self.project.id if route_project_id is None else route_project_id
            }
        }
        connected, _ = await socket.connect()
        self.assertTrue(connected)
        await socket.receive_json_from()
        return socket

    def test_snapshot_revision_conflict_and_missing_revision(self):
        async def scenario():
            socket = await self.open_socket()
            snapshot = {"entidades": [], "relaciones": []}
            await socket.send_json_to({"accion": "guardar_snapshot", "snapshot": snapshot})
            missing = await socket.receive_json_from()
            self.assertEqual(missing["codigo"], "invalid_expected_revision")

            await socket.send_json_to({
                "accion": "guardar_snapshot", "snapshot": snapshot,
                "expected_revision": 0, "request_id": "r1",
            })
            success = await socket.receive_json_from()
            self.assertEqual(
                (success["exito"], success["revision"], success["request_id"], success["proyecto_id"]),
                (True, 1, "r1", self.project.id),
            )

            await socket.send_json_to({
                "accion": "guardar_snapshot", "snapshot": snapshot,
                "expected_revision": 0, "request_id": "r2",
            })
            stale = await socket.receive_json_from()
            self.assertEqual(stale["codigo"], "stale_revision")
            self.assertEqual(stale["current_revision"], 1)
            self.assertEqual(stale["proyecto_id"], self.project.id)
            await socket.disconnect()

        async_to_sync(scenario)()
        self.project.refresh_from_db()
        self.assertEqual(self.project.revision, 1)

    def test_snapshot_ack_normalizes_regex_project_id_to_number(self):
        async def scenario():
            socket = await self.open_socket(route_project_id=str(self.project.id))
            await socket.send_json_to({
                "accion": "guardar_snapshot",
                "snapshot": {"entidades": [], "relaciones": []},
                "expected_revision": 0,
                "request_id": "regex-route-id",
            })
            success = await socket.receive_json_from()
            self.assertEqual(success["accion"], "snapshot_guardado")
            self.assertEqual(success["proyecto_id"], self.project.id)
            self.assertIsInstance(success["proyecto_id"], int)
            await socket.disconnect()

        async_to_sync(scenario)()

    def test_structural_preview_is_not_published_before_commit(self):
        async def scenario():
            socket = await self.open_socket()
            await socket.send_json_to({
                "accion": "crear_entidad", "entidad": {"id": -1, "nombre": "Pendiente"}
            })
            self.assertTrue(await socket.receive_nothing(timeout=0.1))
            await socket.disconnect()

        async_to_sync(scenario)()
        self.assertEqual(self.project.entidades.count(), 0)

    def test_failed_snapshot_rolls_back_without_success_event(self):
        async def scenario():
            socket = await self.open_socket()
            await socket.send_json_to({
                "accion": "guardar_snapshot", "expected_revision": 0,
                "request_id": "fallo-1",
                "snapshot": {"entidades": [{"id": -1, "nombre": "X", "coord_x": "invalido"}]},
            })
            response = await socket.receive_json_from()
            self.assertEqual(response["accion"], "comando_rechazado")
            self.assertFalse(response["exito"])
            self.assertEqual(response["request_id"], "fallo-1")
            self.assertEqual(response["proyecto_id"], self.project.id)
            await socket.disconnect()

        async_to_sync(scenario)()
        self.project.refresh_from_db()
        self.assertEqual(self.project.revision, 0)
        self.assertEqual(self.project.entidades.count(), 0)

    def test_two_clients_cannot_silently_overwrite_the_same_revision(self):
        async def scenario():
            owner_socket = await self.open_socket(self.owner)
            editor_socket = await self.open_socket(self.editor)
            joined = await owner_socket.receive_json_from()
            self.assertEqual(joined["accion"], "colaborador_unido")

            snapshot_a = {"entidades": [], "relaciones": [], "marca": "A"}
            await owner_socket.send_json_to({
                "accion": "guardar_snapshot", "expected_revision": 0,
                "request_id": "owner-a", "snapshot": snapshot_a,
            })
            owner_ack = await owner_socket.receive_json_from()
            editor_remote_ack = await editor_socket.receive_json_from()
            self.assertEqual(owner_ack["revision"], 1)
            self.assertEqual(editor_remote_ack["request_id"], "owner-a")

            await editor_socket.send_json_to({
                "accion": "guardar_snapshot", "expected_revision": 0,
                "request_id": "editor-b", "snapshot": {
                    "entidades": [], "relaciones": [], "marca": "B"
                },
            })
            stale = await editor_socket.receive_json_from()
            self.assertEqual(stale["codigo"], "stale_revision")
            self.assertEqual(stale["current_revision"], 1)
            self.assertEqual(stale["request_id"], "editor-b")
            await owner_socket.disconnect()
            await editor_socket.disconnect()

        async_to_sync(scenario)()
        self.project.refresh_from_db()
        self.assertEqual(self.project.revision, 1)
        self.assertEqual(self.project.datos_diagrama["marca"], "A")
