"""Contrato común de revisión y lectura autoritativa de NodoBoard."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from django.db import transaction

from .models import Proyecto, Entidad
from .serializers import EntidadDiagramaSerializer, RelacionDiagramaSerializer
from .validation import extract_project_model


class InvalidExpectedRevision(ValueError):
    code = "invalid_expected_revision"


class StaleRevision(ValueError):
    code = "stale_revision"

    def __init__(self, current_revision: int):
        self.current_revision = current_revision
        super().__init__("El diagrama cambió desde tu última sincronización.")


def validate_expected_revision(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise InvalidExpectedRevision(
            "expected_revision es obligatorio y debe ser un entero no negativo."
        )
    return value


def lock_project_for_write(project_id: int, expected_revision: Any) -> Proyecto:
    """Debe invocarse dentro de transaction.atomic()."""
    expected = validate_expected_revision(expected_revision)
    project = Proyecto.objects.select_for_update().get(pk=project_id)
    if project.revision != expected:
        raise StaleRevision(project.revision)
    return project


def reconcile_visual_snapshot(
    raw_snapshot: Any,
    entities: list[dict[str, Any]],
    relations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Conserva visuales conocidos, elimina fantasmas y aplica autoridad ORM."""
    snapshot = deepcopy(raw_snapshot) if isinstance(raw_snapshot, dict) else {}
    entity_by_id = {item["id"]: item for item in entities}
    relation_by_id = {item["id"]: item for item in relations}

    positions = snapshot.get("posiciones")
    if isinstance(positions, dict):
        snapshot["posiciones"] = {
            str(entity_id): {
                **(positions.get(str(entity_id), {}) if isinstance(positions.get(str(entity_id)), dict) else {}),
                "x": entity["coord_x"],
                "y": entity["coord_y"],
            }
            for entity_id, entity in entity_by_id.items()
        }

    visual_entities = snapshot.get("entidades")
    if isinstance(visual_entities, list):
        reconciled = []
        for visual in visual_entities:
            if not isinstance(visual, dict) or visual.get("id") not in entity_by_id:
                continue
            authoritative = entity_by_id[visual["id"]]
            # Los campos desconocidos visuales se conservan, pero toda propiedad
            # estructurada presente en el ORM prevalece, incluidos miembros UML.
            reconciled.append({**visual, **authoritative})
        snapshot["entidades"] = reconciled

    visual_relations = snapshot.get("relaciones")
    if isinstance(visual_relations, list):
        reconciled_relations = []
        semantic_fields = (
            "id", "nombre_relacion", "tipo", "entidad_origen_id", "entidad_destino_id",
            "clase_asociacion_id", "cardinalidad_origen", "cardinalidad_destino",
            "rol_origen", "rol_destino", "navegable_origen", "navegable_destino",
        )
        for visual in visual_relations:
            if not isinstance(visual, dict) or visual.get("id") not in relation_by_id:
                continue
            authoritative = relation_by_id[visual["id"]]
            merged = dict(visual)
            for field in semantic_fields:
                if field in authoritative:
                    merged[field] = authoritative[field]
            reconciled_relations.append(merged)
        snapshot["relaciones"] = reconciled_relations
    return snapshot


@dataclass(frozen=True)
class AuthoritativeState:
    project: Proyecto
    revision: int
    model: dict[str, Any]
    entities: list[dict[str, Any]]
    relations: list[dict[str, Any]]
    visual_snapshot: dict[str, Any]


def read_authoritative_state(project_id: int) -> AuthoritativeState:
    """Lee revisión, ORM y visuales bajo el mismo bloqueo de proyecto.

    Todos los escritores F06 bloquean esta fila. En PostgreSQL esto evita mezclar
    el ORM de una escritura confirmada con el snapshot de otra. SQLite mantiene
    el contrato funcional, pero no acredita concurrencia multiworker real.
    """
    with transaction.atomic():
        project = (
            Proyecto.objects.select_for_update()
            .select_related("propietario")
            .get(pk=project_id)
        )
        entity_qs = (
            project.entidades.exclude(estado=Entidad.Estado.PAPELERA)
            .prefetch_related("atributos", "operaciones__parametros")
            .order_by("id")
        )
        entities = list(EntidadDiagramaSerializer(entity_qs, many=True).data)
        entity_ids = [item["id"] for item in entities]
        relation_qs = project.relaciones.filter(
            entidad_origen_id__in=entity_ids,
            entidad_destino_id__in=entity_ids,
        ).order_by("id")
        relations = list(RelacionDiagramaSerializer(relation_qs, many=True).data)
        model = extract_project_model(project)
        visual = reconcile_visual_snapshot(project.datos_diagrama, entities, relations)
        return AuthoritativeState(project, project.revision, model, entities, relations, visual)
