import io
import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from modelado.models import (
    Atributo,
    Entidad,
    Operacion,
    ParametroOperacion,
    Proyecto,
    Relacion,
    VisibilidadUML,
)

from .services.java_model_generator import JavaGenerationError, render_java_model


User = get_user_model()


class JavaModelGenerationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="java-owner", password="test")
        self.project = Proyecto.objects.create(propietario=self.owner, nombre="Java")
        self.url = f"/api/generador/proyectos/{self.project.id}/spring-boot/"
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)
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

    def generate(self):
        return self.client.post(self.url, self.payload, format="json")

    @staticmethod
    def archive(response):
        return zipfile.ZipFile(io.BytesIO(response.content))

    def test_generates_classifiers_attributes_types_defaults_and_operations(self):
        customer = Entidad.objects.create(proyecto=self.project, nombre="Cliente")
        product = Entidad.objects.create(
            proyecto=self.project,
            nombre="Producto",
            abstracto=True,
        )
        attributes = [
            Atributo.objects.create(
                entidad=product, nombre="nombre", tipo="string",
                visibilidad=VisibilidadUML.PRIVATE,
                valor_predeterminado='Pan "especial"\nnuevo', orden=1,
            ),
            Atributo.objects.create(
                entidad=product, nombre="cantidad", tipo="integer",
                visibilidad=VisibilidadUML.PUBLIC, es_estatico=True,
                valor_predeterminado="2", orden=2,
            ),
            Atributo.objects.create(
                entidad=product, nombre="codigo", tipo="long",
                valor_predeterminado="25", orden=3,
            ),
            Atributo.objects.create(
                entidad=product, nombre="precio", tipo="double",
                valor_predeterminado="12.5", orden=4,
            ),
            Atributo.objects.create(
                entidad=product, nombre="activo", tipo="boolean",
                valor_predeterminado="true", orden=5,
            ),
            Atributo.objects.create(
                entidad=product, nombre="fecha", tipo="date",
                valor_predeterminado="2026-11-05", orden=6,
            ),
            Atributo.objects.create(
                entidad=product, nombre="cliente", tipo="Cliente",
                tipo_referencia=customer, es_nulo=True,
                valor_predeterminado="null", orden=7,
            ),
        ]
        operation = Operacion.objects.create(
            entidad=product, nombre="calcular", tipo_retorno="double",
            visibilidad=VisibilidadUML.PROTECTED, es_abstracto=True, orden=1,
        )
        ParametroOperacion.objects.create(
            operacion=operation, nombre="desde", tipo="date", orden=1
        )
        ParametroOperacion.objects.create(
            operacion=operation, nombre="cliente", tipo="Cliente",
            tipo_referencia=customer, orden=2,
        )
        static_operation = Operacion.objects.create(
            entidad=product, nombre="reiniciar", tipo_retorno="void",
            visibilidad=VisibilidadUML.PACKAGE, es_estatico=True, orden=2,
        )

        response = self.generate()
        self.assertEqual(response.status_code, 200)
        with self.archive(response) as archive:
            source = archive.read(
                "tienda/src/main/java/com/ejemplo/tienda/model/Producto.java"
            ).decode()
            manifest = json.loads(archive.read("tienda/nodoboard-generation.json"))
            self._compile_model_sources(archive)
        self.assertIn("public abstract class Producto", source)
        self.assertIn('private String nombre = "Pan \\"especial\\"\\nnuevo";', source)
        self.assertIn("public static Integer cantidad = 2;", source)
        self.assertIn("private Long codigo = 25L;", source)
        self.assertIn("private Double precio = 12.5d;", source)
        self.assertIn("private Boolean activo = true;", source)
        self.assertIn("import java.time.LocalDate;", source)
        self.assertIn("private LocalDate fecha = LocalDate.of(2026, 11, 5);", source)
        self.assertIn("private Cliente cliente = null;", source)
        self.assertIn("protected abstract Double calcular(LocalDate desde, Cliente cliente);", source)
        self.assertIn("static void reiniciar()", source)
        model = manifest["java_model"]
        product_metadata = next(item for item in model["clasificadores"] if item["id"] == product.id)
        self.assertFalse(product_metadata["persistente_sin_jpa"])
        self.assertEqual(product_metadata["atributos"], [item.id for item in attributes])
        self.assertEqual(
            product_metadata["detalle_atributos"][0],
            {"id": attributes[0].id, "orden": 1, "es_clave": False, "anulable": False},
        )
        self.assertEqual(product_metadata["operaciones"], [operation.id, static_operation.id])

    def test_interface_implementation_generates_traced_stub_and_compiles(self):
        payable = Entidad.objects.create(
            proyecto=self.project, nombre="Pagable",
            tipo_clasificador=Entidad.TipoClasificador.INTERFAZ,
        )
        pay = Operacion.objects.create(
            entidad=payable, nombre="pagar", tipo_retorno="boolean",
            visibilidad=VisibilidadUML.PUBLIC,
        )
        ParametroOperacion.objects.create(
            operacion=pay, nombre="monto", tipo="double", orden=1
        )
        card = Entidad.objects.create(proyecto=self.project, nombre="PagoTarjeta")
        Relacion.objects.create(
            proyecto=self.project, entidad_origen=card, entidad_destino=payable,
            tipo=Relacion.Tipo.IMPLEMENTACION,
        )

        response = self.generate()
        self.assertEqual(response.status_code, 200)
        with self.archive(response) as archive:
            card_source = archive.read(
                "tienda/src/main/java/com/ejemplo/tienda/model/PagoTarjeta.java"
            ).decode()
            interface_source = archive.read(
                "tienda/src/main/java/com/ejemplo/tienda/model/Pagable.java"
            ).decode()
            manifest = json.loads(archive.read("tienda/nodoboard-generation.json"))
            self.assertIn("implements Pagable", card_source)
            self.assertIn("@Override", card_source)
            self.assertIn("public Boolean pagar(Double monto)", card_source)
            self.assertIn("Boolean pagar(Double monto);", interface_source)
            metadata = next(
                item for item in manifest["java_model"]["clasificadores"]
                if item["id"] == card.id
            )
            self.assertEqual(metadata["stubs_generados"][0]["operacion_origen_id"], pay.id)
            self._compile_model_sources(archive)

    def test_class_and_interface_inheritance_compile(self):
        base_interface = Entidad.objects.create(
            proyecto=self.project, nombre="Base",
            tipo_clasificador=Entidad.TipoClasificador.INTERFAZ,
        )
        child_interface = Entidad.objects.create(
            proyecto=self.project, nombre="Avanzado",
            tipo_clasificador=Entidad.TipoClasificador.INTERFAZ,
        )
        Operacion.objects.create(
            entidad=base_interface, nombre="auditar", tipo_retorno="void"
        )
        Relacion.objects.create(
            proyecto=self.project, entidad_origen=child_interface,
            entidad_destino=base_interface, tipo=Relacion.Tipo.HERENCIA,
        )
        person = Entidad.objects.create(
            proyecto=self.project, nombre="Persona", abstracto=True
        )
        abstract_operation = Operacion.objects.create(
            entidad=person, nombre="nombreCompleto", tipo_retorno="string",
            visibilidad=VisibilidadUML.PROTECTED, es_abstracto=True,
        )
        employee = Entidad.objects.create(proyecto=self.project, nombre="Empleado")
        Relacion.objects.create(
            proyecto=self.project, entidad_origen=employee,
            entidad_destino=person, tipo=Relacion.Tipo.HERENCIA,
        )
        Relacion.objects.create(
            proyecto=self.project, entidad_origen=employee,
            entidad_destino=child_interface, tipo=Relacion.Tipo.IMPLEMENTACION,
        )
        response = self.generate()
        self.assertEqual(response.status_code, 200)
        with self.archive(response) as archive:
            employee_source = archive.read(
                "tienda/src/main/java/com/ejemplo/tienda/model/Empleado.java"
            ).decode()
            child_source = archive.read(
                "tienda/src/main/java/com/ejemplo/tienda/model/Avanzado.java"
            ).decode()
            self.assertIn("extends Persona implements Avanzado", employee_source)
            self.assertIn("protected String nombreCompleto()", employee_source)
            self.assertIn("public void auditar()", employee_source)
            self.assertIn("interface Avanzado extends Base", child_source)
            self.assertEqual(employee_source.count("nombreCompleto("), 1)
            self._compile_model_sources(archive)

    def test_compiles_simple_references_abstraction_and_method_combinations(self):
        customer = Entidad.objects.create(proyecto=self.project, nombre="Cliente")
        product = Entidad.objects.create(proyecto=self.project, nombre="Producto")
        Atributo.objects.create(entidad=product, nombre="nombre", tipo="string", orden=1)
        Atributo.objects.create(entidad=product, nombre="precio", tipo="double", orden=2)
        order = Entidad.objects.create(proyecto=self.project, nombre="Pedido")
        Atributo.objects.create(
            entidad=order, nombre="cliente", tipo="Cliente",
            tipo_referencia=customer, orden=1,
        )
        figure = Entidad.objects.create(
            proyecto=self.project, nombre="Figura", abstracto=True
        )
        Operacion.objects.create(
            entidad=figure, nombre="calcularArea", tipo_retorno="double",
            visibilidad=VisibilidadUML.PROTECTED, es_abstracto=True,
        )
        circle = Entidad.objects.create(proyecto=self.project, nombre="Circulo")
        Relacion.objects.create(
            proyecto=self.project, entidad_origen=circle, entidad_destino=figure,
            tipo=Relacion.Tipo.HERENCIA,
        )
        utility = Entidad.objects.create(proyecto=self.project, nombre="Utilidad")
        Operacion.objects.create(
            entidad=utility, nombre="convertir", tipo_retorno="void",
            visibilidad=VisibilidadUML.PACKAGE, es_estatico=True, orden=1,
        )
        overloaded = Operacion.objects.create(
            entidad=utility, nombre="convertir", tipo_retorno="string",
            visibilidad=VisibilidadUML.PRIVATE, orden=2,
        )
        ParametroOperacion.objects.create(
            operacion=overloaded, nombre="cantidad", tipo="integer", orden=1
        )
        ParametroOperacion.objects.create(
            operacion=overloaded, nombre="activo", tipo="boolean", orden=2
        )

        response = self.generate()
        self.assertEqual(response.status_code, 200)
        with self.archive(response) as archive:
            circle_source = archive.read(
                "tienda/src/main/java/com/ejemplo/tienda/model/Circulo.java"
            ).decode()
            utility_source = archive.read(
                "tienda/src/main/java/com/ejemplo/tienda/model/Utilidad.java"
            ).decode()
            self.assertIn("extends Figura", circle_source)
            self.assertIn("protected Double calcularArea()", circle_source)
            self.assertIn("static void convertir()", utility_source)
            self.assertIn(
                "private String convertir(Integer cantidad, Boolean activo)",
                utility_source,
            )
            self._compile_model_sources(archive)

    def test_multiple_interfaces_generate_one_stub_per_contract_and_compile(self):
        payable = Entidad.objects.create(
            proyecto=self.project, nombre="Pagable",
            tipo_clasificador=Entidad.TipoClasificador.INTERFAZ,
        )
        auditable = Entidad.objects.create(
            proyecto=self.project, nombre="Auditable",
            tipo_clasificador=Entidad.TipoClasificador.INTERFAZ,
        )
        Operacion.objects.create(entidad=payable, nombre="pagar", tipo_retorno="void")
        Operacion.objects.create(entidad=auditable, nombre="auditar", tipo_retorno="void")
        card = Entidad.objects.create(proyecto=self.project, nombre="PagoTarjeta")
        Relacion.objects.create(
            proyecto=self.project, entidad_origen=card, entidad_destino=payable,
            tipo=Relacion.Tipo.IMPLEMENTACION,
        )
        Relacion.objects.create(
            proyecto=self.project, entidad_origen=card, entidad_destino=auditable,
            tipo=Relacion.Tipo.IMPLEMENTACION,
        )
        response = self.generate()
        self.assertEqual(response.status_code, 200)
        with self.archive(response) as archive:
            source = archive.read(
                "tienda/src/main/java/com/ejemplo/tienda/model/PagoTarjeta.java"
            ).decode()
            self.assertIn("implements Pagable, Auditable", source)
            self.assertEqual(source.count("@Override"), 2)
            self._compile_model_sources(archive)

    def test_existing_implementation_uses_override_without_duplicate(self):
        contract = Entidad.objects.create(
            proyecto=self.project, nombre="Ejecutable",
            tipo_clasificador=Entidad.TipoClasificador.INTERFAZ,
        )
        Operacion.objects.create(entidad=contract, nombre="ejecutar", tipo_retorno="void")
        implementation = Entidad.objects.create(proyecto=self.project, nombre="Tarea")
        Operacion.objects.create(
            entidad=implementation, nombre="ejecutar", tipo_retorno="void",
            visibilidad=VisibilidadUML.PUBLIC,
        )
        Relacion.objects.create(
            proyecto=self.project, entidad_origen=implementation,
            entidad_destino=contract, tipo=Relacion.Tipo.IMPLEMENTACION,
        )
        response = self.generate()
        self.assertEqual(response.status_code, 200)
        with self.archive(response) as archive:
            source = archive.read(
                "tienda/src/main/java/com/ejemplo/tienda/model/Tarea.java"
            ).decode()
        self.assertEqual(source.count("void ejecutar("), 1)
        self.assertEqual(source.count("@Override"), 1)

    def test_concrete_override_is_traced_and_incompatible_override_is_rejected(self):
        parent = Entidad.objects.create(proyecto=self.project, nombre="BaseConcreta")
        Operacion.objects.create(
            entidad=parent, nombre="calcular", tipo_retorno="integer",
            visibilidad=VisibilidadUML.PROTECTED,
        )
        child = Entidad.objects.create(proyecto=self.project, nombre="Derivada")
        operation = Operacion.objects.create(
            entidad=child, nombre="calcular", tipo_retorno="integer",
            visibilidad=VisibilidadUML.PUBLIC,
        )
        Relacion.objects.create(
            proyecto=self.project, entidad_origen=child, entidad_destino=parent,
            tipo=Relacion.Tipo.HERENCIA,
        )
        response = self.generate()
        self.assertEqual(response.status_code, 200)
        with self.archive(response) as archive:
            source = archive.read(
                "tienda/src/main/java/com/ejemplo/tienda/model/Derivada.java"
            ).decode()
            self.assertEqual(source.count("@Override"), 1)
            self._compile_model_sources(archive)

        operation.tipo_retorno = "string"
        operation.save(update_fields=["tipo_retorno"])
        response = self.generate()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "java_generation_failed")
        self.assertEqual(
            response.data["details"]["diagnosticos"][0]["codigo"],
            "JAVA_INCOMPATIBLE_INHERITANCE",
        )

    def test_incompatible_multiple_interface_contracts_are_rejected(self):
        first = Entidad.objects.create(
            proyecto=self.project, nombre="Primera",
            tipo_clasificador=Entidad.TipoClasificador.INTERFAZ,
        )
        second = Entidad.objects.create(
            proyecto=self.project, nombre="Segunda",
            tipo_clasificador=Entidad.TipoClasificador.INTERFAZ,
        )
        combined = Entidad.objects.create(
            proyecto=self.project, nombre="Combinada",
            tipo_clasificador=Entidad.TipoClasificador.INTERFAZ,
        )
        Operacion.objects.create(entidad=first, nombre="valor", tipo_retorno="integer")
        Operacion.objects.create(entidad=second, nombre="valor", tipo_retorno="string")
        for parent in (first, second):
            Relacion.objects.create(
                proyecto=self.project, entidad_origen=combined,
                entidad_destino=parent, tipo=Relacion.Tipo.HERENCIA,
            )
        response = self.generate()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "java_generation_failed")
        self.assertEqual(
            response.data["details"]["diagnosticos"][0]["codigo"],
            "JAVA_INCOMPATIBLE_INHERITANCE",
        )

    def test_rejects_unsupported_interface_members_and_invalid_defaults(self):
        interface = Entidad.objects.create(
            proyecto=self.project, nombre="Invalida",
            tipo_clasificador=Entidad.TipoClasificador.INTERFAZ,
        )
        Atributo.objects.create(entidad=interface, nombre="estado", tipo="string")
        response = self.generate()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "java_generation_failed")
        self.assertEqual(
            response.data["details"]["diagnosticos"][0]["codigo"],
            "JAVA_UNSUPPORTED_INTERFACE_MEMBER",
        )
        interface.delete()

        entity = Entidad.objects.create(proyecto=self.project, nombre="Valor")
        Atributo.objects.create(
            entidad=entity, nombre="cantidad", tipo="integer",
            valor_predeterminado="1; System.exit(0)",
        )
        response = self.generate()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["details"]["diagnosticos"][0]["codigo"],
            "JAVA_INVALID_DEFAULT_VALUE",
        )

    def test_rejects_case_collisions_and_incompatible_interface_method(self):
        first = Entidad.objects.create(proyecto=self.project, nombre="Cliente")
        second = Entidad.objects.create(proyecto=self.project, nombre="cliente")
        response = self.generate()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "java_generation_failed")
        first.delete(); second.delete()

        contract = Entidad.objects.create(
            proyecto=self.project, nombre="Contrato",
            tipo_clasificador=Entidad.TipoClasificador.INTERFAZ,
        )
        Operacion.objects.create(entidad=contract, nombre="hacer", tipo_retorno="void")
        implementation = Entidad.objects.create(proyecto=self.project, nombre="Implementacion")
        Operacion.objects.create(
            entidad=implementation, nombre="hacer", tipo_retorno="void",
            visibilidad=VisibilidadUML.PRIVATE,
        )
        Relacion.objects.create(
            proyecto=self.project, entidad_origen=implementation,
            entidad_destino=contract, tipo=Relacion.Tipo.IMPLEMENTACION,
        )
        response = self.generate()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["details"]["diagnosticos"][0]["codigo"],
            "JAVA_INCOMPATIBLE_INHERITANCE",
        )

    def test_associations_remain_manifest_metadata_without_java_fields(self):
        source = Entidad.objects.create(proyecto=self.project, nombre="Pedido")
        target = Entidad.objects.create(proyecto=self.project, nombre="Cliente")
        relation = Relacion.objects.create(
            proyecto=self.project, entidad_origen=source, entidad_destino=target,
            tipo=Relacion.Tipo.ASOCIACION,
        )
        response = self.generate()
        self.assertEqual(response.status_code, 200)
        with self.archive(response) as archive:
            source_code = archive.read(
                "tienda/src/main/java/com/ejemplo/tienda/model/Pedido.java"
            ).decode()
            manifest = json.loads(archive.read("tienda/nodoboard-generation.json"))
        self.assertNotIn("Cliente", source_code)
        self.assertEqual(
            manifest["java_model"]["relaciones_pendientes_7c"],
            [{
                "id": relation.id,
                "tipo": "asociacion",
                "origen_id": source.id,
                "destino_id": target.id,
                "multiplicidad_origen": "",
                "multiplicidad_destino": "",
                "rol_origen": "",
                "rol_destino": "",
                "navegable_origen": False,
                "navegable_destino": False,
            }],
        )
        self.assertNotIn("jakarta.persistence", source_code)

    def test_model_false_preserves_base_generation(self):
        Entidad.objects.create(proyecto=self.project, nombre="NoGenerada")
        payload = {
            **self.payload,
            "opciones": {**self.payload["opciones"], "modelo": False},
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        with self.archive(response) as archive:
            self.assertFalse(any("/model/" in name for name in archive.namelist()))
            manifest = json.loads(archive.read("tienda/nodoboard-generation.json"))
        self.assertIsNone(manifest["java_model"])

    def test_model_generation_is_binary_deterministic_and_read_only(self):
        Entidad.objects.create(proyecto=self.project, nombre="Determinista")
        first = self.generate()
        second = self.generate()
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.content, second.content)
        self.project.refresh_from_db()
        self.assertEqual(self.project.revision, 0)

    def test_member_and_file_limits_return_structured_errors(self):
        entity = Entidad.objects.create(proyecto=self.project, nombre="Limite")
        Atributo.objects.create(entidad=entity, nombre="uno", tipo="string")
        with patch("generador.services.spring_contract.MAX_ATTRIBUTES", 0):
            response = self.generate()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "generation_limit_exceeded")

        with patch("generador.services.spring_generator.MAX_SINGLE_FILE_BYTES", 10):
            response = self.generate()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "generation_limit_exceeded")

    def test_defensive_unresolved_reference_is_structured(self):
        model = {
            "entities": [{
                "id": 1, "name": "Pedido", "kind": "clase", "abstract": False,
                "attributes": [{
                    "id": 2, "name": "cliente", "type": "Cliente",
                    "reference_id": 999, "visibility": "private", "static": False,
                    "default_value": "", "nullable": False, "order": 0,
                }],
                "operations": [],
            }],
            "relations": [],
        }
        with self.assertRaises(JavaGenerationError) as raised:
            render_java_model(model, "com.ejemplo.tienda", "TiendaApplication")
        self.assertEqual(
            raised.exception.details["diagnosticos"][0]["codigo"],
            "JAVA_UNRESOLVED_TYPE",
        )

    def _compile_model_sources(self, archive):
        javac = shutil.which("javac")
        if not javac:
            self.skipTest("javac no está disponible")
        with tempfile.TemporaryDirectory(prefix="nodoboard-java21-") as temporary:
            root = Path(temporary)
            sources = []
            for name in archive.namelist():
                if "/src/main/java/" not in name or "/model/" not in name:
                    continue
                target = root / Path(name).relative_to("tienda")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(name))
                sources.append(str(target))
            classes = root / "classes"
            classes.mkdir()
            result = subprocess.run(
                [javac, "--release", "21", "-encoding", "UTF-8", "-d", str(classes), *sources],
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
