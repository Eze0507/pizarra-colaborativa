"""Validación determinista y de solo lectura del contrato UML de NodoBoard."""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any, Iterable

from .models import Atributo, Entidad, Proyecto, Relacion
from .jpa_policy import JpaPolicyIssue, analyze_unidirectional_relation, parse_multiplicity


PROFILES = frozenset({"uml", "java", "jpa"})
SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}
SIMPLE_TYPES = frozenset(Atributo.Tipo.values)
JAVA_TYPES = {
    "string": "String", "integer": "Integer", "long": "Long",
    "double": "Double", "boolean": "Boolean", "date": "LocalDate",
}
JAVA_IDENTIFIER = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")
JAVA_RESERVED = frozenset({
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
    "class", "const", "continue", "default", "do", "double", "else", "enum",
    "extends", "final", "finally", "float", "for", "goto", "if", "implements",
    "import", "instanceof", "int", "interface", "long", "native", "new", "package",
    "private", "protected", "public", "return", "short", "static", "strictfp",
    "super", "switch", "synchronized", "this", "throw", "throws", "transient",
    "try", "void", "volatile", "while", "true", "false", "null", "_", "record",
    "sealed", "permits", "non-sealed", "var", "yield",
})
RELATION_TYPES = frozenset(Relacion.Tipo.values)


def extract_project_model(project: Proyecto) -> dict[str, Any]:
    """Extrae un DTO efímero desde ORM; no consulta datos_diagrama ni guarda objetos."""
    entities = list(
        project.entidades.exclude(estado=Entidad.Estado.PAPELERA)
        .prefetch_related("atributos", "operaciones__parametros")
        .order_by("id")
    )
    relations = list(
        project.relaciones.select_related("entidad_origen", "entidad_destino").order_by("id")
    )
    return {
        "project_id": project.id,
        # Proyecto.fecha_actualizacion no cambia necesariamente cuando se edita
        # un miembro relacionado; por ello no se presenta como revision global.
        "updated_at": None,
        "entities": [
            {
                "id": e.id, "project_id": e.proyecto_id, "name": e.nombre,
                "kind": e.tipo_clasificador, "abstract": e.abstracto,
                "attributes": [
                    {
                        "id": a.id, "name": a.nombre, "type": a.tipo,
                        "reference_id": a.tipo_referencia_id,
                        "reference_project_id": a.tipo_referencia.proyecto_id if a.tipo_referencia_id else None,
                        "visibility": a.visibilidad, "static": a.es_estatico,
                        "default_value": a.valor_predeterminado,
                        "is_key": a.es_clave, "nullable": a.es_nulo, "order": a.orden,
                    }
                    for a in e.atributos.all().order_by("orden", "id")
                ],
                "operations": [
                    {
                        "id": o.id, "name": o.nombre, "return_type": o.tipo_retorno,
                        "return_reference_id": o.retorno_referencia_id,
                        "return_reference_project_id": o.retorno_referencia.proyecto_id if o.retorno_referencia_id else None,
                        "visibility": o.visibilidad, "abstract": o.es_abstracto,
                        "static": o.es_estatico, "order": o.orden,
                        "parameters": [
                            {
                                "id": p.id, "name": p.nombre, "type": p.tipo,
                                "reference_id": p.tipo_referencia_id,
                                "reference_project_id": p.tipo_referencia.proyecto_id if p.tipo_referencia_id else None,
                                "order": p.orden,
                            }
                            for p in o.parametros.all().order_by("orden", "id")
                        ],
                    }
                    for o in e.operaciones.all().order_by("orden", "id")
                ],
            }
            for e in entities
        ],
        "relations": [
            {
                "id": r.id, "project_id": r.proyecto_id, "type": r.tipo,
                "source_id": r.entidad_origen_id, "target_id": r.entidad_destino_id,
                "source_project_id": r.entidad_origen.proyecto_id,
                "target_project_id": r.entidad_destino.proyecto_id,
                "source_multiplicity": r.cardinalidad_origen,
                "target_multiplicity": r.cardinalidad_destino,
                "source_role": r.rol_origen, "target_role": r.rol_destino,
                "source_navigable": r.navegable_origen, "target_navigable": r.navegable_destino,
            }
            for r in relations
        ],
    }


class UMLValidator:
    def __init__(self, model: dict[str, Any], profile: str):
        if profile not in PROFILES:
            raise ValueError("Perfil de validación desconocido.")
        self.model = model
        self.profile = profile
        self.findings: list[dict[str, Any]] = []
        self.entities = {e["id"]: e for e in model.get("entities", [])}

    def add(self, code: str, severity: str, message: str, target: dict[str, Any], field: str | None = None) -> None:
        finding = {"codigo": code, "severidad": severity, "mensaje": message, "objetivo": target}
        if field:
            finding["campo"] = field
        self.findings.append(finding)

    def validate(self) -> dict[str, Any]:
        self._validate_uml()
        if self.profile in {"java", "jpa"}:
            self._validate_java()
        if self.profile == "jpa":
            self._validate_jpa()
        self.findings.sort(key=lambda f: (
            SEVERITY_ORDER[f["severidad"]], f["codigo"], f["objetivo"].get("tipo", ""),
            f["objetivo"].get("id") or 0, f.get("campo", ""),
        ))
        counts = Counter(f["severidad"] for f in self.findings)
        return {
            "origen": "orm", "proyecto_id": self.model.get("project_id"),
            "fecha_actualizacion": self.model.get("updated_at"), "perfil": self.profile,
            "valido": counts["error"] == 0,
            "resumen": {"errores": counts["error"], "advertencias": counts["warning"], "informativos": counts["info"]},
            "hallazgos": self.findings,
        }

    @staticmethod
    def _target(kind: str, object_id: int, **parents: int) -> dict[str, Any]:
        return {"tipo": kind, "id": object_id, **parents}

    def _validate_uml(self) -> None:
        names: dict[str, list[int]] = defaultdict(list)
        for entity in self.entities.values():
            target = self._target("clasificador", entity["id"])
            name = (entity.get("name") or "").strip()
            if not name:
                self.add("UML_REQUIRED_NAME", "error", "El clasificador debe tener nombre.", target, "nombre")
            else:
                names[name].append(entity["id"])
            if entity.get("kind") not in Entidad.TipoClasificador.values:
                self.add("UML_UNKNOWN_CLASSIFIER_KIND", "error", "El tipo de clasificador no es reconocido.", target, "tipo_clasificador")
            self._validate_members(entity)
        for name, ids in names.items():
            if len(ids) > 1:
                for entity_id in ids:
                    self.add("UML_DUPLICATE_CLASSIFIER", "error", f"El clasificador '{name}' está duplicado.", self._target("clasificador", entity_id), "nombre")
        self._validate_relations()

    def _validate_members(self, entity: dict[str, Any]) -> None:
        attr_names: dict[str, list[int]] = defaultdict(list)
        for attr in entity.get("attributes", []):
            target = self._target("atributo", attr["id"], clasificador_id=entity["id"])
            name = (attr.get("name") or "").strip()
            if not name:
                self.add("UML_REQUIRED_NAME", "error", "El atributo debe tener nombre.", target, "nombre")
            else:
                attr_names[name].append(attr["id"])
            self._validate_type(attr.get("type"), attr.get("reference_id"), attr.get("reference_project_id"), target, "tipo", allow_void=False)
        for name, ids in attr_names.items():
            if len(ids) > 1:
                for object_id in ids:
                    self.add("UML_DUPLICATE_ATTRIBUTE", "error", f"El atributo '{name}' está duplicado.", self._target("atributo", object_id, clasificador_id=entity["id"]), "nombre")
        for operation in entity.get("operations", []):
            op_target = self._target("operacion", operation["id"], clasificador_id=entity["id"])
            if not (operation.get("name") or "").strip():
                self.add("UML_REQUIRED_NAME", "error", "La operación debe tener nombre.", op_target, "nombre")
            self._validate_type(operation.get("return_type"), operation.get("return_reference_id"), operation.get("return_reference_project_id"), op_target, "tipo_retorno", allow_void=True)
            param_names: dict[str, list[int]] = defaultdict(list)
            for param in operation.get("parameters", []):
                target = self._target("parametro", param["id"], operacion_id=operation["id"], clasificador_id=entity["id"])
                name = (param.get("name") or "").strip()
                if not name:
                    self.add("UML_REQUIRED_NAME", "error", "El parámetro debe tener nombre.", target, "nombre")
                else:
                    param_names[name].append(param["id"])
                self._validate_type(param.get("type"), param.get("reference_id"), param.get("reference_project_id"), target, "tipo", allow_void=False)
            for name, ids in param_names.items():
                if len(ids) > 1:
                    for object_id in ids:
                        self.add("UML_DUPLICATE_PARAMETER", "error", f"El parámetro '{name}' está duplicado.", self._target("parametro", object_id, operacion_id=operation["id"], clasificador_id=entity["id"]), "nombre")

    def _validate_type(self, type_name: str | None, reference_id: int | None, reference_project_id: int | None, target: dict[str, Any], field: str, allow_void: bool) -> None:
        raw = (type_name or "").strip()
        if reference_id is not None:
            referenced = self.entities.get(reference_id)
            if referenced is None:
                code = "UML_CROSS_PROJECT_REFERENCE" if reference_project_id and reference_project_id != self.model.get("project_id") else "UML_UNRESOLVED_REFERENCE"
                self.add(code, "error", "La referencia de tipo no pertenece al modelo validado.", target, field)
            elif raw and raw != referenced.get("name"):
                self.add("UML_REFERENCE_NAME_MISMATCH", "warning", "El texto del tipo no coincide con el clasificador referenciado.", target, field)
            return
        if not raw:
            self.add("UML_REQUIRED_TYPE", "error", "Debe especificarse un tipo.", target, field)
        elif raw == "void" and not allow_void:
            self.add("UML_VOID_NOT_ALLOWED", "error", "void solo se permite como retorno de una operación.", target, field)

    @staticmethod
    def _parse_multiplicity(value: str) -> tuple[int, int | None] | None:
        return parse_multiplicity(value)

    def _validate_relations(self) -> None:
        seen = defaultdict(list)
        inheritance: dict[int, list[int]] = defaultdict(list)
        for relation in self.model.get("relations", []):
            target = self._target("relacion", relation["id"])
            relation_type = relation.get("type")
            if relation.get("project_id") not in (None, self.model.get("project_id")):
                self.add("UML_CROSS_PROJECT_RELATION", "error", "La relación no pertenece al proyecto validado.", target, "proyecto_id")
            if relation_type not in RELATION_TYPES:
                self.add("UML_UNKNOWN_RELATION_TYPE", "error", "El tipo de relación no es reconocido.", target, "tipo")
            for side in ("source", "target"):
                entity_id = relation.get(f"{side}_id")
                if entity_id not in self.entities or relation.get(f"{side}_project_id") != self.model.get("project_id"):
                    self.add("UML_INVALID_RELATION_ENDPOINT", "error", "El extremo de la relación no pertenece al proyecto.", target, f"entidad_{'origen' if side == 'source' else 'destino'}_id")
            for field, api_field in (("source_role", "rol_origen"), ("target_role", "rol_destino")):
                if not isinstance(relation.get(field, ""), str):
                    self.add("UML_INVALID_ROLE", "error", "El rol de la relación debe ser texto.", target, api_field)
            for field, api_field in (("source_navigable", "navegable_origen"), ("target_navigable", "navegable_destino")):
                if field in relation and not isinstance(relation[field], bool):
                    self.add("UML_INVALID_NAVIGABILITY", "error", "La navegabilidad debe ser un valor booleano.", target, api_field)
            for field in ("source_multiplicity", "target_multiplicity"):
                value = (relation.get(field) or "").strip()
                api_field = "cardinalidad_origen" if field.startswith("source") else "cardinalidad_destino"
                if not value:
                    self.add("UML_MULTIPLICITY_UNSPECIFIED", "warning", "La multiplicidad no está especificada.", target, api_field)
                    continue
                parsed = self._parse_multiplicity(value)
                if parsed is None:
                    self.add("UML_INVALID_MULTIPLICITY", "error", "La multiplicidad tiene una sintaxis inválida.", target, api_field)
                elif parsed[1] is not None and parsed[0] > parsed[1]:
                    self.add("UML_INVERTED_MULTIPLICITY", "error", "El límite inferior supera al superior.", target, api_field)
            key = (relation_type, relation.get("source_id"), relation.get("target_id"))
            seen[key].append(relation["id"])
            if relation_type == Relacion.Tipo.HERENCIA:
                inheritance[relation.get("source_id")].append(relation.get("target_id"))
        for ids in seen.values():
            if len(ids) > 1:
                for relation_id in ids:
                    self.add("UML_DUPLICATE_RELATION", "warning", "Existe una relación equivalente duplicada.", self._target("relacion", relation_id))
        self._inheritance_cycles(inheritance)

    def _inheritance_cycles(self, graph: dict[int, list[int]]) -> None:
        visited, active, cycle_nodes = set(), set(), set()
        def visit(node: int) -> None:
            if node in active:
                cycle_nodes.update(active); return
            if node in visited: return
            active.add(node)
            for target in graph.get(node, []): visit(target)
            active.remove(node); visited.add(node)
        for node in sorted(graph): visit(node)
        for relation in self.model.get("relations", []):
            if relation.get("type") == Relacion.Tipo.HERENCIA and relation.get("source_id") in cycle_nodes:
                self.add("JAVA_INHERITANCE_CYCLE", "error" if self.profile != "uml" else "warning", "La jerarquía contiene un ciclo de herencia.", self._target("relacion", relation["id"]))

    def _validate_java(self) -> None:
        for entity in self.entities.values():
            self._java_name(entity.get("name"), self._target("clasificador", entity["id"]), "nombre", "classifier")
            signatures = defaultdict(list)
            for attr in entity.get("attributes", []):
                target = self._target("atributo", attr["id"], clasificador_id=entity["id"])
                self._java_name(attr.get("name"), target, "nombre", "member")
                self._java_type(attr.get("type"), attr.get("reference_id"), target, "tipo", False)
            for operation in entity.get("operations", []):
                target = self._target("operacion", operation["id"], clasificador_id=entity["id"])
                self._java_name(operation.get("name"), target, "nombre", "member")
                self._java_type(operation.get("return_type"), operation.get("return_reference_id"), target, "tipo_retorno", True)
                signature = (operation.get("name"), tuple((p.get("reference_id") or p.get("type")) for p in operation.get("parameters", [])))
                signatures[signature].append(operation["id"])
                if operation.get("abstract") and not entity.get("abstract") and entity.get("kind") != Entidad.TipoClasificador.INTERFAZ:
                    self.add("JAVA_ABSTRACT_METHOD_IN_CONCRETE_CLASS", "error", "Una clase concreta no puede declarar una operación abstracta.", target, "es_abstracto")
                if operation.get("abstract") and operation.get("static"):
                    self.add("JAVA_STATIC_ABSTRACT_OPERATION", "error", "Una operación no puede ser estática y abstracta.", target, "es_estatico")
                for param in operation.get("parameters", []):
                    p_target = self._target("parametro", param["id"], operacion_id=operation["id"], clasificador_id=entity["id"])
                    self._java_name(param.get("name"), p_target, "nombre", "member")
                    self._java_type(param.get("type"), param.get("reference_id"), p_target, "tipo", False)
            for ids in signatures.values():
                if len(ids) > 1:
                    for operation_id in ids:
                        self.add("JAVA_DUPLICATE_METHOD_SIGNATURE", "error", "La firma de la operación está duplicada.", self._target("operacion", operation_id, clasificador_id=entity["id"]), "nombre")
        self._validate_java_relations()

    def _java_name(self, name: str | None, target: dict[str, Any], field: str, style: str) -> None:
        value = (name or "").strip()
        if not value: return
        if not JAVA_IDENTIFIER.fullmatch(value) or value in JAVA_RESERVED:
            self.add("JAVA_INVALID_IDENTIFIER" if value not in JAVA_RESERVED else "JAVA_RESERVED_WORD", "error", "El nombre no es un identificador Java 21 válido.", target, field)
            return
        convention = re.fullmatch(r"[A-Z][A-Za-z0-9]*", value) if style == "classifier" else re.fullmatch(r"[a-z][A-Za-z0-9]*", value)
        if not convention:
            self.add("JAVA_NAMING_CONVENTION", "warning", "El nombre es válido, pero no sigue la convención Java recomendada.", target, field)

    def _java_type(self, type_name: str | None, reference_id: int | None, target: dict[str, Any], field: str, allow_void: bool) -> None:
        if reference_id is not None: return
        value = (type_name or "").strip()
        if value == "void" and allow_void: return
        if value not in JAVA_TYPES:
            self.add("JAVA_UNMAPPABLE_TYPE", "error", "El tipo no tiene una traducción Java conocida.", target, field)

    def _validate_java_relations(self) -> None:
        superclasses = Counter()
        for relation in self.model.get("relations", []):
            source, target = self.entities.get(relation.get("source_id")), self.entities.get(relation.get("target_id"))
            if not source or not target: continue
            rel_target = self._target("relacion", relation["id"])
            if relation.get("type") == Relacion.Tipo.IMPLEMENTACION:
                if source.get("kind") == Entidad.TipoClasificador.INTERFAZ or target.get("kind") != Entidad.TipoClasificador.INTERFAZ:
                    self.add("JAVA_INVALID_INTERFACE_IMPLEMENTATION", "error", "La implementación debe ir de una clase hacia una interfaz.", rel_target)
            elif relation.get("type") == Relacion.Tipo.HERENCIA:
                if source.get("kind") == Entidad.TipoClasificador.INTERFAZ:
                    valid = target.get("kind") == Entidad.TipoClasificador.INTERFAZ
                else:
                    valid = target.get("kind") != Entidad.TipoClasificador.INTERFAZ
                    superclasses[source["id"]] += 1
                if not valid:
                    self.add("JAVA_INVALID_INHERITANCE", "error", "Los extremos de herencia no son compatibles con Java.", rel_target)
        for entity_id, count in superclasses.items():
            if count > 1:
                self.add("JAVA_MULTIPLE_CLASS_INHERITANCE", "error", "Una clase Java solo puede tener una superclase directa.", self._target("clasificador", entity_id))

    def _validate_jpa(self) -> None:
        persistent = {e["id"] for e in self.entities.values() if e.get("kind") == Entidad.TipoClasificador.ENTIDAD_PERSISTENTE}
        for entity_id in persistent:
            entity = self.entities[entity_id]
            keys = [a for a in entity.get("attributes", []) if a.get("is_key")]
            target = self._target("clasificador", entity_id)
            if not keys:
                self.add("JPA_ENTITY_WITHOUT_ID", "error", "La entidad persistente no tiene atributo identificador.", target)
            elif len(keys) > 1:
                self.add("JPA_COMPOSITE_ID_UNSUPPORTED", "error", "El modelo no define una estrategia compatible para una clave compuesta.", target)
            elif keys[0].get("reference_id") is not None or keys[0].get("type") not in {"string", "integer", "long"}:
                self.add("JPA_UNSUPPORTED_ID_TYPE", "error", "7C admite claves simples String, Integer o Long.", self._target("atributo", keys[0]["id"], clasificador_id=entity_id), "tipo")
            for attr in entity.get("attributes", []):
                if attr.get("static"):
                    self.add("JPA_UNSUPPORTED_ATTRIBUTE_TYPE", "error", "Una entidad no puede persistir un atributo UML estático durante 7C.", self._target("atributo", attr["id"], clasificador_id=entity_id), "es_estatico")
                if attr.get("reference_id") is None and attr.get("type") not in JAVA_TYPES:
                    self.add("JPA_UNPERSISTABLE_TYPE", "error", "El atributo no tiene un tipo persistible conocido.", self._target("atributo", attr["id"], clasificador_id=entity_id), "tipo")
        for relation in self.model.get("relations", []):
            target = self._target("relacion", relation["id"])
            if relation.get("type") == Relacion.Tipo.HERENCIA and (
                relation.get("source_id") in persistent or relation.get("target_id") in persistent
            ):
                self.add("JPA_UNSUPPORTED_INHERITANCE", "error", "7C no define una estrategia de herencia para entidades JPA.", target)
                continue
            try:
                analyze_unidirectional_relation(self.entities, relation)
            except JpaPolicyIssue as issue:
                self.add(issue.code, "error", issue.message, target, issue.field)


def validate_project(project: Proyecto, profile: str) -> dict[str, Any]:
    return UMLValidator(extract_project_model(project), profile).validate()
