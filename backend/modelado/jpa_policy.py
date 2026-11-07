"""Política pura y determinista para relaciones JPA unidireccionales de F24/7C."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping


PERSISTENT_KIND = "entidad_persistente"
RELATION_KINDS = frozenset({"asociacion", "agregacion", "composicion"})
JAVA_IDENTIFIER = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")


@dataclass(frozen=True, slots=True)
class JpaPolicyIssue(ValueError):
    code: str
    message: str
    field: str | None = None

    def __str__(self) -> str:
        return self.message


def parse_multiplicity(value: str) -> tuple[int, int | None] | None:
    value = (value or "").strip()
    if value == "*":
        return (0, None)
    if re.fullmatch(r"\d+", value):
        number = int(value)
        return (number, number)
    match = re.fullmatch(r"(\d+)\.\.(\d+|\*)", value)
    if not match:
        return None
    return (int(match.group(1)), None if match.group(2) == "*" else int(match.group(2)))


def analyze_unidirectional_relation(
    entities: Mapping[int, Mapping[str, Any]], relation: Mapping[str, Any]
) -> dict[str, Any] | None:
    """Devuelve el contrato JPA o ``None`` cuando UML no solicita navegación."""
    if relation.get("type") not in RELATION_KINDS:
        return None
    source = entities.get(relation.get("source_id"))
    target = entities.get(relation.get("target_id"))
    if source is None or target is None:
        return None  # El perfil UML ya informa extremos inexistentes.

    source_nav = bool(relation.get("source_navigable"))
    target_nav = bool(relation.get("target_navigable"))
    source_persistent = source.get("kind") == PERSISTENT_KIND
    target_persistent = target.get("kind") == PERSISTENT_KIND

    if not source_nav and not target_nav:
        return None
    if source_persistent != target_persistent:
        raise JpaPolicyIssue(
            "JPA_NON_PERSISTENT_RELATION_ENDPOINT",
            "Una relación navegable JPA requiere dos entidades persistentes.",
        )
    if not source_persistent:
        return None
    if source_nav and target_nav:
        raise JpaPolicyIssue(
            "JPA_RELATION_MAPPING_AMBIGUOUS",
            "7C no puede determinar el propietario de una relación bidireccional.",
        )

    # Una flecha hacia el destino representa una propiedad en origen cuyo nombre
    # es el rol del extremo destino. La dirección inversa aplica simétricamente.
    owner_side = "source" if target_nav else "target"
    referenced_side = "target" if target_nav else "source"
    role_key = f"{referenced_side}_role"
    field_name = (relation.get(role_key) or "").strip()
    if not field_name or not JAVA_IDENTIFIER.fullmatch(field_name):
        raise JpaPolicyIssue(
            "JPA_RELATION_MAPPING_AMBIGUOUS",
            "El extremo navegable necesita un rol que sea identificador Java válido.",
            "rol_destino" if referenced_side == "target" else "rol_origen",
        )

    source_mult = parse_multiplicity(relation.get("source_multiplicity", ""))
    target_mult = parse_multiplicity(relation.get("target_multiplicity", ""))
    if source_mult is None or target_mult is None:
        raise JpaPolicyIssue(
            "JPA_RELATION_MAPPING_AMBIGUOUS",
            "La relación JPA necesita multiplicidades válidas en ambos extremos.",
        )
    owner_mult = source_mult if owner_side == "source" else target_mult
    referenced_mult = target_mult if referenced_side == "target" else source_mult
    owner_many = owner_mult[1] is None or owner_mult[1] > 1
    referenced_many = referenced_mult[1] is None or referenced_mult[1] > 1
    if owner_many and referenced_many:
        annotation = "ManyToMany"
    elif owner_many:
        annotation = "ManyToOne"
    elif referenced_many:
        annotation = "OneToMany"
    else:
        annotation = "OneToOne"

    owner = source if owner_side == "source" else target
    referenced = target if referenced_side == "target" else source
    return {
        "relation_id": relation["id"],
        "relation_type": relation["type"],
        "owner_id": owner["id"],
        "referenced_id": referenced["id"],
        "owner_side": owner_side,
        "referenced_side": referenced_side,
        "field_name": field_name,
        "annotation": annotation,
        "collection": referenced_many,
        "nullable": referenced_mult[0] == 0,
        "source_multiplicity": relation.get("source_multiplicity", ""),
        "target_multiplicity": relation.get("target_multiplicity", ""),
        "source_role": relation.get("source_role", ""),
        "target_role": relation.get("target_role", ""),
        "source_navigable": source_nav,
        "target_navigable": target_nav,
    }
