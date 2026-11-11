import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from unittest.mock import patch
import zipfile

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from modelado.models import Atributo, Entidad, Operacion, Proyecto, Relacion


User = get_user_model()


class CrudGenerationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="crud-owner", password="test")
        self.project = Proyecto.objects.create(propietario=self.owner, nombre="CRUD")
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)
        self.url = f"/api/generador/proyectos/{self.project.id}/spring-boot/"
        self.payload = {
            "expected_revision": 0,
            "nombre_proyecto": "tienda",
            "paquete_base": "com.ejemplo.tienda",
            "opciones": {
                "modelo": True,
                "repositorio": True,
                "servicio": True,
                "controlador": True,
            },
        }

    def entity(self, name="Producto", key_type="long"):
        entity = Entidad.objects.create(
            proyecto=self.project,
            nombre=name,
            tipo_clasificador=Entidad.TipoClasificador.ENTIDAD_PERSISTENTE,
        )
        Atributo.objects.create(
            entidad=entity, nombre="id", tipo=key_type, es_clave=True,
            es_nulo=False, orden=1,
        )
        return entity

    def generate(self, payload=None):
        return self.client.post(self.url, payload or self.payload, format="json")

    @staticmethod
    def archive(response):
        return zipfile.ZipFile(io.BytesIO(response.content))

    def test_generates_complete_crud_with_accessors_http_contract_and_manifest(self):
        product = self.entity()
        Atributo.objects.create(
            entidad=product, nombre="nombre", tipo="string", es_nulo=False, orden=2
        )
        Atributo.objects.create(
            entidad=product, nombre="activo", tipo="boolean", es_nulo=True, orden=3
        )
        response = self.generate()
        self.assertEqual(response.status_code, 200)
        with self.archive(response) as archive:
            names = set(archive.namelist())
            prefix = "tienda/src/main/java/com/ejemplo/tienda"
            expected = {
                f"{prefix}/model/Producto.java",
                f"{prefix}/repository/ProductoRepository.java",
                f"{prefix}/service/ProductoService.java",
                f"{prefix}/controller/ProductoController.java",
                f"{prefix}/exception/ApiError.java",
                f"{prefix}/exception/GlobalExceptionHandler.java",
            }
            self.assertTrue(expected.issubset(names))
            model = archive.read(f"{prefix}/model/Producto.java").decode()
            repository = archive.read(f"{prefix}/repository/ProductoRepository.java").decode()
            service = archive.read(f"{prefix}/service/ProductoService.java").decode()
            controller = archive.read(f"{prefix}/controller/ProductoController.java").decode()
            pom = archive.read("tienda/pom.xml").decode()
            readme = archive.read("tienda/README.md").decode()
            manifest = json.loads(archive.read("tienda/nodoboard-generation.json"))

        self.assertIn("public Long getId()", model)
        self.assertIn("public void setId(Long id)", model)
        self.assertIn("public Boolean getActivo()", model)
        self.assertNotIn("isActivo", model)
        self.assertIn("JpaRepository<Producto, Long>", repository)
        self.assertIn("repository.existsById(entity.getId())", service)
        self.assertIn("@Transactional(readOnly = true)", service)
        self.assertIn("existing.setNombre(input.getNombre())", service)
        self.assertNotIn("existing.setId", service)
        self.assertIn('@RequestMapping("/api/producto")', controller)
        self.assertIn("HttpStatus.CREATED", controller)
        self.assertIn("ResponseEntity.noContent()", controller)
        self.assertNotIn("@PatchMapping", controller)
        self.assertNotIn("@Valid", controller)
        self.assertIn("spring-boot-starter-web", pom)
        self.assertIn("Capas CRUD de 7D", readme)
        self.assertEqual(manifest["generator_version"], "0.5.0")
        self.assertTrue(manifest["crud"]["atomic"])
        self.assertEqual(manifest["crud"]["endpoints"], ["/api/producto"])

    def test_repository_id_types_and_nonpersistent_class_exclusion(self):
        for index, key_type in enumerate(("string", "integer", "long"), start=1):
            self.entity(f"Entidad{index}", key_type)
        Entidad.objects.create(proyecto=self.project, nombre="Auxiliar")
        payload = {
            **self.payload,
            "opciones": {**self.payload["opciones"], "servicio": False, "controlador": False},
        }
        response = self.generate(payload)
        self.assertEqual(response.status_code, 200)
        with self.archive(response) as archive:
            combined = "\n".join(
                archive.read(name).decode()
                for name in archive.namelist()
                if "/repository/" in name
            )
            names = archive.namelist()
        for java_type in ("String", "Integer", "Long"):
            self.assertIn(f", {java_type}>", combined)
        self.assertFalse(any("AuxiliarRepository" in name for name in names))
        self.assertFalse(any("/service/" in name for name in names))

    def test_generates_four_layers_for_joined_inheritance(self):
        vehicle = self.entity("Vehiculo", key_type="string")
        vehicle.atributos.filter(nombre="id").update(nombre="placa")
        car = self.entity("Auto", key_type="integer")
        Atributo.objects.create(
            entidad=car, nombre="pasajeros", tipo="integer", es_nulo=False, orden=2,
        )
        Relacion.objects.create(
            proyecto=self.project, entidad_origen=car, entidad_destino=vehicle,
            tipo=Relacion.Tipo.HERENCIA,
        )

        response = self.generate()

        self.assertEqual(response.status_code, 200)
        with self.archive(response) as archive:
            names = set(archive.namelist())
            prefix = "tienda/src/main/java/com/ejemplo/tienda"
            parent = archive.read(f"{prefix}/model/Vehiculo.java").decode()
            child = archive.read(f"{prefix}/model/Auto.java").decode()
            repository = archive.read(f"{prefix}/repository/AutoRepository.java").decode()
        self.assertIn("@Inheritance(strategy = InheritanceType.JOINED)", parent)
        self.assertIn('@PrimaryKeyJoinColumn(name = "placa")', child)
        self.assertIn("public class Auto extends Vehiculo", child)
        self.assertIn("JpaRepository<Auto, String>", repository)
        self.assertIn(f"{prefix}/service/AutoService.java", names)
        self.assertIn(f"{prefix}/controller/AutoController.java", names)

    def test_controller_uses_portable_route_for_snake_case_entity(self):
        self.entity("compra_producto")

        response = self.generate()

        self.assertEqual(response.status_code, 200)
        with self.archive(response) as archive:
            controller = archive.read(
                "tienda/src/main/java/com/ejemplo/tienda/controller/"
                "compra_productoController.java"
            ).decode()
            manifest = json.loads(archive.read("tienda/nodoboard-generation.json"))
        self.assertIn('@RequestMapping("/api/compra-producto")', controller)
        self.assertIn("/api/compra-producto", manifest["crud"]["endpoints"])

    def test_repository_allows_relation_but_service_rejects_entire_archive(self):
        order = self.entity("Pedido")
        customer = self.entity("Cliente")
        Relacion.objects.create(
            proyecto=self.project, entidad_origen=order, entidad_destino=customer,
            tipo=Relacion.Tipo.ASOCIACION,
            cardinalidad_origen="*", cardinalidad_destino="1",
            rol_destino="cliente", navegable_destino=True,
        )
        repository_only = {
            **self.payload,
            "opciones": {**self.payload["opciones"], "servicio": False, "controlador": False},
        }
        response = self.generate(repository_only)
        self.assertEqual(response.status_code, 200)
        with self.archive(response) as archive:
            self.assertIn(
                "tienda/src/main/java/com/ejemplo/tienda/repository/PedidoRepository.java",
                archive.namelist(),
            )

        response = self.generate()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "CRUD_UNSUPPORTED_RELATION_PAYLOAD")
        self.assertNotEqual(response["Content-Type"], "application/zip")

    def test_mixed_model_is_rejected_atomically(self):
        self.entity("Simple")
        source = self.entity("Origen")
        target = self.entity("Destino")
        Relacion.objects.create(
            proyecto=self.project, entidad_origen=source, entidad_destino=target,
            tipo=Relacion.Tipo.ASOCIACION,
            cardinalidad_origen="1", cardinalidad_destino="1",
            rol_destino="destino", navegable_destino=True,
        )
        response = self.generate()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "CRUD_UNSUPPORTED_RELATION_PAYLOAD")

    def test_accessor_collision_is_structured(self):
        product = self.entity()
        Atributo.objects.create(
            entidad=product, nombre="nombre", tipo="string", es_nulo=False, orden=2
        )
        Operacion.objects.create(
            entidad=product, nombre="getNombre", tipo_retorno="string", orden=1
        )
        response = self.generate()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "CRUD_METHOD_NAME_COLLISION")
        self.assertEqual(
            response.data["details"]["diagnosticos"][0]["objetivo"]["metodo"],
            "getNombre",
        )

    def test_no_persistent_entity_and_invalid_dependencies_are_rejected(self):
        Entidad.objects.create(proyecto=self.project, nombre="Normal")
        response = self.generate()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "CRUD_NO_ELIGIBLE_ENTITIES")

        invalid = {
            **self.payload,
            "opciones": {
                "modelo": True,
                "repositorio": False,
                "servicio": True,
                "controlador": False,
            },
        }
        response = self.generate(invalid)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "CRUD_INVALID_OPTION_COMBINATION")

    def test_crud_entity_limit_is_enforced_before_rendering(self):
        self.entity()
        with patch("generador.services.spring_contract.MAX_CRUD_ENTITIES", 0):
            response = self.generate()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "generation_limit_exceeded")
        self.assertEqual(response.data["details"]["limite"], "entidades_crud")

    def test_generation_is_deterministic_and_read_only(self):
        self.entity()
        first = self.generate()
        second = self.generate()
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.content, second.content)
        self.project.refresh_from_db()
        self.assertEqual(self.project.revision, 0)

    def test_optional_maven_offline_compile(self):
        if os.environ.get("NODOBOARD_MAVEN_CRUD_TEST") != "1":
            self.skipTest("Compilacion Maven CRUD opcional no solicitada")
        maven = shutil.which("mvn")
        if not maven:
            self.skipTest("Maven no esta disponible")
        product = self.entity()
        Atributo.objects.create(
            entidad=product, nombre="nombre", tipo="string", es_nulo=False, orden=2
        )
        response = self.generate()
        self.assertEqual(response.status_code, 200)
        with tempfile.TemporaryDirectory(prefix="nodoboard-crud-maven-") as temporary:
            root = Path(temporary)
            user_home = Path(os.environ.get("USERPROFILE", Path.home()))
            local_repository = user_home / ".m2" / "repository"
            with self.archive(response) as archive:
                archive.extractall(root)
            result = subprocess.run(
                [
                    maven,
                    "-o",
                    "-q",
                    f"-Dmaven.repo.local={local_repository}",
                    "-DskipTests",
                    "compile",
                ],
                cwd=root / "tienda", capture_output=True, text=True, timeout=120,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
