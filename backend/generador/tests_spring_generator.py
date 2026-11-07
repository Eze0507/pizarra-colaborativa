import io
import json
import zipfile
from unittest.mock import patch
from xml.etree import ElementTree as ET

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from modelado.models import Entidad, Proyecto, Relacion
from usuario.models import UserColaborador

from .services.spring_contract import capture_generation_contract
from .services.spring_generator import (
    GENERATOR_VERSION,
    SPRING_BOOT_VERSION,
    build_coordinates,
)


User = get_user_model()


class SpringBootGenerationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="spring-owner", password="test")
        self.editor = User.objects.create_user(username="spring-editor", password="test")
        self.viewer = User.objects.create_user(username="spring-viewer", password="test")
        self.pending = User.objects.create_user(username="spring-pending", password="test")
        self.removed = User.objects.create_user(username="spring-removed", password="test")
        self.outsider = User.objects.create_user(username="spring-outsider", password="test")
        self.project = Proyecto.objects.create(propietario=self.owner, nombre="Spring")
        for user, role, state in (
            (self.editor, UserColaborador.Rol.EDITOR, UserColaborador.Estado.ACTIVO),
            (self.viewer, UserColaborador.Rol.VISUALIZADOR, UserColaborador.Estado.ACTIVO),
            (self.pending, UserColaborador.Rol.EDITOR, UserColaborador.Estado.PENDIENTE),
        ):
            UserColaborador.objects.create(
                proyecto=self.project, usuario=user, rol=role, estado=state
            )
        removed_membership = UserColaborador.objects.create(
            proyecto=self.project,
            usuario=self.removed,
            rol=UserColaborador.Rol.EDITOR,
            estado=UserColaborador.Estado.ACTIVO,
        )
        removed_membership.delete()
        self.url = f"/api/generador/proyectos/{self.project.id}/spring-boot/"
        self.client = APIClient()
        self.payload = {
            "expected_revision": 0,
            "nombre_proyecto": "tienda",
            "paquete_base": "com.ejemplo.tienda",
            "opciones": {
                "modelo": False,
                "repositorio": False,
                "servicio": False,
                "controlador": False,
            },
        }

    def post_as(self, user, payload=None):
        self.client.force_authenticate(user=user)
        return self.client.post(self.url, payload or self.payload, format="json")

    @staticmethod
    def read_zip(response):
        return zipfile.ZipFile(io.BytesIO(response.content))

    def test_export_permissions_owner_editor_and_viewer(self):
        for user in (self.owner, self.editor, self.viewer):
            with self.subTest(user=user.username):
                response = self.post_as(user)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response["Content-Type"], "application/zip")

    def test_rejects_unauthenticated_pending_removed_and_external(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.post(self.url, self.payload, format="json").status_code, 401)
        for user in (self.pending, self.removed, self.outsider):
            with self.subTest(user=user.username):
                self.assertEqual(self.post_as(user).status_code, 403)

    def test_revision_contract_and_read_only_generation(self):
        missing = dict(self.payload)
        missing.pop("expected_revision")
        self.assertEqual(self.post_as(self.owner, missing).status_code, 400)
        for invalid in (True, -1, "0", 1.5):
            payload = {**self.payload, "expected_revision": invalid}
            with self.subTest(value=invalid):
                self.assertEqual(self.post_as(self.owner, payload).status_code, 400)
        stale = self.post_as(self.owner, {**self.payload, "expected_revision": 1})
        self.assertEqual(stale.status_code, 409)
        self.assertEqual((stale.data["code"], stale.data["current_revision"]), ("stale_revision", 0))

        before = (self.project.revision, self.project.datos_diagrama)
        with patch("modelado.realtime.notificar_evento_proyecto_sync") as notify:
            accepted = self.post_as(self.owner)
        self.assertEqual(accepted.status_code, 200)
        notify.assert_not_called()
        self.project.refresh_from_db()
        self.assertEqual((self.project.revision, self.project.datos_diagrama), before)

    def test_strict_names_packages_and_options(self):
        invalid_cases = (
            ("nombre_proyecto", "", "invalid_generation_request"),
            ("nombre_proyecto", "../tienda", "invalid_generation_request"),
            ("nombre_proyecto", "CON", "invalid_generation_request"),
            ("nombre_proyecto", "Tienda", "invalid_generation_request"),
            ("paquete_base", "com.class.tienda", "invalid_generation_request"),
            ("paquete_base", "com/ejemplo", "invalid_generation_request"),
        )
        for field, value, code in invalid_cases:
            with self.subTest(field=field, value=value):
                response = self.post_as(self.owner, {**self.payload, field: value})
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.data["code"], code)

        unknown = {**self.payload, "opciones": {**self.payload["opciones"], "dto": False}}
        self.assertEqual(self.post_as(self.owner, unknown).status_code, 400)
        enabled = {**self.payload, "opciones": {**self.payload["opciones"], "repositorio": True}}
        unsupported = self.post_as(self.owner, enabled)
        self.assertEqual(unsupported.status_code, 400)
        self.assertEqual(unsupported.data["code"], "CRUD_INVALID_OPTION_COMBINATION")
        non_boolean = {**self.payload, "opciones": {**self.payload["opciones"], "modelo": "false"}}
        self.assertEqual(self.post_as(self.owner, non_boolean).status_code, 400)
        boundary = self.post_as(self.owner, {**self.payload, "nombre_proyecto": "a" * 64})
        self.assertEqual(boundary.status_code, 200)
        too_long = self.post_as(self.owner, {**self.payload, "nombre_proyecto": "a" * 65})
        self.assertEqual(too_long.status_code, 400)

    def test_uml_and_java_errors_block_but_jpa_only_errors_do_not(self):
        invalid_uml = Entidad.objects.create(proyecto=self.project, nombre="")
        response = self.post_as(self.owner)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.data["details"]["perfil"], "uml")
        invalid_uml.delete()

        invalid_java = Entidad.objects.create(proyecto=self.project, nombre="class")
        response = self.post_as(self.owner)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.data["details"]["perfil"], "java")
        invalid_java.delete()

        Entidad.objects.create(
            proyecto=self.project,
            nombre="Pedido",
            tipo_clasificador=Entidad.TipoClasificador.ENTIDAD_PERSISTENTE,
        )
        response = self.post_as(self.owner)
        self.assertEqual(response.status_code, 200)
        with self.read_zip(response) as archive:
            manifest = json.loads(archive.read("tienda/nodoboard-generation.json"))
        self.assertTrue(manifest["validation"]["preparacion"]["maven_base"])
        self.assertFalse(manifest["validation"]["preparacion"]["jpa"])
        self.assertTrue(
            any(
                item["codigo"] == "JPA_ENTITY_WITHOUT_ID"
                for item in manifest["validation"]["perfiles"]["jpa"]["hallazgos"]
            )
        )

    def test_capture_is_immutable_and_profiles_share_revision(self):
        capture = capture_generation_contract(
            project_id=self.project.id, expected_revision=0, user=self.owner
        )
        with self.assertRaises(TypeError):
            capture.model["project_id"] = 99
        with self.assertRaises(TypeError):
            capture.validation["revision_validada"] = 99
        self.assertEqual(capture.revision, 0)
        for profile in ("uml", "java", "jpa"):
            self.assertEqual(capture.validation["perfiles"][profile]["revision"], 0)
            self.assertEqual(
                capture.validation["perfiles"][profile]["origen"],
                "captura_autoritativa",
            )

    def test_zip_structure_http_contract_and_no_forbidden_layers(self):
        response = self.post_as(self.owner)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Disposition"], 'attachment; filename="tienda.zip"')
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(int(response["Content-Length"]), len(response.content))
        with self.read_zip(response) as archive:
            names = archive.namelist()
            self.assertEqual(names, sorted(names))
            self.assertEqual(len(names), len(set(names)))
            self.assertFalse(any(name.startswith(("/", "\\")) or ".." in name.split("/") for name in names))
            expected = {
                "tienda/pom.xml",
                "tienda/README.md",
                "tienda/nodoboard-generation.json",
                "tienda/src/main/java/com/ejemplo/tienda/TiendaApplication.java",
                "tienda/src/main/resources/application.properties",
                "tienda/src/test/java/com/ejemplo/tienda/TiendaApplicationTests.java",
            }
            self.assertEqual(set(names), expected)
            pom = archive.read("tienda/pom.xml").decode()
            ET.fromstring(pom)
            self.assertIn(f"<version>{SPRING_BOOT_VERSION}</version>", pom)
            self.assertNotIn("data-jpa", pom)
            self.assertNotIn("postgresql", pom)
            self.assertFalse(any("mvnw" in name or ".env" in name for name in names))
            combined = b"".join(archive.read(name) for name in names).lower()
            self.assertNotIn(b"password", combined)
            manifest = json.loads(archive.read("tienda/nodoboard-generation.json"))
            self.assertEqual(manifest["generator_version"], GENERATOR_VERSION)
            self.assertEqual(manifest["uml"]["revision"], 0)

    def test_generation_is_binary_deterministic(self):
        first = self.post_as(self.owner)
        second = self.post_as(self.owner)
        self.assertEqual(first.content, second.content)
        with self.read_zip(first) as archive:
            self.assertTrue(all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in archive.infolist()))

    def test_validation_warnings_are_in_manifest(self):
        source = Entidad.objects.create(proyecto=self.project, nombre="Origen")
        target = Entidad.objects.create(proyecto=self.project, nombre="Destino")
        Relacion.objects.create(
            proyecto=self.project,
            entidad_origen=source,
            entidad_destino=target,
            cardinalidad_origen="",
            cardinalidad_destino="",
        )
        response = self.post_as(self.owner)
        self.assertEqual(response.status_code, 200)
        with self.read_zip(response) as archive:
            manifest = json.loads(archive.read("tienda/nodoboard-generation.json"))
        findings = manifest["validation"]["perfiles"]["java"]["hallazgos"]
        self.assertTrue(any(item["codigo"] == "UML_MULTIPLICITY_UNSPECIFIED" for item in findings))

    def test_limits_reject_without_partial_zip(self):
        Entidad.objects.create(proyecto=self.project, nombre="Uno")
        with patch("generador.services.spring_contract.MAX_CLASSIFIERS", 0):
            response = self.post_as(self.owner)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "generation_limit_exceeded")
        self.assertNotEqual(response["Content-Type"], "application/zip")

        with patch("generador.services.spring_generator.MAX_GENERATED_FILES", 5):
            response = self.post_as(self.owner)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "generation_limit_exceeded")

    def test_coordinates_are_explicit_and_deterministic(self):
        first = build_coordinates("tienda-online", "com.ejemplo.tienda")
        second = build_coordinates("tienda-online", "com.ejemplo.tienda")
        self.assertEqual(first, second)
        self.assertEqual(first.group_id, "com.ejemplo.tienda")
        self.assertEqual(first.artifact_id, "tienda-online")
        self.assertEqual(first.main_class, "TiendaOnlineApplication")
