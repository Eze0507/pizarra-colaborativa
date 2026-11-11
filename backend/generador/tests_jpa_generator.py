import io
import json
import zipfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from modelado.models import Atributo, Entidad, Operacion, Proyecto, Relacion


User = get_user_model()


class JpaGenerationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="jpa-owner", password="test")
        self.project = Proyecto.objects.create(propietario=self.owner, nombre="JPA")
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

    def entity(self, name, key_type="long", **kwargs):
        entity = Entidad.objects.create(
            proyecto=self.project,
            nombre=name,
            tipo_clasificador=Entidad.TipoClasificador.ENTIDAD_PERSISTENTE,
            **kwargs,
        )
        if key_type is not None:
            Atributo.objects.create(
                entidad=entity, nombre="id", tipo=key_type, es_clave=True, orden=1
            )
        return entity

    def generate(self, payload=None):
        return self.client.post(self.url, payload or self.payload, format="json")

    @staticmethod
    def archive(response):
        return zipfile.ZipFile(io.BytesIO(response.content))

    def test_persistent_entity_generates_jakarta_fields_dependency_and_metadata(self):
        product = self.entity("Producto")
        Atributo.objects.create(
            entidad=product, nombre="nombre", tipo="string", es_nulo=False, orden=2
        )
        Atributo.objects.create(
            entidad=product, nombre="fecha", tipo="date", es_nulo=True, orden=3
        )
        Operacion.objects.create(
            entidad=product, nombre="calcular", tipo_retorno="double", orden=1
        )

        response = self.generate()
        self.assertEqual(response.status_code, 200)
        with self.archive(response) as archive:
            source = archive.read(
                "tienda/src/main/java/com/ejemplo/tienda/model/Producto.java"
            ).decode()
            pom = archive.read("tienda/pom.xml").decode()
            readme = archive.read("tienda/README.md").decode()
            test_source = archive.read(
                "tienda/src/test/java/com/ejemplo/tienda/TiendaApplicationTests.java"
            ).decode()
            manifest = json.loads(archive.read("tienda/nodoboard-generation.json"))
        self.assertIn("import jakarta.persistence.Entity;", source)
        self.assertIn("import jakarta.persistence.Id;", source)
        self.assertIn("@Entity\npublic class Producto", source)
        self.assertIn("@Id\n    private Long id;", source)
        self.assertIn("@Column(nullable = false)\n    private String nombre;", source)
        self.assertNotIn("@GeneratedValue", source)
        self.assertNotIn("@Table", source)
        self.assertIn("Double calcular()", source)
        self.assertIn("spring-boot-starter-data-jpa", pom)
        self.assertIn("DataSourceAutoConfiguration", test_source)
        self.assertIn("Persistencia JPA de 7C", readme)
        self.assertEqual(manifest["generator_version"], "0.5.0")
        self.assertTrue(manifest["jpa_model"]["active"])
        self.assertEqual(manifest["jpa_model"]["entities"][0]["entity_id"], product.id)

    def test_model_false_does_not_activate_or_validate_jpa(self):
        self.entity("Incompleta", key_type=None)
        payload = {
            **self.payload,
            "opciones": {**self.payload["opciones"], "modelo": False},
        }
        response = self.generate(payload)
        self.assertEqual(response.status_code, 200)
        with self.archive(response) as archive:
            pom = archive.read("tienda/pom.xml").decode()
            manifest = json.loads(archive.read("tienda/nodoboard-generation.json"))
        self.assertNotIn("spring-boot-starter-data-jpa", pom)
        self.assertIsNone(manifest["jpa_model"])

    def test_model_true_without_persistent_entities_preserves_structural_generation(self):
        Entidad.objects.create(proyecto=self.project, nombre="ServicioLocal")
        response = self.generate()
        self.assertEqual(response.status_code, 200)
        with self.archive(response) as archive:
            pom = archive.read("tienda/pom.xml").decode()
            source = archive.read(
                "tienda/src/main/java/com/ejemplo/tienda/model/ServicioLocal.java"
            ).decode()
            manifest = json.loads(archive.read("tienda/nodoboard-generation.json"))
        self.assertNotIn("spring-boot-starter-data-jpa", pom)
        self.assertNotIn("jakarta.persistence", source)
        self.assertFalse(manifest["jpa_model"]["active"])

    def test_missing_composite_and_unsupported_keys_are_blocked_by_f03(self):
        missing = self.entity("SinClave", key_type=None)
        response = self.generate()
        self.assertEqual(response.status_code, 422)
        self.assertIn("JPA_ENTITY_WITHOUT_ID", str(response.data))
        missing.delete()

        composite = self.entity("Compuesta")
        Atributo.objects.create(
            entidad=composite, nombre="otra", tipo="integer", es_clave=True, orden=2
        )
        response = self.generate()
        self.assertEqual(response.status_code, 422)
        self.assertIn("JPA_COMPOSITE_ID_UNSUPPORTED", str(response.data))
        composite.delete()

        self.entity("ClaveFecha", key_type="date")
        response = self.generate()
        self.assertEqual(response.status_code, 422)
        self.assertIn("JPA_UNSUPPORTED_ID_TYPE", str(response.data))

    def test_all_unidirectional_cardinalities_generate_expected_annotations(self):
        cases = (
            ("UnoUno", "1", "1", "OneToOne", "detalle"),
            ("MuchosUno", "*", "1", "ManyToOne", "cliente"),
            ("UnoMuchos", "1", "*", "OneToMany", "pedidos"),
            ("MuchosMuchos", "*", "*", "ManyToMany", "etiquetas"),
        )
        expected_owners = {}
        for prefix, source_mult, target_mult, annotation, role in cases:
            source = self.entity(f"{prefix}Origen")
            target = self.entity(f"{prefix}Destino")
            relation = Relacion.objects.create(
                proyecto=self.project,
                entidad_origen=source,
                entidad_destino=target,
                tipo=Relacion.Tipo.ASOCIACION,
                cardinalidad_origen=source_mult,
                cardinalidad_destino=target_mult,
                rol_destino=role,
                navegable_destino=True,
            )
            expected_owners[source.nombre] = (annotation, role, target.nombre, relation.id)

        response = self.generate()
        self.assertEqual(response.status_code, 200)
        with self.archive(response) as archive:
            manifest = json.loads(archive.read("tienda/nodoboard-generation.json"))
            for owner, (annotation, role, target, _) in expected_owners.items():
                source = archive.read(
                    f"tienda/src/main/java/com/ejemplo/tienda/model/{owner}.java"
                ).decode()
                self.assertIn(f"@{annotation}", source)
                if annotation in {"OneToMany", "ManyToMany"}:
                    self.assertIn(f"List<{target}> {role};", source)
                else:
                    self.assertIn(f"{target} {role};", source)
                self.assertNotIn("mappedBy", source)
                self.assertNotIn("cascade", source)
                self.assertNotIn("orphanRemoval", source)
        self.assertEqual(len(manifest["jpa_model"]["relationships"]), 4)

    def test_reverse_navigation_uses_source_role_and_target_owner(self):
        source = self.entity("Departamento")
        target = self.entity("Empleado")
        Relacion.objects.create(
            proyecto=self.project, entidad_origen=source, entidad_destino=target,
            tipo=Relacion.Tipo.AGREGACION,
            cardinalidad_origen="1", cardinalidad_destino="*",
            rol_origen="departamento", navegable_origen=True,
        )
        response = self.generate()
        self.assertEqual(response.status_code, 200)
        with self.archive(response) as archive:
            target_source = archive.read(
                "tienda/src/main/java/com/ejemplo/tienda/model/Empleado.java"
            ).decode()
        self.assertIn("@ManyToOne", target_source)
        self.assertIn("Departamento departamento;", target_source)

    def test_typed_reference_is_reused_once_for_matching_to_one_relation(self):
        order = self.entity("Pedido")
        customer = self.entity("Cliente")
        reference = Atributo.objects.create(
            entidad=order, nombre="cliente", tipo="Cliente",
            tipo_referencia=customer, es_nulo=False, orden=2,
        )
        Relacion.objects.create(
            proyecto=self.project, entidad_origen=order, entidad_destino=customer,
            tipo=Relacion.Tipo.ASOCIACION,
            cardinalidad_origen="*", cardinalidad_destino="1",
            rol_destino="cliente", navegable_destino=True,
        )
        response = self.generate()
        self.assertEqual(response.status_code, 200)
        with self.archive(response) as archive:
            source = archive.read(
                "tienda/src/main/java/com/ejemplo/tienda/model/Pedido.java"
            ).decode()
            manifest = json.loads(archive.read("tienda/nodoboard-generation.json"))
        self.assertEqual(source.count("Cliente cliente;"), 1)
        self.assertIn("@ManyToOne", source)
        self.assertEqual(
            manifest["jpa_model"]["relationships"][0]["reused_attribute_id"],
            reference.id,
        )

    def test_unmapped_and_ambiguous_relations_follow_navigation_policy(self):
        source = self.entity("Origen")
        target = self.entity("Destino")
        unmapped = Relacion.objects.create(
            proyecto=self.project, entidad_origen=source, entidad_destino=target,
            tipo=Relacion.Tipo.COMPOSICION,
            cardinalidad_origen="1", cardinalidad_destino="1",
        )
        response = self.generate()
        self.assertEqual(response.status_code, 200)
        with self.archive(response) as archive:
            manifest = json.loads(archive.read("tienda/nodoboard-generation.json"))
        self.assertEqual(
            manifest["jpa_model"]["unmapped_relationships"][0]["relation_id"],
            unmapped.id,
        )

        unmapped.navegable_origen = True
        unmapped.navegable_destino = True
        unmapped.save(update_fields=["navegable_origen", "navegable_destino"])
        response = self.generate()
        self.assertEqual(response.status_code, 422)
        self.assertIn("JPA_RELATION_MAPPING_AMBIGUOUS", str(response.data))

    def test_missing_role_nonpersistent_endpoint_or_orphan_reference_is_rejected(self):
        source = self.entity("Pedido")
        target = self.entity("Cliente")
        relation = Relacion.objects.create(
            proyecto=self.project, entidad_origen=source, entidad_destino=target,
            tipo=Relacion.Tipo.ASOCIACION,
            cardinalidad_origen="*", cardinalidad_destino="1",
            navegable_destino=True,
        )
        response = self.generate()
        self.assertEqual(response.status_code, 422)
        self.assertIn("JPA_RELATION_MAPPING_AMBIGUOUS", str(response.data))
        relation.delete()

        ordinary = Entidad.objects.create(proyecto=self.project, nombre="Auxiliar")
        Relacion.objects.create(
            proyecto=self.project, entidad_origen=source, entidad_destino=ordinary,
            tipo=Relacion.Tipo.ASOCIACION,
            cardinalidad_origen="1", cardinalidad_destino="1",
            rol_destino="auxiliar", navegable_destino=True,
        )
        response = self.generate()
        self.assertEqual(response.status_code, 422)
        self.assertIn("JPA_NON_PERSISTENT_RELATION_ENDPOINT", str(response.data))

    def test_orphan_reference_is_rejected_and_jpa_inheritance_uses_joined(self):
        source = self.entity("Pedido")
        target = self.entity("Cliente")
        Atributo.objects.create(
            entidad=source, nombre="cliente", tipo="Cliente",
            tipo_referencia=target, orden=2,
        )
        response = self.generate()
        self.assertEqual(response.status_code, 400)
        self.assertIn("JPA_UNSUPPORTED_ATTRIBUTE_TYPE", str(response.data))

        self.project.entidades.all().delete()
        parent = self.entity("Base")
        child = self.entity("Derivada", key_type=None)
        Atributo.objects.create(
            entidad=child, nombre="detalle", tipo="string", orden=1,
        )
        Relacion.objects.create(
            proyecto=self.project, entidad_origen=child, entidad_destino=parent,
            tipo=Relacion.Tipo.HERENCIA,
        )
        response = self.generate()
        self.assertEqual(response.status_code, 200)
        with self.archive(response) as archive:
            parent_source = archive.read(
                "tienda/src/main/java/com/ejemplo/tienda/model/Base.java"
            ).decode()
            child_source = archive.read(
                "tienda/src/main/java/com/ejemplo/tienda/model/Derivada.java"
            ).decode()
            manifest = json.loads(archive.read("tienda/nodoboard-generation.json"))
        self.assertIn("@Inheritance(strategy = InheritanceType.JOINED)", parent_source)
        self.assertIn('@PrimaryKeyJoinColumn(name = "id")', child_source)
        self.assertIn("public class Derivada extends Base", child_source)
        self.assertEqual(manifest["jpa_model"]["inheritance"], "joined")

    def test_relation_role_collision_is_rejected_without_renaming(self):
        source = self.entity("Pedido")
        target = self.entity("Cliente")
        Atributo.objects.create(
            entidad=source, nombre="cliente", tipo="string", orden=2
        )
        Relacion.objects.create(
            proyecto=self.project, entidad_origen=source, entidad_destino=target,
            tipo=Relacion.Tipo.ASOCIACION,
            cardinalidad_origen="*", cardinalidad_destino="1",
            rol_destino="cliente", navegable_destino=True,
        )
        response = self.generate()
        self.assertEqual(response.status_code, 400)
        self.assertIn("JPA_FIELD_NAME_COLLISION", str(response.data))

    def test_jpa_zip_is_binary_deterministic_and_generation_is_read_only(self):
        self.entity("Determinista")
        first = self.generate()
        second = self.generate()
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.content, second.content)
        self.project.refresh_from_db()
        self.assertEqual(self.project.revision, 0)

    def test_generated_relation_fields_participate_in_member_limits(self):
        source = self.entity("Pedido")
        target = self.entity("Cliente")
        Relacion.objects.create(
            proyecto=self.project, entidad_origen=source, entidad_destino=target,
            tipo=Relacion.Tipo.ASOCIACION,
            cardinalidad_origen="*", cardinalidad_destino="1",
            rol_destino="cliente", navegable_destino=True,
        )
        with patch("generador.services.spring_contract.MAX_MEMBERS_PER_CLASSIFIER", 1):
            response = self.generate()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "generation_limit_exceeded")
