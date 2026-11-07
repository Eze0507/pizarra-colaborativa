import io
import json
import zipfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from modelado.models import Atributo, Entidad, Proyecto


User = get_user_model()


class PostgreSqlGenerationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="postgres-owner", password="test")
        self.project = Proyecto.objects.create(propietario=self.owner, nombre="PostgreSQL")
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)
        self.url = f"/api/generador/proyectos/{self.project.id}/spring-boot/"
        self.payload = {
            "expected_revision": 0,
            "nombre_proyecto": "tienda",
            "paquete_base": "com.ejemplo.tienda",
            "opciones": {
                "modelo": True,
                "repositorio": False,
                "servicio": False,
                "controlador": False,
            },
        }

    def generate(self, payload=None):
        return self.client.post(self.url, payload or self.payload, format="json")

    @staticmethod
    def archive(response):
        return zipfile.ZipFile(io.BytesIO(response.content))

    def test_jpa_project_has_runtime_driver_fail_closed_properties_and_metadata(self):
        entity = Entidad.objects.create(
            proyecto=self.project,
            nombre="Producto",
            tipo_clasificador=Entidad.TipoClasificador.ENTIDAD_PERSISTENTE,
        )
        Atributo.objects.create(
            entidad=entity, nombre="id", tipo="long", es_clave=True,
            es_nulo=False, orden=1,
        )
        response = self.generate()
        self.assertEqual(response.status_code, 200)
        with self.archive(response) as archive:
            pom = archive.read("tienda/pom.xml").decode()
            properties = archive.read(
                "tienda/src/main/resources/application.properties"
            ).decode()
            readme = archive.read("tienda/README.md").decode()
            manifest = json.loads(archive.read("tienda/nodoboard-generation.json"))

        self.assertEqual(pom.count("<artifactId>postgresql</artifactId>"), 1)
        self.assertIn("<scope>runtime</scope>", pom)
        self.assertNotIn("<artifactId>h2</artifactId>", pom)
        self.assertEqual(properties.count("spring.application.name="), 1)
        expected = (
            "spring.application.name=tienda\n"
            "spring.datasource.url=${DB_URL}\n"
            "spring.datasource.username=${DB_USERNAME}\n"
            "spring.datasource.password=${DB_PASSWORD}\n"
            "spring.datasource.driver-class-name=org.postgresql.Driver\n"
            "spring.jpa.hibernate.ddl-auto=${DB_DDL_AUTO:validate}\n"
            "spring.jpa.open-in-view=false\n"
        )
        self.assertEqual(properties, expected)
        self.assertNotIn("jdbc:postgresql://", properties)
        self.assertNotIn("create-drop", properties)
        self.assertNotIn("ddl-auto=update", properties)
        self.assertIn("DB_DDL_AUTO", readme)
        self.assertIn("no crea la base, tablas ni migraciones", readme)
        self.assertIn("no incluye Spring\nSecurity", readme)
        self.assertEqual(manifest["generator_version"], "0.5.0")
        self.assertEqual(manifest["postgresql"]["scope"], "runtime")
        self.assertEqual(
            manifest["postgresql"]["required_environment"],
            ["DB_URL", "DB_USERNAME", "DB_PASSWORD"],
        )
        self.assertFalse(manifest["postgresql"]["real_database_verified"])
        self.assertFalse(manifest["postgresql"]["persistence_verified"])

    def test_non_jpa_projects_do_not_include_postgresql(self):
        Entidad.objects.create(proyecto=self.project, nombre="Auxiliar")
        response = self.generate()
        self.assertEqual(response.status_code, 200)
        with self.archive(response) as archive:
            pom = archive.read("tienda/pom.xml").decode()
            properties = archive.read(
                "tienda/src/main/resources/application.properties"
            ).decode()
            manifest = json.loads(archive.read("tienda/nodoboard-generation.json"))
        self.assertNotIn("postgresql", pom)
        self.assertEqual(properties, "spring.application.name=tienda\n")
        self.assertIsNone(manifest["postgresql"])

    def test_postgresql_generation_is_deterministic_and_read_only(self):
        entity = Entidad.objects.create(
            proyecto=self.project,
            nombre="Determinista",
            tipo_clasificador=Entidad.TipoClasificador.ENTIDAD_PERSISTENTE,
        )
        Atributo.objects.create(
            entidad=entity, nombre="id", tipo="string", es_clave=True,
            es_nulo=False, orden=1,
        )
        first = self.generate()
        second = self.generate()
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.content, second.content)
        self.project.refresh_from_db()
        self.assertEqual(self.project.revision, 0)

    def test_download_headers_are_exposed_without_wildcard(self):
        self.assertIn("Content-Disposition", settings.CORS_EXPOSE_HEADERS)
        self.assertIn("Content-Length", settings.CORS_EXPOSE_HEADERS)
        self.assertNotIn("*", settings.CORS_EXPOSE_HEADERS)
        response = self.client.post(
            self.url,
            self.payload,
            format="json",
            HTTP_ORIGIN="http://localhost:4200",
        )
        exposed = response.headers.get("Access-Control-Expose-Headers", "")
        self.assertIn("Content-Disposition", exposed)
        self.assertIn("Content-Length", exposed)
