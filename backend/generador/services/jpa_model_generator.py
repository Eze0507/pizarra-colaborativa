"""Planificador inmutable de persistencia para F24/7C."""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from modelado.jpa_policy import JpaPolicyIssue, analyze_unidirectional_relation
from modelado.validation import JAVA_RESERVED


PERSISTENT_KIND = "entidad_persistente"
SUPPORTED_ID_TYPES = frozenset({"string", "integer", "long"})


class JpaGenerationError(ValueError):
    code = "jpa_generation_failed"

    def __init__(self, diagnostics: list[dict[str, Any]]):
        self.details = {"diagnosticos": diagnostics}
        super().__init__("El modelo persistente no puede representarse de forma JPA segura.")


@dataclass(frozen=True, slots=True)
class JpaModelPlan:
    active: bool
    entities: Mapping[int, Mapping[str, Any]]
    relation_fields: Mapping[int, tuple[Mapping[str, Any], ...]]
    metadata: Mapping[str, Any]


def _diagnostic(code: str, message: str, kind: str, object_id: Any, **context: Any):
    return {
        "codigo": code,
        "mensaje": message,
        "objetivo": {"tipo": kind, "id": object_id, **context},
    }


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return value


def plan_jpa_model(model: Mapping[str, Any]) -> JpaModelPlan:
    entities = {entity["id"]: entity for entity in model.get("entities", ())}
    persistent = {
        entity_id: entity for entity_id, entity in entities.items()
        if entity.get("kind") == PERSISTENT_KIND
    }
    if not persistent:
        return JpaModelPlan(False, MappingProxyType({}), MappingProxyType({}), MappingProxyType({
            "active": False,
            "entities": (),
            "relationships": (),
            "unmapped_relationships": (),
        }))

    errors: list[dict[str, Any]] = []
    planned_entities: dict[int, dict[str, Any]] = {}
    for entity_id, entity in sorted(persistent.items()):
        keys = [item for item in entity.get("attributes", ()) if item.get("is_key")]
        if len(keys) != 1:
            code = "JPA_ENTITY_WITHOUT_ID" if not keys else "JPA_COMPOSITE_ID_UNSUPPORTED"
            errors.append(_diagnostic(code, "La entidad necesita exactamente una clave simple.", "clasificador", entity_id))
            continue
        key = keys[0]
        if key.get("reference_id") is not None or key.get("type") not in SUPPORTED_ID_TYPES:
            errors.append(_diagnostic(
                "JPA_UNSUPPORTED_ID_TYPE", "La clave debe ser String, Integer o Long.",
                "atributo", key["id"], clasificador_id=entity_id,
            ))
        for attribute in entity.get("attributes", ()):
            if attribute.get("static"):
                errors.append(_diagnostic(
                    "JPA_UNSUPPORTED_ATTRIBUTE_TYPE", "7C no persiste atributos estáticos.",
                    "atributo", attribute["id"], clasificador_id=entity_id,
                ))
        planned_entities[entity_id] = {
            "entity_id": entity_id,
            "key_attribute_id": key["id"],
            "basic_attribute_ids": tuple(
                item["id"] for item in entity.get("attributes", ())
                if item.get("reference_id") is None
            ),
        }

    relation_fields: dict[int, list[dict[str, Any]]] = {entity_id: [] for entity_id in persistent}
    relationships: list[dict[str, Any]] = []
    unmapped: list[dict[str, Any]] = []
    consumed_reference_attributes: set[int] = set()
    field_names: dict[int, dict[str, tuple[str, int]]] = {
        entity_id: {
            item["name"]: ("atributo", item["id"])
            for item in entity.get("attributes", ())
        }
        for entity_id, entity in persistent.items()
    }

    for relation in sorted(model.get("relations", ()), key=lambda item: item["id"]):
        if relation.get("type") == "herencia" and (
            relation.get("source_id") in persistent or relation.get("target_id") in persistent
        ):
            errors.append(_diagnostic(
                "JPA_UNSUPPORTED_INHERITANCE", "7C no soporta herencia entre entidades persistentes.",
                "relacion", relation["id"],
            ))
            continue
        try:
            planned = analyze_unidirectional_relation(entities, relation)
        except JpaPolicyIssue as issue:
            errors.append(_diagnostic(issue.code, issue.message, "relacion", relation["id"], campo=issue.field))
            continue
        if planned is None:
            if relation.get("type") in {"asociacion", "agregacion", "composicion"}:
                unmapped.append({
                    "relation_id": relation["id"],
                    "relation_type": relation["type"],
                    "reason": "sin_navegabilidad_jpa_inequivoca",
                })
            continue

        owner = persistent[planned["owner_id"]]
        referenced = persistent[planned["referenced_id"]]
        if planned["field_name"] in JAVA_RESERVED:
            errors.append(_diagnostic(
                "JPA_RELATION_MAPPING_AMBIGUOUS", "El rol JPA es una palabra reservada de Java.",
                "relacion", relation["id"],
            ))
            continue
        existing = next(
            (item for item in owner.get("attributes", ()) if item["name"] == planned["field_name"]),
            None,
        )
        reused_attribute_id = None
        if existing is not None:
            if (
                existing.get("reference_id") != referenced["id"]
                or planned["collection"]
                or existing.get("is_key")
                or existing["id"] in consumed_reference_attributes
            ):
                errors.append(_diagnostic(
                    "JPA_FIELD_NAME_COLLISION",
                    "El rol JPA colisiona con un atributo que no representa la misma relación escalar.",
                    "relacion", relation["id"], atributo_id=existing["id"],
                ))
                continue
            reused_attribute_id = existing["id"]
            consumed_reference_attributes.add(existing["id"])
        else:
            previous = field_names[owner["id"]].get(planned["field_name"])
            if previous is not None:
                errors.append(_diagnostic(
                    "JPA_FIELD_NAME_COLLISION", "Dos elementos generan el mismo campo JPA.",
                    "relacion", relation["id"], conflicto_tipo=previous[0], conflicto_id=previous[1],
                ))
                continue
            field_names[owner["id"]][planned["field_name"]] = ("relacion", relation["id"])

        field = {
            **planned,
            "referenced_name": referenced["name"],
            "reused_attribute_id": reused_attribute_id,
            "generated": reused_attribute_id is None,
        }
        relation_fields[owner["id"]].append(field)
        relationships.append(field)

    for entity_id, entity in persistent.items():
        for attribute in entity.get("attributes", ()):
            if attribute.get("reference_id") is not None and attribute["id"] not in consumed_reference_attributes:
                errors.append(_diagnostic(
                    "JPA_UNSUPPORTED_ATTRIBUTE_TYPE",
                    "La referencia tipada no corresponde a una relación JPA unidireccional inequívoca.",
                    "atributo", attribute["id"], clasificador_id=entity_id,
                ))

    for entity_id, fields in relation_fields.items():
        fields.sort(key=lambda item: item["relation_id"])
    if errors:
        errors.sort(key=lambda item: (item["codigo"], item["objetivo"]["tipo"], item["objetivo"]["id"]))
        raise JpaGenerationError(errors)

    entity_metadata = [
        {
            "entity_id": entity_id,
            "key_attribute_id": data["key_attribute_id"],
            "basic_attribute_ids": list(data["basic_attribute_ids"]),
        }
        for entity_id, data in sorted(planned_entities.items())
    ]
    metadata = {
        "active": True,
        "access": "field",
        "supported_id_types": ["string", "integer", "long"],
        "generated_value": False,
        "nullable_policy": "es_nulo_false_genera_nullable_false",
        "collection_policy": "java.util.List_sin_inicializacion",
        "bidirectional_relationships": False,
        "inheritance": "no_soportada_en_7c",
        "entities": entity_metadata,
        "relationships": relationships,
        "unmapped_relationships": unmapped,
        "pending_capabilities": ["herencia_jpa", "relaciones_bidireccionales", "crud", "datasource"],
    }
    return JpaModelPlan(
        True,
        _freeze(planned_entities),
        _freeze({key: tuple(value) for key, value in relation_fields.items()}),
        _freeze(metadata),
    )
