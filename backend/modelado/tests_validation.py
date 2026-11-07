from copy import deepcopy
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from usuario.models import UserColaborador
from .models import Atributo, Entidad, Operacion, ParametroOperacion, Proyecto, Relacion
from .validation import UMLValidator, extract_project_model, validate_project


User = get_user_model()


def codes(result):
    return [finding["codigo"] for finding in result["hallazgos"]]


class UMLValidatorUnitTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="validator", password="test")
        self.project = Proyecto.objects.create(propietario=self.owner, nombre="Validacion")

    def test_valid_uml_and_java_overload_are_deterministic(self):
        entity = Entidad.objects.create(proyecto=self.project, nombre="Pedido", abstracto=True)
        Atributo.objects.create(entidad=entity, nombre="codigo", tipo="string", orden=1)
        for index, param_type in enumerate(("string", "integer"), start=1):
            operation = Operacion.objects.create(entidad=entity, nombre="buscar", tipo_retorno="string", orden=index)
            ParametroOperacion.objects.create(operacion=operation, nombre="valor", tipo=param_type, orden=1)
        first = validate_project(self.project, "java")
        second = validate_project(self.project, "java")
        self.assertTrue(first["valido"])
        self.assertEqual(first["hallazgos"], second["hallazgos"])
        self.assertNotIn("JAVA_DUPLICATE_METHOD_SIGNATURE", codes(first))

    def test_names_reserved_words_duplicates_and_duplicate_signatures(self):
        entity = Entidad.objects.create(proyecto=self.project, nombre="class")
        Atributo.objects.create(entidad=entity, nombre="valor", tipo="string", orden=1)
        Atributo.objects.create(entidad=entity, nombre="valor", tipo="string", orden=2)
        for index in range(2):
            operation = Operacion.objects.create(entidad=entity, nombre="for", tipo_retorno="void", orden=index)
            ParametroOperacion.objects.create(operacion=operation, nombre="_", tipo="string", orden=1)
        result = validate_project(self.project, "java")
        self.assertIn("UML_DUPLICATE_ATTRIBUTE", codes(result))
        self.assertIn("JAVA_RESERVED_WORD", codes(result))
        self.assertIn("JAVA_DUPLICATE_METHOD_SIGNATURE", codes(result))

    def test_auth_user_is_valid_identifier_with_convention_warning(self):
        Entidad.objects.create(proyecto=self.project, nombre="auth_user")
        result = validate_project(self.project, "java")
        self.assertNotIn("JAVA_INVALID_IDENTIFIER", codes(result))
        self.assertIn("JAVA_NAMING_CONVENTION", codes(result))

    def test_void_custom_types_and_cross_project_references(self):
        other = Proyecto.objects.create(propietario=self.owner, nombre="Otro")
        external = Entidad.objects.create(proyecto=other, nombre="Externo")
        entity = Entidad.objects.create(proyecto=self.project, nombre="Pedido")
        Atributo.objects.create(entidad=entity, nombre="invalido", tipo="void", orden=1)
        Atributo.objects.create(entidad=entity, nombre="custom", tipo="Money", orden=2)
        Atributo.objects.create(entidad=entity, nombre="externo", tipo="Externo", tipo_referencia=external, orden=3)
        uml = validate_project(self.project, "uml")
        java = validate_project(self.project, "java")
        self.assertIn("UML_VOID_NOT_ALLOWED", codes(uml))
        self.assertIn("UML_CROSS_PROJECT_REFERENCE", codes(uml))
        self.assertIn("JAVA_UNMAPPABLE_TYPE", codes(java))

    def test_multiplicity_syntax_inverted_range_and_duplicates(self):
        source = Entidad.objects.create(proyecto=self.project, nombre="Origen")
        target = Entidad.objects.create(proyecto=self.project, nombre="Destino")
        valid_model = extract_project_model(self.project)
        valid_model["relations"] = [
            {"id": 1, "project_id": self.project.id, "type": "asociacion", "source_id": source.id,
             "target_id": target.id, "source_project_id": self.project.id, "target_project_id": self.project.id,
             "source_multiplicity": "2..5", "target_multiplicity": "*"},
            {"id": 2, "project_id": self.project.id, "type": "asociacion", "source_id": source.id,
             "target_id": target.id, "source_project_id": self.project.id, "target_project_id": self.project.id,
             "source_multiplicity": "3..1", "target_multiplicity": "*..2"},
        ]
        result = UMLValidator(valid_model, "uml").validate()
        self.assertIn("UML_INVERTED_MULTIPLICITY", codes(result))
        self.assertIn("UML_INVALID_MULTIPLICITY", codes(result))
        self.assertIn("UML_DUPLICATE_RELATION", codes(result))

    def test_unknown_relation_and_missing_endpoint_from_structured_input(self):
        model = extract_project_model(self.project)
        model["relations"] = [{
            "id": 99, "type": "dependencia", "source_id": 100, "target_id": 101,
            "source_project_id": self.project.id, "target_project_id": self.project.id,
            "source_multiplicity": "1", "target_multiplicity": "1",
        }]
        result = UMLValidator(model, "uml").validate()
        self.assertIn("UML_UNKNOWN_RELATION_TYPE", codes(result))
        self.assertEqual(codes(result).count("UML_INVALID_RELATION_ENDPOINT"), 2)

    def test_java_inheritance_interface_rules_multiple_inheritance_and_cycle(self):
        base1 = Entidad.objects.create(proyecto=self.project, nombre="BaseUno")
        base2 = Entidad.objects.create(proyecto=self.project, nombre="BaseDos")
        child = Entidad.objects.create(proyecto=self.project, nombre="Hija")
        interface = Entidad.objects.create(proyecto=self.project, nombre="Contrato", tipo_clasificador="interfaz", abstracto=True)
        Relacion.objects.create(proyecto=self.project, entidad_origen=child, entidad_destino=base1, tipo="herencia")
        Relacion.objects.create(proyecto=self.project, entidad_origen=child, entidad_destino=base2, tipo="herencia")
        Relacion.objects.create(proyecto=self.project, entidad_origen=base1, entidad_destino=child, tipo="herencia")
        Relacion.objects.create(proyecto=self.project, entidad_origen=interface, entidad_destino=child, tipo="implementacion")
        result = validate_project(self.project, "java")
        self.assertIn("JAVA_MULTIPLE_CLASS_INHERITANCE", codes(result))
        self.assertIn("JAVA_INHERITANCE_CYCLE", codes(result))
        self.assertIn("JAVA_INVALID_INTERFACE_IMPLEMENTATION", codes(result))

    def test_relation_project_roles_and_navigability_are_structural(self):
        model = extract_project_model(self.project)
        model["relations"] = [{
            "id": 100, "project_id": 999, "type": "asociacion",
            "source_id": 1, "target_id": 2,
            "source_project_id": self.project.id, "target_project_id": self.project.id,
            "source_multiplicity": "1", "target_multiplicity": "1",
            "source_role": 3, "target_role": "destino",
            "source_navigable": "yes", "target_navigable": False,
        }]
        result = UMLValidator(model, "uml").validate()
        self.assertIn("UML_CROSS_PROJECT_RELATION", codes(result))
        self.assertIn("UML_INVALID_ROLE", codes(result))
        self.assertIn("UML_INVALID_NAVIGABILITY", codes(result))

    def test_abstract_operation_constraints(self):
        entity = Entidad.objects.create(proyecto=self.project, nombre="Concreta", abstracto=False)
        Operacion.objects.create(entidad=entity, nombre="calcular", tipo_retorno="void", es_abstracto=True, es_estatico=True)
        result = validate_project(self.project, "java")
        self.assertIn("JAVA_ABSTRACT_METHOD_IN_CONCRETE_CLASS", codes(result))
        self.assertIn("JAVA_STATIC_ABSTRACT_OPERATION", codes(result))

    def test_jpa_id_types_and_ambiguous_relations(self):
        first = Entidad.objects.create(proyecto=self.project, nombre="Pedido", tipo_clasificador="entidad_persistente")
        second = Entidad.objects.create(proyecto=self.project, nombre="Cliente", tipo_clasificador="entidad_persistente")
        third = Entidad.objects.create(proyecto=self.project, nombre="Auxiliar")
        Atributo.objects.create(entidad=first, nombre="idUno", tipo="long", es_clave=True, orden=1)
        Atributo.objects.create(entidad=first, nombre="idDos", tipo="long", es_clave=True, orden=2)
        Atributo.objects.create(entidad=first, nombre="monto", tipo="Money", orden=3)
        Relacion.objects.create(
            proyecto=self.project, entidad_origen=first, entidad_destino=second,
            tipo="asociacion", navegable_origen=True, navegable_destino=True,
        )
        Relacion.objects.create(
            proyecto=self.project, entidad_origen=first, entidad_destino=third,
            tipo="agregacion", navegable_destino=True,
        )
        result = validate_project(self.project, "jpa")
        self.assertIn("JPA_COMPOSITE_ID_UNSUPPORTED", codes(result))
        self.assertIn("JPA_ENTITY_WITHOUT_ID", codes(result))
        self.assertIn("JPA_UNPERSISTABLE_TYPE", codes(result))
        self.assertIn("JPA_RELATION_MAPPING_AMBIGUOUS", codes(result))
        self.assertIn("JPA_NON_PERSISTENT_RELATION_ENDPOINT", codes(result))

    def test_validator_does_not_mutate_structured_input(self):
        model = extract_project_model(self.project)
        before = deepcopy(model)
        UMLValidator(model, "jpa").validate()
        self.assertEqual(model, before)

    def test_valid_relation_kinds_and_multiplicities(self):
        source = Entidad.objects.create(proyecto=self.project, nombre="Origen")
        target = Entidad.objects.create(proyecto=self.project, nombre="Destino")
        model = extract_project_model(self.project)
        valid_multiplicities = ("0", "1", "2", "*", "0..1", "0..*", "1..*", "2..5")
        model["relations"] = [
            {
                "id": index, "type": kind, "source_id": source.id, "target_id": target.id,
                "source_project_id": self.project.id, "target_project_id": self.project.id,
                "source_multiplicity": valid_multiplicities[index - 1], "target_multiplicity": "1",
            }
            for index, kind in enumerate(("asociacion", "agregacion", "composicion", "herencia", "implementacion"), start=1)
        ]
        result = UMLValidator(model, "uml").validate()
        self.assertNotIn("UML_UNKNOWN_RELATION_TYPE", codes(result))
        self.assertNotIn("UML_INVALID_MULTIPLICITY", codes(result))

    def test_targets_summary_order_and_warning_only_validity(self):
        entity = Entidad.objects.create(proyecto=self.project, nombre="auth_user")
        operation = Operacion.objects.create(entidad=entity, nombre="buscar_valor", tipo_retorno="void")
        parameter = ParametroOperacion.objects.create(operacion=operation, nombre="un_valor", tipo="string")
        result = validate_project(self.project, "java")
        self.assertTrue(result["valido"])
        self.assertGreater(result["resumen"]["advertencias"], 0)
        targets = {item["objetivo"]["tipo"]: item["objetivo"] for item in result["hallazgos"]}
        self.assertEqual(targets["parametro"]["clasificador_id"], entity.id)
        self.assertEqual(targets["parametro"]["operacion_id"], operation.id)
        self.assertEqual(parameter.operacion_id, operation.id)
        expected = sorted(result["hallazgos"], key=lambda f: (
            {"error": 0, "warning": 1, "info": 2}[f["severidad"]], f["codigo"],
            f["objetivo"]["tipo"], f["objetivo"]["id"], f.get("campo", ""),
        ))
        self.assertEqual(result["hallazgos"], expected)


class ValidationApiTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner-validation", password="test")
        self.editor = User.objects.create_user(username="editor-validation", password="test")
        self.viewer = User.objects.create_user(username="viewer-validation", password="test")
        self.removed = User.objects.create_user(username="removed-validation", password="test")
        self.pending = User.objects.create_user(username="pending-validation", password="test")
        self.outsider = User.objects.create_user(username="outsider-validation", password="test")
        self.project = Proyecto.objects.create(propietario=self.owner, nombre="API")
        self.entity = Entidad.objects.create(proyecto=self.project, nombre="Pedido")
        for user, role, state in (
            (self.editor, UserColaborador.Rol.EDITOR, UserColaborador.Estado.ACTIVO),
            (self.viewer, UserColaborador.Rol.VISUALIZADOR, UserColaborador.Estado.ACTIVO),
            (self.pending, UserColaborador.Rol.EDITOR, UserColaborador.Estado.PENDIENTE),
        ):
            UserColaborador.objects.create(proyecto=self.project, usuario=user, rol=role, estado=state)
        self.url = f"/api/modelado/proyectos/{self.project.id}/validacion/"
        self.client = APIClient()

    def test_active_roles_can_validate_and_unknown_profile_is_400(self):
        for user in (self.owner, self.editor, self.viewer):
            self.client.force_authenticate(user)
            response = self.client.get(self.url, {"perfil": "uml"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["origen"], "orm")
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.get(self.url, {"perfil": "otro"}).status_code, 400)

    def test_unauthenticated_removed_and_external_are_rejected(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)
        for user in (self.removed, self.pending, self.outsider):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_validation_does_not_write_project_or_model(self):
        self.client.force_authenticate(self.owner)
        before = {
            "updated": self.project.fecha_actualizacion,
            "snapshot": deepcopy(self.project.datos_diagrama),
            "entities": self.project.entidades.count(),
            "attributes": Atributo.objects.filter(entidad__proyecto=self.project).count(),
            "operations": Operacion.objects.filter(entidad__proyecto=self.project).count(),
            "parameters": ParametroOperacion.objects.filter(operacion__entidad__proyecto=self.project).count(),
            "relations": self.project.relaciones.count(),
        }
        with patch("modelado.realtime.async_to_sync") as websocket_bridge:
            response = self.client.get(self.url, {"perfil": "jpa"})
        websocket_bridge.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.project.refresh_from_db()
        after = {
            "updated": self.project.fecha_actualizacion,
            "snapshot": self.project.datos_diagrama,
            "entities": self.project.entidades.count(),
            "attributes": Atributo.objects.filter(entidad__proyecto=self.project).count(),
            "operations": Operacion.objects.filter(entidad__proyecto=self.project).count(),
            "parameters": ParametroOperacion.objects.filter(operacion__entidad__proyecto=self.project).count(),
            "relations": self.project.relaciones.count(),
        }
        self.assertEqual(before, after)
