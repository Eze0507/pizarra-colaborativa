"""Captura autoritativa e inmutable para F24/7A."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from django.db import transaction

from modelado.consistency import (
    StaleRevision,
    read_authoritative_state,
    validate_expected_revision,
)
from modelado.permissions import ProjectAction, require_project_action
from modelado.validation import UMLValidator


MAX_CLASSIFIERS = 500
MAX_RELATIONS = 1000
MAX_ATTRIBUTES = 5000
MAX_OPERATIONS = 5000
MAX_PARAMETERS = 10000
MAX_MEMBERS_PER_CLASSIFIER = 500
MAX_CRUD_ENTITIES = 100


class GenerationValidationError(ValueError):
    code = "generation_validation_failed"

    def __init__(self, details: dict[str, Any]):
        self.details = details
        super().__init__("El modelo no es válido para la generación solicitada.")


class GenerationLimitError(ValueError):
    code = "generation_limit_exceeded"

    def __init__(self, limit: str, maximum: int, actual: int):
        self.details = {"limite": limit, "maximo": maximum, "actual": actual}
        super().__init__(f"El modelo supera el límite de {limit}.")


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return value


def thaw(value: Any) -> Any:
    """Devuelve una copia mutable/serializable sin compartir el contrato interno."""
    if isinstance(value, Mapping):
        return {key: thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw(item) for item in value]
    return deepcopy(value)


@dataclass(frozen=True, slots=True)
class SpringGenerationCapture:
    project_id: int
    project_name: str
    revision: int
    model: Mapping[str, Any]
    validation: Mapping[str, Any]


def _validate_limits(model: dict[str, Any], *, crud_enabled: bool = False) -> None:
    entities = model.get("entities", [])
    entity_kinds = {entity.get("id"): entity.get("kind") for entity in entities}
    relation_field_counts: dict[int, int] = {}
    for relation in model.get("relations", []):
        if relation.get("type") not in {"asociacion", "agregacion", "composicion"}:
            continue
        if (
            entity_kinds.get(relation.get("source_id")) != "entidad_persistente"
            or entity_kinds.get(relation.get("target_id")) != "entidad_persistente"
        ):
            continue
        source_nav = bool(relation.get("source_navigable"))
        target_nav = bool(relation.get("target_navigable"))
        if source_nav == target_nav:
            continue
        owner_id = relation.get("source_id") if target_nav else relation.get("target_id")
        relation_field_counts[owner_id] = relation_field_counts.get(owner_id, 0) + 1
    classifier_count = len(entities)
    crud_entity_count = sum(
        entity.get("kind") == "entidad_persistente" for entity in entities
    )
    relation_count = len(model.get("relations", []))
    if classifier_count > MAX_CLASSIFIERS:
        raise GenerationLimitError("clasificadores", MAX_CLASSIFIERS, classifier_count)
    if relation_count > MAX_RELATIONS:
        raise GenerationLimitError("relaciones", MAX_RELATIONS, relation_count)
    if crud_enabled and crud_entity_count > MAX_CRUD_ENTITIES:
        raise GenerationLimitError(
            "entidades_crud", MAX_CRUD_ENTITIES, crud_entity_count
        )
    attribute_count = sum(len(entity.get("attributes", [])) for entity in entities)
    generated_relation_field_count = sum(relation_field_counts.values())
    operation_count = sum(len(entity.get("operations", [])) for entity in entities)
    parameter_count = sum(
        len(operation.get("parameters", []))
        for entity in entities
        for operation in entity.get("operations", [])
    )
    for limit, maximum, actual in (
        ("atributos", MAX_ATTRIBUTES, attribute_count),
        ("operaciones", MAX_OPERATIONS, operation_count),
        ("parametros", MAX_PARAMETERS, parameter_count),
        ("campos_incluyendo_relaciones", MAX_ATTRIBUTES, attribute_count + generated_relation_field_count),
    ):
        if actual > maximum:
            raise GenerationLimitError(limit, maximum, actual)
    for entity in entities:
        member_count = (
            len(entity.get("attributes", []))
            + len(entity.get("operations", []))
            + relation_field_counts.get(entity.get("id"), 0)
        )
        if member_count > MAX_MEMBERS_PER_CLASSIFIER:
            error = GenerationLimitError(
                "miembros_por_clasificador", MAX_MEMBERS_PER_CLASSIFIER, member_count
            )
            error.details["clasificador_id"] = entity.get("id")
            raise error


def _validate_same_capture(
    model: dict[str, Any], revision: int, *, model_enabled: bool = False,
    crud_enabled: bool = False,
) -> dict[str, Any]:
    profiles: dict[str, Any] = {}
    for profile in ("uml", "java", "jpa"):
        result = UMLValidator(model, profile).validate()
        result["origen"] = "captura_autoritativa"
        result["revision"] = revision
        profiles[profile] = result

    jpa_required = model_enabled and any(
        entity.get("kind") == "entidad_persistente" for entity in model.get("entities", [])
    )
    metadata = {
        "revision_validada": revision,
        "perfiles_evaluados": ["uml", "java", "jpa"],
        "perfiles": profiles,
        "preparacion": {
            "maven_base": profiles["uml"]["valido"] and profiles["java"]["valido"],
            "uml": profiles["uml"]["valido"],
            "java": profiles["java"]["valido"],
            "jpa": profiles["jpa"]["valido"],
            "jpa_requerido": jpa_required,
            "crud": crud_enabled and profiles["jpa"]["valido"],
        },
    }
    if (
        not profiles["uml"]["valido"]
        or not profiles["java"]["valido"]
        or (jpa_required and not profiles["jpa"]["valido"])
    ):
        blocking_profile = (
            "uml" if not profiles["uml"]["valido"]
            else "java" if not profiles["java"]["valido"]
            else "jpa"
        )
        raise GenerationValidationError({
            "perfil": blocking_profile,
            "revision": revision,
            "hallazgos": profiles[blocking_profile]["hallazgos"],
            "perfiles": profiles,
        })
    return metadata


def capture_generation_contract(
    *, project_id: int, expected_revision: Any, user: Any, model_enabled: bool = False,
    crud_enabled: bool = False,
) -> SpringGenerationCapture:
    """Autoriza, captura y valida antes de liberar el bloqueo del proyecto."""
    expected = validate_expected_revision(expected_revision)
    with transaction.atomic():
        state = read_authoritative_state(project_id)
        require_project_action(
            user,
            state.project,
            ProjectAction.EXPORT,
            "No tienes permisos para generar código desde este proyecto.",
        )
        if state.revision != expected:
            raise StaleRevision(state.revision)

        # La copia desacopla la generación de objetos ORM y de modificaciones
        # posteriores. UMLValidator opera solo sobre este DTO.
        model = deepcopy(state.model)
        _validate_limits(model, crud_enabled=crud_enabled)
        validation = _validate_same_capture(
            model, state.revision, model_enabled=model_enabled, crud_enabled=crud_enabled
        )
        return SpringGenerationCapture(
            project_id=state.project.id,
            project_name=str(state.project.nombre),
            revision=state.revision,
            model=_freeze(model),
            validation=_freeze(validation),
        )
