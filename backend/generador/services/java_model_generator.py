"""Transformación determinista del contrato UML de NodoBoard a Java 21."""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from modelado.validation import JAVA_RESERVED, JAVA_TYPES

from .jpa_model_generator import JpaModelPlan


VISIBILITY = {"public": "public", "protected": "protected", "private": "private", "package": ""}
VISIBILITY_RANK = {"private": 0, "package": 1, "protected": 2, "public": 3}
INTEGER_LITERAL = re.compile(r"^[+-]?(?:0|[1-9][0-9]*)$")
DOUBLE_LITERAL = re.compile(r"^[+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$")
WINDOWS_RESERVED = frozenset({
    "con", "prn", "aux", "nul",
    *(f"com{number}" for number in range(1, 10)),
    *(f"lpt{number}" for number in range(1, 10)),
})
RELATION_INHERITANCE = "herencia"
RELATION_IMPLEMENTATION = "implementacion"
KIND_INTERFACE = "interfaz"
KIND_PERSISTENT = "entidad_persistente"


class JavaGenerationError(ValueError):
    code = "java_generation_failed"

    def __init__(self, diagnostics: list[dict[str, Any]]):
        self.details = {"diagnosticos": diagnostics}
        super().__init__("El modelo no puede representarse como Java 21 de forma segura.")


@dataclass(frozen=True, slots=True)
class JavaModelResult:
    files: Mapping[str, str]
    metadata: Mapping[str, Any]


def _diagnostic(code: str, message: str, kind: str, object_id: Any, **context: Any) -> dict[str, Any]:
    return {
        "codigo": code,
        "mensaje": message,
        "objetivo": {"tipo": kind, "id": object_id, **context},
    }


class JavaModelRenderer:
    def __init__(
        self,
        model: Mapping[str, Any],
        base_package: str,
        main_class: str,
        jpa_plan: JpaModelPlan | None = None,
        accessor_attribute_ids: Mapping[int, frozenset[int]] | None = None,
    ):
        self.model = model
        self.base_package = base_package
        self.model_package = f"{base_package}.model"
        self.main_class = main_class
        self.jpa_plan = jpa_plan
        self.accessor_attribute_ids = accessor_attribute_ids or {}
        self.entities = {entity["id"]: entity for entity in model.get("entities", ())}
        self.relations = tuple(model.get("relations", ()))
        self.errors: list[dict[str, Any]] = []
        self.parent: dict[int, int] = {}
        self.interface_parents: dict[int, list[int]] = {}
        self.implemented: dict[int, list[int]] = {}

    def render(self) -> JavaModelResult:
        self._validate_names()
        self._index_relations()
        self._validate_interface_members()
        self._validate_inherited_contracts()
        if self.errors:
            raise JavaGenerationError(self.errors)

        files: dict[str, str] = {}
        classifiers: list[dict[str, Any]] = []
        for entity in sorted(self.entities.values(), key=lambda item: item["id"]):
            content, stubs = self._render_classifier(entity)
            relative = (
                f"src/main/java/{self.model_package.replace('.', '/')}/{entity['name']}.java"
            )
            if len(relative) > 240:
                self.errors.append(_diagnostic(
                    "JAVA_OUTPUT_PATH_COLLISION",
                    "La ruta Java supera el límite seguro de 240 caracteres.",
                    "clasificador", entity["id"],
                ))
                continue
            key = relative.casefold()
            if any(existing.casefold() == key for existing in files):
                self.errors.append(_diagnostic(
                    "JAVA_OUTPUT_PATH_COLLISION",
                    "Dos clasificadores producirían la misma ruta Java.",
                    "clasificador", entity["id"],
                ))
                continue
            files[relative] = content
            classifiers.append({
                "id": entity["id"],
                "nombre_java": entity["name"],
                "tipo_uml": entity["kind"],
                "archivo": relative,
                "abstracto": bool(entity.get("abstract")),
                "persistente_sin_jpa": entity["kind"] == KIND_PERSISTENT,
                "atributos": [item["id"] for item in entity.get("attributes", ())],
                "detalle_atributos": [
                    {
                        "id": item["id"],
                        "orden": item.get("order", 0),
                        "es_clave": bool(item.get("is_key")),
                        "anulable": bool(item.get("nullable")),
                    }
                    for item in entity.get("attributes", ())
                ],
                "operaciones": [item["id"] for item in entity.get("operations", ())],
                "detalle_operaciones": [
                    {
                        "id": item["id"],
                        "orden": item.get("order", 0),
                        "parametros": [
                            {"id": parameter["id"], "orden": parameter.get("order", 0)}
                            for parameter in item.get("parameters", ())
                        ],
                    }
                    for item in entity.get("operations", ())
                ],
                "superclase_id": self.parent.get(entity["id"]),
                "interfaces_ids": sorted(self.implemented.get(entity["id"], ())),
                "stubs_generados": stubs,
            })
        if self.errors:
            raise JavaGenerationError(self.errors)
        mapped_relation_ids = {
            item["relation_id"]
            for fields in (self.jpa_plan.relation_fields.values() if self.jpa_plan else ())
            for item in fields
        }
        pending = [
            {
                "id": relation["id"],
                "tipo": relation["type"],
                "origen_id": relation["source_id"],
                "destino_id": relation["target_id"],
                "multiplicidad_origen": relation.get("source_multiplicity", ""),
                "multiplicidad_destino": relation.get("target_multiplicity", ""),
                "rol_origen": relation.get("source_role", ""),
                "rol_destino": relation.get("target_role", ""),
                "navegable_origen": relation.get("source_navigable"),
                "navegable_destino": relation.get("target_navigable"),
            }
            for relation in self.relations
            if relation.get("type") not in {RELATION_INHERITANCE, RELATION_IMPLEMENTATION}
            and relation["id"] not in mapped_relation_ids
        ]
        metadata = {
            "schema_version": 1,
            "paquete_modelo": self.model_package,
            "clasificadores": classifiers,
            "conteos": {
                "clases": sum(item["tipo_uml"] == "clase" for item in classifiers),
                "entidades_persistentes_sin_jpa": sum(
                    item["tipo_uml"] == KIND_PERSISTENT for item in classifiers
                ),
                "interfaces": sum(item["tipo_uml"] == KIND_INTERFACE for item in classifiers),
                "abstractas": sum(item["abstracto"] for item in classifiers),
                "archivos_java_modelo": len(files),
            },
            "relaciones_pendientes_7c": pending,
            "capacidades_pendientes": (
                ([] if self.jpa_plan and self.jpa_plan.active else ["jpa"])
                + ["repositorios", "servicios", "controladores", "dto"]
            ),
        }
        return JavaModelResult(files=files, metadata=metadata)

    def _validate_names(self) -> None:
        seen: dict[str, int] = {}
        for entity in sorted(self.entities.values(), key=lambda item: item["id"]):
            name = entity.get("name", "")
            folded = name.casefold()
            if folded in seen:
                self.errors.append(_diagnostic(
                    "JAVA_NAME_COLLISION",
                    "Dos clasificadores solo se diferencian por mayúsculas/minúsculas.",
                    "clasificador", entity["id"], otro_clasificador_id=seen[folded],
                ))
            else:
                seen[folded] = entity["id"]
            if folded in WINDOWS_RESERVED:
                self.errors.append(_diagnostic(
                    "JAVA_NAME_COLLISION", "El nombre está reservado en Windows.",
                    "clasificador", entity["id"],
                ))
            if name == self.main_class:
                self.errors.append(_diagnostic(
                    "JAVA_NAME_COLLISION", "El clasificador colisiona con la clase principal.",
                    "clasificador", entity["id"],
                ))

    def _index_relations(self) -> None:
        for relation in sorted(self.relations, key=lambda item: item["id"]):
            source_id, target_id = relation.get("source_id"), relation.get("target_id")
            source, target = self.entities.get(source_id), self.entities.get(target_id)
            if source is None or target is None:
                self.errors.append(_diagnostic(
                    "JAVA_UNRESOLVED_TYPE", "La relación referencia un clasificador inexistente.",
                    "relacion", relation.get("id"),
                ))
                continue
            if relation.get("type") == RELATION_INHERITANCE:
                if source["kind"] == KIND_INTERFACE:
                    self.interface_parents.setdefault(source_id, []).append(target_id)
                else:
                    if source_id in self.parent:
                        self.errors.append(_diagnostic(
                            "JAVA_INCOMPATIBLE_INHERITANCE",
                            "Una clase no puede extender múltiples superclases.",
                            "relacion", relation["id"], clasificador_id=source_id,
                        ))
                    self.parent[source_id] = target_id
            elif relation.get("type") == RELATION_IMPLEMENTATION:
                self.implemented.setdefault(source_id, []).append(target_id)
        for mapping in (self.interface_parents, self.implemented):
            for key in mapping:
                mapping[key] = sorted(set(mapping[key]))

    def _validate_interface_members(self) -> None:
        for entity in self.entities.values():
            if entity.get("kind") != KIND_INTERFACE:
                continue
            if entity.get("attributes"):
                for attribute in entity["attributes"]:
                    self.errors.append(_diagnostic(
                        "JAVA_UNSUPPORTED_INTERFACE_MEMBER",
                        "7B no puede convertir un atributo de interfaz en una constante sin inventar semántica.",
                        "atributo", attribute["id"], clasificador_id=entity["id"],
                    ))
            for operation in entity.get("operations", ()):
                if operation.get("static") or operation.get("visibility", "public") != "public":
                    self.errors.append(_diagnostic(
                        "JAVA_UNSUPPORTED_INTERFACE_MEMBER",
                        "Las operaciones de interfaz de 7B deben ser públicas y no estáticas.",
                        "operacion", operation["id"], clasificador_id=entity["id"],
                    ))

    def _validate_inherited_contracts(self) -> None:
        """Rechaza conflictos Java que F03 no compara entre clasificadores."""
        for entity in self.entities.values():
            entity_id = entity["id"]
            if entity.get("kind") == KIND_INTERFACE:
                contracts: dict[tuple[Any, ...], Mapping[str, Any]] = {}
                operations = list(entity.get("operations", ()))
                for parent_id in self.interface_parents.get(entity_id, ()):
                    operations.extend(self._all_interface_operations(parent_id))
                for operation in operations:
                    signature = self._signature(operation)
                    previous = contracts.get(signature)
                    if previous and self._return_type(previous) != self._return_type(operation):
                        self.errors.append(_diagnostic(
                            "JAVA_INCOMPATIBLE_INHERITANCE",
                            "La interfaz hereda contratos con retornos incompatibles.",
                            "operacion", operation["id"], clasificador_id=entity_id,
                        ))
                    else:
                        contracts.setdefault(signature, operation)
                continue

            inherited: dict[tuple[Any, ...], Mapping[str, Any]] = {}
            current = self.parent.get(entity_id)
            visited: set[int] = set()
            while current is not None and current not in visited:
                visited.add(current)
                for operation in self.entities[current].get("operations", ()):
                    if operation.get("visibility") != "private":
                        inherited.setdefault(self._signature(operation), operation)
                current = self.parent.get(current)
            for operation in entity.get("operations", ()):
                parent_operation = inherited.get(self._signature(operation))
                if parent_operation is None:
                    continue
                incompatible = (
                    bool(operation.get("static")) != bool(parent_operation.get("static"))
                    or self._return_type(operation) != self._return_type(parent_operation)
                    or VISIBILITY_RANK.get(operation.get("visibility", "package"), 0)
                    < VISIBILITY_RANK.get(parent_operation.get("visibility", "package"), 0)
                )
                if incompatible:
                    self.errors.append(_diagnostic(
                        "JAVA_INCOMPATIBLE_INHERITANCE",
                        "La operación redefine un método heredado de forma incompatible.",
                        "operacion", operation["id"], clasificador_id=entity_id,
                    ))

    def _semantic_type(self, member: Mapping[str, Any], type_key: str, reference_key: str) -> tuple[str, Any]:
        reference_id = member.get(reference_key)
        if reference_id is not None:
            return ("reference", reference_id)
        return ("simple", member.get(type_key))

    def _render_type(self, member: Mapping[str, Any], type_key: str, reference_key: str) -> str:
        reference_id = member.get(reference_key)
        if reference_id is not None:
            referenced = self.entities.get(reference_id)
            if referenced is None:
                raise JavaGenerationError([_diagnostic(
                    "JAVA_UNRESOLVED_TYPE", "No se encontró el clasificador referenciado.",
                    "referencia", reference_id,
                )])
            return referenced["name"]
        uml_type = member.get(type_key)
        if uml_type == "void":
            return "void"
        java_type = JAVA_TYPES.get(uml_type)
        if java_type is None:
            raise JavaGenerationError([_diagnostic(
                "JAVA_UNRESOLVED_TYPE", f"No existe mapeo Java para {uml_type!r}.",
                "tipo", member.get("id"),
            )])
        if java_type in {entity["name"] for entity in self.entities.values()}:
            return "java.time.LocalDate" if java_type == "LocalDate" else f"java.lang.{java_type}"
        return java_type

    def _signature(self, operation: Mapping[str, Any]) -> tuple[Any, ...]:
        return (
            operation.get("name"),
            tuple(
                self._semantic_type(parameter, "type", "reference_id")
                for parameter in operation.get("parameters", ())
            ),
        )

    def _return_type(self, operation: Mapping[str, Any]) -> tuple[str, Any]:
        return self._semantic_type(operation, "return_type", "return_reference_id")

    def _all_interface_operations(self, interface_id: int, visited: set[int] | None = None):
        visited = set() if visited is None else visited
        if interface_id in visited:
            return []
        visited.add(interface_id)
        interface = self.entities[interface_id]
        result = list(interface.get("operations", ()))
        for parent_id in self.interface_parents.get(interface_id, ()):
            result.extend(self._all_interface_operations(parent_id, visited))
        return result

    def _required_operations(self, entity_id: int) -> dict[tuple[Any, ...], Mapping[str, Any]]:
        required: dict[tuple[Any, ...], Mapping[str, Any]] = {}

        def add(operation: Mapping[str, Any], source: str, source_id: int):
            enriched = dict(operation)
            enriched["_requirement_source"] = source
            enriched["_requirement_source_id"] = source_id
            signature = self._signature(operation)
            existing = required.get(signature)
            if existing and self._return_type(existing) != self._return_type(operation):
                self.errors.append(_diagnostic(
                    "JAVA_INCOMPATIBLE_INHERITANCE",
                    "Dos contratos heredados tienen retornos incompatibles.",
                    "operacion", operation["id"],
                ))
            else:
                required.setdefault(signature, enriched)

        for interface_id in self.implemented.get(entity_id, ()):
            for operation in self._all_interface_operations(interface_id):
                add(operation, "interfaz", interface_id)
        current = self.parent.get(entity_id)
        visited: set[int] = set()
        while current is not None and current not in visited:
            visited.add(current)
            parent = self.entities[current]
            for operation in parent.get("operations", ()):
                if operation.get("abstract"):
                    add(operation, "superclase", current)
            for interface_id in self.implemented.get(current, ()):
                for operation in self._all_interface_operations(interface_id):
                    add(operation, "interfaz", interface_id)
            current = self.parent.get(current)
        return required

    def _effective_operation(self, entity_id: int, signature: tuple[Any, ...]):
        current = entity_id
        visited: set[int] = set()
        while current is not None and current not in visited:
            visited.add(current)
            entity = self.entities[current]
            for operation in entity.get("operations", ()):
                if self._signature(operation) == signature and operation.get("visibility") != "private":
                    return operation, current
            current = self.parent.get(current)
        return None, None

    def _render_classifier(self, entity: Mapping[str, Any]) -> tuple[str, list[dict[str, Any]]]:
        entity_id = entity["id"]
        is_interface = entity["kind"] == KIND_INTERFACE
        parent_id = self.parent.get(entity_id)
        interface_ids = self.interface_parents.get(entity_id, ()) if is_interface else self.implemented.get(entity_id, ())
        declaration = "public interface" if is_interface else "public " + ("abstract " if entity.get("abstract") else "") + "class"
        suffix: list[str] = []
        if is_interface and interface_ids:
            suffix.append("extends " + ", ".join(self.entities[item]["name"] for item in interface_ids))
        elif not is_interface:
            if parent_id is not None:
                suffix.append("extends " + self.entities[parent_id]["name"])
            if interface_ids:
                suffix.append("implements " + ", ".join(self.entities[item]["name"] for item in interface_ids))

        imports: set[str] = set()
        members: list[str] = []
        jpa_entity = bool(
            self.jpa_plan and self.jpa_plan.active and entity_id in self.jpa_plan.entities
        )
        jpa_entity_plan = self.jpa_plan.entities.get(entity_id, {}) if jpa_entity else {}
        relation_fields = self.jpa_plan.relation_fields.get(entity_id, ()) if jpa_entity else ()
        reused_relations = {
            item["reused_attribute_id"]: item
            for item in relation_fields
            if item.get("reused_attribute_id") is not None
        }
        if jpa_entity:
            imports.add("jakarta.persistence.Entity")
            if jpa_entity_plan.get("inheritance_root"):
                imports.add("jakarta.persistence.Inheritance")
                imports.add("jakarta.persistence.InheritanceType")
            if jpa_entity_plan.get("inheritance_parent_id") is not None:
                imports.add("jakarta.persistence.PrimaryKeyJoinColumn")
        for attribute in entity.get("attributes", ()):
            java_type = self._render_type(attribute, "type", "reference_id")
            if java_type == "LocalDate":
                imports.add("java.time.LocalDate")
            default = self._render_default(attribute, java_type)
            visibility = VISIBILITY.get(attribute.get("visibility", "private"), "private")
            modifiers = " ".join(item for item in (visibility, "static" if attribute.get("static") else "") if item)
            prefix = f"{modifiers} " if modifiers else ""
            if jpa_entity and attribute["id"] == jpa_entity_plan.get("key_attribute_id"):
                imports.add("jakarta.persistence.Id")
                members.append("    @Id")
            elif jpa_entity and attribute["id"] in reused_relations:
                members.extend(self._render_relation_annotations(reused_relations[attribute["id"]], imports))
            elif jpa_entity and attribute.get("reference_id") is None and not attribute.get("nullable"):
                imports.add("jakarta.persistence.Column")
                members.append("    @Column(nullable = false)")
            members.append(f"    {prefix}{java_type} {attribute['name']}{default};")

        for relation_field in relation_fields:
            if not relation_field.get("generated"):
                continue
            members.extend(self._render_relation_annotations(relation_field, imports))
            if relation_field["collection"]:
                imports.add("java.util.List")
                java_type = f"List<{relation_field['referenced_name']}>"
            else:
                java_type = relation_field["referenced_name"]
            members.append(f"    private {java_type} {relation_field['field_name']};")

        accessor_ids = self.accessor_attribute_ids.get(entity_id, frozenset())
        for attribute in entity.get("attributes", ()):
            if attribute["id"] not in accessor_ids:
                continue
            java_type = self._render_type(attribute, "type", "reference_id")
            if java_type == "LocalDate":
                imports.add("java.time.LocalDate")
            suffix_name = attribute["name"][:1].upper() + attribute["name"][1:]
            members.extend([
                f"    public {java_type} get{suffix_name}() {{",
                f"        return this.{attribute['name']};",
                "    }",
                f"    public void set{suffix_name}({java_type} {attribute['name']}) {{",
                f"        this.{attribute['name']} = {attribute['name']};",
                "    }",
            ])

        requirements = {} if is_interface else self._required_operations(entity_id)
        own_signatures = {self._signature(item): item for item in entity.get("operations", ())}
        override_signatures: set[tuple[Any, ...]] = set()
        current = parent_id
        visited: set[int] = set()
        while current is not None and current not in visited:
            visited.add(current)
            for inherited_operation in self.entities[current].get("operations", ()):
                if (
                    inherited_operation.get("visibility") != "private"
                    and not inherited_operation.get("static")
                ):
                    signature = self._signature(inherited_operation)
                    own = own_signatures.get(signature)
                    if own is not None and not own.get("static"):
                        override_signatures.add(signature)
            current = self.parent.get(current)
        stubs: list[dict[str, Any]] = []
        if not is_interface:
            for signature, requirement in requirements.items():
                declared = own_signatures.get(signature)
                required_visibility = "public" if requirement["_requirement_source"] == "interfaz" else requirement.get("visibility", "package")
                if declared is not None and (
                    declared.get("static")
                    or declared.get("abstract")
                    or self._return_type(declared) != self._return_type(requirement)
                    or VISIBILITY_RANK.get(declared.get("visibility", "package"), 0)
                    < VISIBILITY_RANK[required_visibility]
                ):
                    self.errors.append(_diagnostic(
                        "JAVA_INCOMPATIBLE_INHERITANCE",
                        "La operación declarada no implementa de forma compatible el contrato heredado.",
                        "operacion", declared["id"], clasificador_id=entity_id,
                    ))
                    continue
                effective, declaring_id = self._effective_operation(entity_id, signature)
                if effective is not None and not effective.get("abstract"):
                    if self._return_type(effective) != self._return_type(requirement):
                        self.errors.append(_diagnostic(
                            "JAVA_INCOMPATIBLE_INHERITANCE",
                            "El método implementado tiene un retorno incompatible.",
                            "operacion", effective["id"], clasificador_id=entity_id,
                        ))
                    if VISIBILITY_RANK.get(effective.get("visibility", "package"), 0) < VISIBILITY_RANK[required_visibility]:
                        self.errors.append(_diagnostic(
                            "JAVA_INCOMPATIBLE_INHERITANCE",
                            "La implementación reduce la visibilidad del contrato heredado.",
                            "operacion", effective["id"], clasificador_id=entity_id,
                        ))
                    if declaring_id == entity_id:
                        override_signatures.add(signature)
                    continue
                if entity.get("abstract"):
                    continue
                stub = dict(requirement)
                stub["visibility"] = "public" if requirement["_requirement_source"] == "interfaz" else requirement.get("visibility", "protected")
                stub["abstract"] = False
                stub["static"] = False
                stub["_generated_override"] = True
                own_signatures.setdefault(signature, stub)
                stubs.append({
                    "operacion_origen_id": requirement["id"],
                    "origen_tipo": requirement["_requirement_source"],
                    "origen_id": requirement["_requirement_source_id"],
                })

        operations = list(entity.get("operations", ()))
        generated = [operation for signature, operation in own_signatures.items() if operation not in operations]
        operations.extend(sorted(generated, key=lambda item: (item.get("_requirement_source_id", 0), item["id"])))
        for operation in operations:
            return_type = self._render_type(operation, "return_type", "return_reference_id")
            if return_type == "LocalDate":
                imports.add("java.time.LocalDate")
            parameters = []
            for parameter in operation.get("parameters", ()):
                parameter_type = self._render_type(parameter, "type", "reference_id")
                if parameter_type == "LocalDate":
                    imports.add("java.time.LocalDate")
                parameters.append(f"{parameter_type} {parameter['name']}")
            signature_text = f"{return_type} {operation['name']}({', '.join(parameters)})"
            if is_interface:
                members.append(f"    {signature_text};")
                continue
            visibility = VISIBILITY.get(operation.get("visibility", "public"), "public")
            modifiers = [visibility]
            if operation.get("static"):
                modifiers.append("static")
            if operation.get("abstract"):
                modifiers.append("abstract")
            modifier_text = " ".join(item for item in modifiers if item)
            prefix = f"{modifier_text} " if modifier_text else ""
            is_override = operation.get("_generated_override") or self._signature(operation) in override_signatures
            if is_override:
                members.append("    @Override")
            if operation.get("abstract"):
                members.append(f"    {prefix}{signature_text};")
            else:
                members.extend([
                    f"    {prefix}{signature_text} {{",
                    '        throw new UnsupportedOperationException("Operacion pendiente de implementar");',
                    "    }",
                ])

        lines = [f"package {self.model_package};", ""]
        for import_name in sorted(imports):
            lines.append(f"import {import_name};")
        if imports:
            lines.append("")
        if jpa_entity:
            lines.append("@Entity")
            if jpa_entity_plan.get("inheritance_root"):
                lines.append("@Inheritance(strategy = InheritanceType.JOINED)")
            if jpa_entity_plan.get("inheritance_parent_id") is not None:
                root_id = jpa_entity_plan.get("inheritance_root_id")
                root_key_id = jpa_entity_plan.get("key_attribute_id")
                root_key = next(
                    item for item in self.entities[root_id].get("attributes", ())
                    if item["id"] == root_key_id
                )
                lines.append(f'@PrimaryKeyJoinColumn(name = "{root_key["name"]}")')
        lines.append(f"{declaration} {entity['name']}{(' ' + ' '.join(suffix)) if suffix else ''} {{")
        if members:
            lines.append("")
            for index, member in enumerate(members):
                lines.append(member)
                if index < len(members) - 1 and member == "    }":
                    lines.append("")
            lines.append("")
        lines.append("}")
        return "\n".join(lines) + "\n", stubs

    @staticmethod
    def _render_relation_annotations(field: Mapping[str, Any], imports: set[str]) -> list[str]:
        annotation = field["annotation"]
        imports.add(f"jakarta.persistence.{annotation}")
        result = [f"    @{annotation}"]
        if annotation in {"OneToOne", "ManyToOne", "OneToMany"}:
            imports.add("jakarta.persistence.JoinColumn")
            suffix = "(nullable = false)" if not field["nullable"] and not field["collection"] else ""
            result.append(f"    @JoinColumn{suffix}")
        elif annotation == "ManyToMany":
            imports.add("jakarta.persistence.JoinTable")
            result.append("    @JoinTable")
        return result

    def _render_default(self, attribute: Mapping[str, Any], java_type: str) -> str:
        raw = attribute.get("default_value", "")
        if raw == "":
            return ""
        if raw == "null":
            if attribute.get("nullable"):
                return " = null"
            raise JavaGenerationError([_diagnostic(
                "JAVA_INVALID_DEFAULT_VALUE", "null requiere un atributo anulable.",
                "atributo", attribute["id"],
            )])
        if attribute.get("reference_id") is not None:
            raise JavaGenerationError([_diagnostic(
                "JAVA_INVALID_DEFAULT_VALUE", "7B no inicializa referencias internas.",
                "atributo", attribute["id"],
            )])
        uml_type = attribute.get("type")
        try:
            if uml_type == "string":
                return " = " + json.dumps(raw, ensure_ascii=False)
            if uml_type == "integer":
                if not INTEGER_LITERAL.fullmatch(raw) or not -(2**31) <= int(raw) <= 2**31 - 1:
                    raise ValueError
                return f" = {int(raw)}"
            if uml_type == "long":
                if not INTEGER_LITERAL.fullmatch(raw) or not -(2**63) <= int(raw) <= 2**63 - 1:
                    raise ValueError
                return f" = {int(raw)}L"
            if uml_type == "double":
                if not DOUBLE_LITERAL.fullmatch(raw):
                    raise ValueError
                value = Decimal(raw)
                if not value.is_finite() or not math.isfinite(float(value)):
                    raise ValueError
                return f" = {raw}d"
            if uml_type == "boolean":
                if raw not in {"true", "false"}:
                    raise ValueError
                return f" = {raw}"
            if uml_type == "date":
                parsed = date.fromisoformat(raw)
                type_name = "java.time.LocalDate" if java_type == "java.time.LocalDate" else "LocalDate"
                return f" = {type_name}.of({parsed.year}, {parsed.month}, {parsed.day})"
        except (ValueError, InvalidOperation, OverflowError):
            pass
        raise JavaGenerationError([_diagnostic(
            "JAVA_INVALID_DEFAULT_VALUE", "El valor predeterminado no es un literal seguro del tipo declarado.",
            "atributo", attribute["id"],
        )])


def render_java_model(
    model: Mapping[str, Any],
    base_package: str,
    main_class: str,
    jpa_plan: JpaModelPlan | None = None,
    accessor_attribute_ids: Mapping[int, frozenset[int]] | None = None,
) -> JavaModelResult:
    return JavaModelRenderer(
        model, base_package, main_class, jpa_plan, accessor_attribute_ids
    ).render()
