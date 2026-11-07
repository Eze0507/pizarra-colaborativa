from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from rest_framework import status
from rest_framework.test import APITestCase

from modelado.consumers import PizarraConsumer
from modelado.models import Proyecto
from modelado.realtime import get_proyecto_group_name
from usuario.models import UserColaborador


User = get_user_model()


class ProjectPermissionFixture:
    def create_fixture(self):
        self.owner = User.objects.create_user(username="owner", password="test")
        self.editor = User.objects.create_user(username="editor", password="test")
        self.viewer = User.objects.create_user(username="viewer", password="test")
        self.removed = User.objects.create_user(username="removed", password="test")
        self.pending = User.objects.create_user(username="pending", password="test")
        self.outsider = User.objects.create_user(username="outsider", password="test")
        self.project = Proyecto.objects.create(propietario=self.owner, nombre="Permisos")
        self.memberships = {}
        for user, role in (
            (self.editor, UserColaborador.Rol.EDITOR),
            (self.viewer, UserColaborador.Rol.VISUALIZADOR),
        ):
            self.memberships[role] = UserColaborador.objects.create(
                proyecto=self.project,
                usuario=user,
                rol=role,
                estado=UserColaborador.Estado.ACTIVO,
            )
        UserColaborador.objects.create(
            proyecto=self.project,
            usuario=self.pending,
            rol=UserColaborador.Rol.EDITOR,
            estado=UserColaborador.Estado.PENDIENTE,
        )


class ProjectRestPermissionTests(ProjectPermissionFixture, APITestCase):
    def setUp(self):
        self.create_fixture()
        self.detail_url = f"/api/modelado/proyectos/{self.project.id}/"
        self.export_url = f"/api/generador/proyectos/{self.project.id}/exportar-xml/"
        self.import_url = f"/api/generador/proyectos/{self.project.id}/importar-xml/"

    def request_as(self, user, method, url, data=None, format=None):
        self.client.force_authenticate(user=user)
        return getattr(self.client, method)(url, data=data, format=format)

    def test_owner_and_editor_can_update_project(self):
        for expected_revision, user in enumerate((self.owner, self.editor)):
            response = self.request_as(
                user, "patch", self.detail_url,
                {"descripcion": user.username, "expected_revision": expected_revision}, "json"
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_viewer_can_read_and_export_but_cannot_update_or_import(self):
        self.assertEqual(
            self.request_as(self.viewer, "get", self.detail_url).status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            self.request_as(self.viewer, "get", self.export_url).status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            self.request_as(self.viewer, "patch", self.detail_url, {"nombre": "No"}, "json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.request_as(self.viewer, "post", self.import_url, {}, "multipart").status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_only_owner_can_delete_project_or_manage_collaborators(self):
        collaborator_id = self.memberships[UserColaborador.Rol.VISUALIZADOR].id
        delete_collaborator_url = (
            f"/api/modelado/proyectos/{self.project.id}/colaboradores/{collaborator_id}/"
        )
        self.assertEqual(
            self.request_as(self.editor, "delete", delete_collaborator_url).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.request_as(self.editor, "delete", self.detail_url).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.request_as(self.owner, "delete", delete_collaborator_url).status_code,
            status.HTTP_200_OK,
        )

    def test_removed_and_external_users_have_no_access(self):
        for user in (self.removed, self.pending, self.outsider):
            self.assertEqual(
                self.request_as(user, "get", self.detail_url).status_code,
                status.HTTP_403_FORBIDDEN,
            )
            self.assertEqual(
                self.request_as(user, "get", self.export_url).status_code,
                status.HTTP_403_FORBIDDEN,
            )


class ProjectWebSocketPermissionTests(ProjectPermissionFixture, TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.create_fixture()

    async def open_socket(self, user):
        communicator = WebsocketCommunicator(PizarraConsumer.as_asgi(), "/ws/test/")
        communicator.scope["user"] = user
        communicator.scope["url_route"] = {"kwargs": {"proyecto_id": self.project.id}}
        connected, _ = await communicator.connect()
        if connected:
            first = await communicator.receive_json_from()
            self.assertEqual(first["accion"], "usuarios_conectados")
        return communicator, connected

    def test_owner_and_editor_can_mutate(self):
        async def scenario():
            for expected_revision, user in enumerate((self.owner, self.editor)):
                socket, connected = await self.open_socket(user)
                self.assertTrue(connected)
                await socket.send_json_to({
                    "accion": "renombrar_proyecto", "nombre": user.username,
                    "expected_revision": expected_revision,
                })
                response = await socket.receive_json_from()
                self.assertEqual(response["accion"], "proyecto_renombrado")
                await socket.disconnect()

        async_to_sync(scenario)()

    def test_viewer_can_connect_but_all_client_commands_are_read_only(self):
        async def scenario():
            socket, connected = await self.open_socket(self.viewer)
            self.assertTrue(connected)
            await socket.send_json_to({"accion": "crear_entidad", "entidad": {"id": -1}})
            response = await socket.receive_json_from()
            self.assertEqual(response["accion"], "permiso_denegado")
            await socket.disconnect()

        async_to_sync(scenario)()

    def test_unknown_commands_are_rejected(self):
        async def scenario():
            socket, connected = await self.open_socket(self.owner)
            self.assertTrue(connected)
            await socket.send_json_to({"accion": "comando_inventado"})
            response = await socket.receive_json_from()
            self.assertEqual(response["accion"], "comando_rechazado")
            await socket.disconnect()

        async_to_sync(scenario)()

    def test_removed_and_external_users_cannot_connect(self):
        async def scenario():
            for user in (self.removed, self.pending, self.outsider):
                socket, connected = await self.open_socket(user)
                self.assertFalse(connected)
                await socket.disconnect()

        async_to_sync(scenario)()

    def test_live_revocation_closes_socket_and_blocks_outbound_events(self):
        async def scenario():
            socket, connected = await self.open_socket(self.editor)
            self.assertTrue(connected)
            await database_sync_to_async(
                UserColaborador.objects.filter(
                    proyecto=self.project, usuario=self.editor
                ).delete
            )()
            await get_channel_layer().group_send(
                get_proyecto_group_name(self.project.id),
                {"type": "pizarra.evento", "evento": "entidad_creada", "data": {}},
            )
            response = await socket.receive_json_from()
            self.assertEqual(response["accion"], "access.revoked")
            close_event = await socket.receive_output()
            self.assertEqual(close_event["type"], "websocket.close")

        async_to_sync(scenario)()

    def test_access_revoked_event_closes_only_target_user(self):
        async def scenario():
            editor_socket, editor_connected = await self.open_socket(self.editor)
            owner_socket, owner_connected = await self.open_socket(self.owner)
            self.assertTrue(editor_connected and owner_connected)
            # Vaciar eventos de presencia producidos al abrir la segunda conexión.
            for socket in (editor_socket, owner_socket):
                while not await socket.receive_nothing(timeout=0.01):
                    await socket.receive_json_from()
            await get_channel_layer().group_send(
                get_proyecto_group_name(self.project.id),
                {
                    "type": "access.revoked",
                    "usuario_id": self.editor.id,
                    "proyecto_id": self.project.id,
                },
            )
            response = await editor_socket.receive_json_from()
            self.assertEqual(response["accion"], "access.revoked")
            self.assertTrue(await owner_socket.receive_nothing(timeout=0.05))
            await owner_socket.disconnect()

        async_to_sync(scenario)()

    def test_projects_use_isolated_channel_groups(self):
        other_project = Proyecto.objects.create(propietario=self.owner, nombre="Otro")

        async def scenario():
            socket, connected = await self.open_socket(self.editor)
            self.assertTrue(connected)
            await get_channel_layer().group_send(
                get_proyecto_group_name(other_project.id),
                {"type": "pizarra.evento", "evento": "entidad_creada", "data": {}},
            )
            self.assertTrue(await socket.receive_nothing(timeout=0.05))
            await socket.disconnect()

        async_to_sync(scenario)()
