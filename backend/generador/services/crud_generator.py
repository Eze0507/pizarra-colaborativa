"""Planificacion y renderizado determinista de las capas CRUD de F24/7D."""
from __future__ import annotations

from dataclasses import dataclass
import re
from types import MappingProxyType
from typing import Any, Mapping

from .jpa_model_generator import JpaModelPlan


JAVA_TYPE = {
    "string": "String",
    "integer": "Integer",
    "long": "Long",
    "double": "Double",
    "boolean": "Boolean",
    "date": "LocalDate",
}
class CrudGenerationError(ValueError):
    def __init__(self, code: str, message: str, diagnostics: list[dict[str, Any]]):
        self.code = code
        self.details = {"diagnosticos": diagnostics}
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class CrudPlan:
    active: bool
    entities: Mapping[int, Mapping[str, Any]]
    accessor_attribute_ids: Mapping[int, frozenset[int]]
    metadata: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class CrudRenderResult:
    files: Mapping[str, str]
    metadata: Mapping[str, Any]


def _diagnostic(code: str, message: str, entity: Mapping[str, Any], **context: Any):
    return {
        "codigo": code,
        "mensaje": message,
        "objetivo": {
            "tipo": "clasificador",
            "id": entity["id"],
            "nombre": entity["name"],
            **context,
        },
    }


def _method_signature(operation: Mapping[str, Any]) -> tuple[str, tuple[tuple[str, Any], ...]]:
    return (
        operation.get("name", ""),
        tuple(
            ("reference", item.get("reference_id"))
            if item.get("reference_id") is not None
            else ("simple", item.get("type"))
            for item in operation.get("parameters", ())
        ),
    )


def _property_suffix(name: str) -> str:
    return name[:1].upper() + name[1:]


def _rest_route(name: str) -> str:
    """Conserva camelCase y representa los guiones bajos como segmentos REST."""
    route = name[:1].lower() + name[1:]
    return route.replace("_", "-")


def plan_crud(
    model: Mapping[str, Any],
    jpa_plan: JpaModelPlan,
    options: Mapping[str, bool],
) -> CrudPlan:
    requested = any(options.get(name) for name in ("repositorio", "servicio", "controlador"))
    if not requested:
        return CrudPlan(False, MappingProxyType({}), MappingProxyType({}), MappingProxyType({
            "active": False,
            "repositories": (),
            "services": (),
            "controllers": (),
        }))

    entities = {item["id"]: item for item in model.get("entities", ())}
    persistent = {
        entity_id: entities[entity_id]
        for entity_id in sorted(jpa_plan.entities)
    }
    if not persistent:
        raise CrudGenerationError(
            "CRUD_NO_ELIGIBLE_ENTITIES",
            "No existen entidades persistentes elegibles para las capas CRUD.",
            [],
        )

    errors: list[dict[str, Any]] = []
    all_attributes = {
        attribute["id"]: attribute
        for entity in entities.values()
        for attribute in entity.get("attributes", ())
    }
    planned: dict[int, dict[str, Any]] = {}
    generated_names: dict[str, tuple[int, str]] = {}
    classifier_names = {item["name"].casefold(): item["id"] for item in entities.values()}
    routes: dict[str, int] = {}

    for entity_id, entity in persistent.items():
        jpa_entity = jpa_plan.entities[entity_id]
        key = all_attributes[jpa_entity["key_attribute_id"]]
        id_type = JAVA_TYPE.get(key.get("type"))
        if options.get("servicio") and entity.get("abstract"):
            errors.append(_diagnostic(
                "CRUD_UNSUPPORTED_ENTITY",
                "7D no puede crear instancias REST de una entidad persistente abstracta.",
                entity,
            ))
        if id_type not in {"String", "Integer", "Long"}:
            errors.append(_diagnostic(
                "CRUD_INVALID_ID_TYPE", "La clave CRUD debe ser String, Integer o Long.", entity,
                atributo_id=key["id"],
            ))
            continue

        basic = [all_attributes[item_id] for item_id in jpa_entity["basic_attribute_ids"]]
        unsupported = [item for item in basic if item.get("type") not in JAVA_TYPE]
        for item in unsupported:
            errors.append(_diagnostic(
                "CRUD_UNSUPPORTED_ATTRIBUTE_TYPE",
                "El atributo no tiene una representacion REST basica soportada.",
                entity,
                atributo_id=item["id"],
            ))

        relation_fields = tuple(jpa_plan.relation_fields.get(entity_id, ()))
        if options.get("servicio") and relation_fields:
            errors.append(_diagnostic(
                "CRUD_UNSUPPORTED_RELATION_PAYLOAD",
                "7D no genera servicios ni controladores para entidades con relaciones JPA.",
                entity,
                relaciones_ids=sorted(item["relation_id"] for item in relation_fields),
            ))

        route = _rest_route(entity["name"])
        if options.get("controlador") and not re.fullmatch(
            r"[a-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*", route
        ):
            errors.append(_diagnostic(
                "CRUD_UNSUPPORTED_JSON_EXPOSURE",
                "El nombre de la entidad no produce una ruta REST portable.",
                entity,
                ruta=route,
            ))
        previous_route = routes.get(route.casefold())
        if options.get("controlador") and previous_route is not None:
            errors.append(_diagnostic(
                "CRUD_ROUTE_COLLISION", "Dos entidades producirian la misma ruta REST.", entity,
                otro_clasificador_id=previous_route,
            ))
        routes[route.casefold()] = entity_id

        layers = ["Repository"]
        if options.get("servicio"):
            layers.append("Service")
        if options.get("controlador"):
            layers.append("Controller")
        for suffix in layers:
            generated = f"{entity['name']}{suffix}"
            folded = generated.casefold()
            if folded in classifier_names:
                errors.append(_diagnostic(
                    "CRUD_UNSUPPORTED_ENTITY", "Una capa CRUD colisiona con un clasificador UML.",
                    entity, nombre_generado=generated,
                    otro_clasificador_id=classifier_names[folded],
                ))
            if folded in generated_names:
                errors.append(_diagnostic(
                    "CRUD_UNSUPPORTED_ENTITY", "Dos capas CRUD producirian la misma clase Java.",
                    entity, nombre_generado=generated,
                    otro_clasificador_id=generated_names[folded][0],
                ))
            generated_names[folded] = (entity_id, suffix)

        if options.get("servicio"):
            signatures = {_method_signature(item): item for item in entity.get("operations", ())}
            for attribute in basic:
                suffix = _property_suffix(attribute["name"])
                expected = (
                    (f"get{suffix}", ()),
                    (f"set{suffix}", (("simple", attribute.get("type")),)),
                )
                for signature in expected:
                    operation = signatures.get(signature)
                    if operation is not None:
                        errors.append(_diagnostic(
                            "CRUD_METHOD_NAME_COLLISION",
                            "Una operacion UML colisiona con un accesor requerido por CRUD.",
                            entity, atributo_id=attribute["id"], operacion_id=operation["id"],
                            metodo=signature[0],
                        ))

        planned[entity_id] = {
            "entity_id": entity_id,
            "name": entity["name"],
            "route": route,
            "id_attribute_id": key["id"],
            "id_attribute_name": key["name"],
            "id_type": id_type,
            "basic_attributes": tuple(basic),
            "required_attribute_ids": tuple(
                item["id"] for item in basic
                if item["id"] == key["id"] or not item.get("nullable")
            ),
            "has_relationships": bool(relation_fields),
        }

    if errors:
        errors.sort(key=lambda item: (item["codigo"], item["objetivo"]["id"], item["objetivo"].get("atributo_id", 0)))
        raise CrudGenerationError(
            errors[0]["codigo"],
            "El modelo no puede generar todas las capas CRUD solicitadas de forma segura.",
            errors,
        )

    accessor_ids = {
        entity_id: frozenset(item["id"] for item in data["basic_attributes"])
        for entity_id, data in planned.items()
        if options.get("servicio")
    }
    metadata = {
        "active": True,
        "atomic": True,
        "entity_count": len(planned),
        "repositories": [data["name"] for data in planned.values()] if options.get("repositorio") else [],
        "services": [data["name"] for data in planned.values()] if options.get("servicio") else [],
        "controllers": [data["name"] for data in planned.values()] if options.get("controlador") else [],
        "endpoints": [f"/api/{data['route']}" for data in planned.values()] if options.get("controlador") else [],
        "id_types": {data["name"]: data["id_type"] for data in planned.values()},
        "create_policy": "client_supplied_id_duplicate_rejected",
        "update_policy": "path_and_body_id_must_match_basic_fields_only",
        "transaction_policy": "read_only_queries_write_transactions",
        "accessor_policy": "public_get_and_set_for_basic_fields_when_service_enabled",
        "serialization_policy": "direct_entity_only_without_jpa_relationships",
        "relationship_policy": "repository_only_in_7d",
        "validation_status": "generated_and_structurally_validated",
        "pending_capabilities": ["entity_dto", "relationship_crud", "spring_security", "datasource"],
    }
    return CrudPlan(True, MappingProxyType(planned), MappingProxyType(accessor_ids), MappingProxyType(metadata))


def _repository(base: str, data: Mapping[str, Any]) -> str:
    name = data["name"]
    return f"""package {base}.repository;

import {base}.model.{name};
import org.springframework.data.jpa.repository.JpaRepository;

public interface {name}Repository extends JpaRepository<{name}, {data['id_type']}> {{
}}
"""


def _service(base: str, data: Mapping[str, Any]) -> str:
    name = data["name"]
    id_getter = f"get{_property_suffix(data['id_attribute_name'])}"
    required_checks = []
    setters = []
    for attribute in data["basic_attributes"]:
        getter = f"get{_property_suffix(attribute['name'])}"
        setter = f"set{_property_suffix(attribute['name'])}"
        if attribute["id"] in data["required_attribute_ids"]:
            required_checks.extend([
                f"        if (entity.{getter}() == null) {{",
                f'            throw new InvalidRequestException("El atributo {attribute["name"]} es obligatorio.");',
                "        }",
            ])
        if attribute["id"] != data["id_attribute_id"]:
            setters.append(f"        existing.{setter}(input.{getter}());")
    checks = "\n".join(required_checks)
    copies = "\n".join(setters)
    return f"""package {base}.service;

import {base}.exception.InvalidRequestException;
import {base}.exception.ResourceAlreadyExistsException;
import {base}.exception.ResourceNotFoundException;
import {base}.model.{name};
import {base}.repository.{name}Repository;
import java.util.List;
import java.util.Objects;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class {name}Service {{
    private final {name}Repository repository;

    public {name}Service({name}Repository repository) {{
        this.repository = repository;
    }}

    @Transactional
    public {name} create({name} entity) {{
        validateRequired(entity);
        if (repository.existsById(entity.{id_getter}())) {{
            throw new ResourceAlreadyExistsException("{name} ya existe.");
        }}
        return repository.save(entity);
    }}

    @Transactional(readOnly = true)
    public List<{name}> findAll() {{
        return repository.findAll();
    }}

    @Transactional(readOnly = true)
    public {name} findById({data['id_type']} id) {{
        return repository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("{name} no existe."));
    }}

    @Transactional
    public {name} update({data['id_type']} id, {name} input) {{
        if (id == null || input.{id_getter}() == null || !Objects.equals(id, input.{id_getter}())) {{
            throw new InvalidRequestException("La clave de la ruta y del cuerpo debe coincidir.");
        }}
        {name} existing = repository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("{name} no existe."));
{copies}
        validateRequired(existing);
        return repository.save(existing);
    }}

    @Transactional
    public void delete({data['id_type']} id) {{
        if (!repository.existsById(id)) {{
            throw new ResourceNotFoundException("{name} no existe.");
        }}
        repository.deleteById(id);
    }}

    private void validateRequired({name} entity) {{
        if (entity == null) {{
            throw new InvalidRequestException("El cuerpo es obligatorio.");
        }}
{checks}
    }}
}}
"""


def _controller(base: str, data: Mapping[str, Any]) -> str:
    name = data["name"]
    return f"""package {base}.controller;

import {base}.model.{name};
import {base}.service.{name}Service;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/{data['route']}")
public class {name}Controller {{
    private final {name}Service service;

    public {name}Controller({name}Service service) {{
        this.service = service;
    }}

    @PostMapping
    public ResponseEntity<{name}> create(@RequestBody {name} entity) {{
        return ResponseEntity.status(HttpStatus.CREATED).body(service.create(entity));
    }}

    @GetMapping
    public ResponseEntity<List<{name}>> findAll() {{
        return ResponseEntity.ok(service.findAll());
    }}

    @GetMapping("/{{id}}")
    public ResponseEntity<{name}> findById(@PathVariable {data['id_type']} id) {{
        return ResponseEntity.ok(service.findById(id));
    }}

    @PutMapping("/{{id}}")
    public ResponseEntity<{name}> update(@PathVariable {data['id_type']} id, @RequestBody {name} entity) {{
        return ResponseEntity.ok(service.update(id, entity));
    }}

    @DeleteMapping("/{{id}}")
    public ResponseEntity<Void> delete(@PathVariable {data['id_type']} id) {{
        service.delete(id);
        return ResponseEntity.noContent().build();
    }}
}}
"""


def _exception_files(base: str, include_handler: bool) -> dict[str, str]:
    path = f"src/main/java/{base.replace('.', '/')}/exception"
    files: dict[str, str] = {}
    for name in ("InvalidRequestException", "ResourceAlreadyExistsException", "ResourceNotFoundException"):
        files[f"{path}/{name}.java"] = f"""package {base}.exception;

public class {name} extends RuntimeException {{
    public {name}(String message) {{
        super(message);
    }}
}}
"""
    if not include_handler:
        return files
    files[f"{path}/ApiError.java"] = f"""package {base}.exception;

public record ApiError(String code, String message) {{
}}
"""
    files[f"{path}/GlobalExceptionHandler.java"] = f"""package {base}.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

@RestControllerAdvice
public class GlobalExceptionHandler {{
    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ApiError> notFound(ResourceNotFoundException exception) {{
        return response(HttpStatus.NOT_FOUND, "resource_not_found", exception.getMessage());
    }}

    @ExceptionHandler(ResourceAlreadyExistsException.class)
    public ResponseEntity<ApiError> conflict(ResourceAlreadyExistsException exception) {{
        return response(HttpStatus.CONFLICT, "resource_already_exists", exception.getMessage());
    }}

    @ExceptionHandler({{InvalidRequestException.class, MethodArgumentTypeMismatchException.class,
        HttpMessageNotReadableException.class, MethodArgumentNotValidException.class}})
    public ResponseEntity<ApiError> badRequest(Exception exception) {{
        return response(HttpStatus.BAD_REQUEST, "invalid_request", "La solicitud no es valida.");
    }}

    private ResponseEntity<ApiError> response(HttpStatus status, String code, String message) {{
        return ResponseEntity.status(status).body(new ApiError(code, message));
    }}
}}
"""
    return files


def render_crud(base_package: str, plan: CrudPlan, options: Mapping[str, bool]) -> CrudRenderResult:
    if not plan.active:
        return CrudRenderResult(MappingProxyType({}), plan.metadata)
    base_path = f"src/main/java/{base_package.replace('.', '/')}"
    files: dict[str, str] = {}
    for data in plan.entities.values():
        name = data["name"]
        if options.get("repositorio"):
            files[f"{base_path}/repository/{name}Repository.java"] = _repository(base_package, data)
        if options.get("servicio"):
            files[f"{base_path}/service/{name}Service.java"] = _service(base_package, data)
        if options.get("controlador"):
            files[f"{base_path}/controller/{name}Controller.java"] = _controller(base_package, data)
    if options.get("servicio"):
        files.update(_exception_files(base_package, bool(options.get("controlador"))))
    return CrudRenderResult(MappingProxyType(files), plan.metadata)
