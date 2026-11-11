"""Renderizado determinista del proyecto Maven/Spring Boot base de F24/7A."""
from __future__ import annotations

import io
import json
import re
import zipfile
from dataclasses import dataclass
from typing import Mapping
from xml.etree import ElementTree as ET

from modelado.validation import JAVA_RESERVED

from .spring_contract import GenerationLimitError, SpringGenerationCapture, thaw
from .java_model_generator import render_java_model
from .jpa_model_generator import plan_jpa_model
from .crud_generator import plan_crud, render_crud


GENERATOR_VERSION = "0.5.0"
MAVEN_PROJECT_VERSION = "0.0.1-SNAPSHOT"
SPRING_BOOT_VERSION = "3.4.0"
JAVA_VERSION = "21"
MINIMUM_MAVEN_VERSION = "3.9"

MAX_PROJECT_NAME_LENGTH = 64
MAX_PACKAGE_LENGTH = 200
MAX_GENERATED_FILES = 520
MAX_SINGLE_FILE_BYTES = 256 * 1024
MAX_UNCOMPRESSED_BYTES = 8 * 1024 * 1024
MAX_ZIP_BYTES = 4 * 1024 * 1024

ARTIFACT_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
PACKAGE_SEGMENT_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
WINDOWS_RESERVED = frozenset({
    "con", "prn", "aux", "nul",
    *(f"com{number}" for number in range(1, 10)),
    *(f"lpt{number}" for number in range(1, 10)),
})


class InvalidGenerationInput(ValueError):
    code = "invalid_generation_request"

    def __init__(self, field: str, message: str):
        self.details = {"campo": field}
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class MavenCoordinates:
    group_id: str
    artifact_id: str
    base_package: str
    main_class: str
    project_version: str = MAVEN_PROJECT_VERSION


@dataclass(frozen=True, slots=True)
class GeneratedArchive:
    content: bytes
    filename: str
    files: tuple[str, ...]
    coordinates: MavenCoordinates


def build_coordinates(project_name: str, base_package: str) -> MavenCoordinates:
    if not isinstance(project_name, str) or not project_name:
        raise InvalidGenerationInput("nombre_proyecto", "El nombre del proyecto es obligatorio.")
    if len(project_name) > MAX_PROJECT_NAME_LENGTH:
        raise InvalidGenerationInput("nombre_proyecto", "El nombre del proyecto supera 64 caracteres.")
    if project_name != project_name.strip() or not ARTIFACT_PATTERN.fullmatch(project_name):
        raise InvalidGenerationInput(
            "nombre_proyecto",
            "Use minúsculas, números y guiones simples; el nombre debe comenzar con una letra.",
        )
    if project_name.casefold() in WINDOWS_RESERVED:
        raise InvalidGenerationInput("nombre_proyecto", "El nombre está reservado por el sistema operativo.")

    if not isinstance(base_package, str) or not base_package:
        raise InvalidGenerationInput("paquete_base", "El paquete base es obligatorio.")
    if len(base_package) > MAX_PACKAGE_LENGTH or base_package != base_package.strip():
        raise InvalidGenerationInput("paquete_base", "El paquete base es inválido o demasiado largo.")
    segments = base_package.split(".")
    if len(segments) < 2:
        raise InvalidGenerationInput("paquete_base", "El paquete debe contener al menos dos segmentos.")
    for segment in segments:
        if (
            not PACKAGE_SEGMENT_PATTERN.fullmatch(segment)
            or segment in JAVA_RESERVED
            or segment.casefold() in WINDOWS_RESERVED
        ):
            raise InvalidGenerationInput("paquete_base", f"Segmento de paquete inválido: {segment!r}.")

    class_stem = "".join(part[:1].upper() + part[1:] for part in project_name.split("-"))
    return MavenCoordinates(
        group_id=base_package,
        artifact_id=project_name,
        base_package=base_package,
        main_class=f"{class_stem}Application",
    )


def _pom_xml(
    coordinates: MavenCoordinates,
    include_jpa: bool = False,
    include_web: bool = False,
) -> str:
    namespace = "http://maven.apache.org/POM/4.0.0"
    xsi = "http://www.w3.org/2001/XMLSchema-instance"
    ET.register_namespace("", namespace)
    ET.register_namespace("xsi", xsi)
    root = ET.Element(f"{{{namespace}}}project", {
        f"{{{xsi}}}schemaLocation": (
            "http://maven.apache.org/POM/4.0.0 "
            "https://maven.apache.org/xsd/maven-4.0.0.xsd"
        )
    })

    def child(parent, tag: str, text: str | None = None):
        element = ET.SubElement(parent, f"{{{namespace}}}{tag}")
        if text is not None:
            element.text = text
        return element

    child(root, "modelVersion", "4.0.0")
    parent = child(root, "parent")
    child(parent, "groupId", "org.springframework.boot")
    child(parent, "artifactId", "spring-boot-starter-parent")
    child(parent, "version", SPRING_BOOT_VERSION)
    child(parent, "relativePath", "")
    child(root, "groupId", coordinates.group_id)
    child(root, "artifactId", coordinates.artifact_id)
    child(root, "version", coordinates.project_version)
    child(root, "name", coordinates.artifact_id)
    properties = child(root, "properties")
    child(properties, "java.version", JAVA_VERSION)
    dependencies = child(root, "dependencies")
    starter = child(dependencies, "dependency")
    child(starter, "groupId", "org.springframework.boot")
    child(starter, "artifactId", "spring-boot-starter")
    if include_jpa:
        jpa_starter = child(dependencies, "dependency")
        child(jpa_starter, "groupId", "org.springframework.boot")
        child(jpa_starter, "artifactId", "spring-boot-starter-data-jpa")
        postgresql = child(dependencies, "dependency")
        child(postgresql, "groupId", "org.postgresql")
        child(postgresql, "artifactId", "postgresql")
        child(postgresql, "scope", "runtime")
    if include_web:
        web_starter = child(dependencies, "dependency")
        child(web_starter, "groupId", "org.springframework.boot")
        child(web_starter, "artifactId", "spring-boot-starter-web")
    test_starter = child(dependencies, "dependency")
    child(test_starter, "groupId", "org.springframework.boot")
    child(test_starter, "artifactId", "spring-boot-starter-test")
    child(test_starter, "scope", "test")
    build = child(root, "build")
    plugins = child(build, "plugins")
    plugin = child(plugins, "plugin")
    child(plugin, "groupId", "org.springframework.boot")
    child(plugin, "artifactId", "spring-boot-maven-plugin")
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", xml_declaration=True) + "\n"


def _render_files(
    capture: SpringGenerationCapture,
    coordinates: MavenCoordinates,
    options: Mapping[str, bool],
) -> dict[str, str]:
    package_path = coordinates.base_package.replace(".", "/")
    root = coordinates.artifact_id
    main_path = f"{root}/src/main/java/{package_path}/{coordinates.main_class}.java"
    test_path = f"{root}/src/test/java/{package_path}/{coordinates.main_class}Tests.java"
    validation = thaw(capture.validation)
    java_model = None
    jpa_model = None
    jpa_active = False
    crud_plan = None
    crud_model = None
    model_files: dict[str, str] = {}
    if options.get("modelo"):
        jpa_plan = plan_jpa_model(capture.model)
        jpa_active = jpa_plan.active
        crud_plan = plan_crud(capture.model, jpa_plan, options)
        rendered = render_java_model(
            capture.model,
            coordinates.base_package,
            coordinates.main_class,
            jpa_plan,
            crud_plan.accessor_attribute_ids,
        )
        java_model = dict(rendered.metadata)
        jpa_model = thaw(jpa_plan.metadata)
        java_model["capacidades_pendientes"] = [
            capability
            for capability, enabled in (
                ("repositorios", options.get("repositorio")),
                ("servicios", options.get("servicio")),
                ("controladores", options.get("controlador")),
                ("dto", False),
            )
            if not enabled
        ]
        if crud_plan.active:
            jpa_model["pending_capabilities"] = [
                capability
                for capability in jpa_model.get("pending_capabilities", [])
                if capability != "crud"
            ]
        model_files = {f"{root}/{path}": content for path, content in rendered.files.items()}
        crud_rendered = render_crud(coordinates.base_package, crud_plan, options)
        crud_model = thaw(crud_rendered.metadata)
        model_files.update(
            {f"{root}/{path}": content for path, content in crud_rendered.files.items()}
        )
    manifest = {
        "schema_version": 1,
        "generator_version": GENERATOR_VERSION,
        "uml": {
            "project_id": capture.project_id,
            "revision": capture.revision,
            "classifier_count": len(capture.model.get("entities", ())),
            "relation_count": len(capture.model.get("relations", ())),
        },
        "maven": {
            "group_id": coordinates.group_id,
            "artifact_id": coordinates.artifact_id,
            "version": coordinates.project_version,
            "base_package": coordinates.base_package,
            "main_class": coordinates.main_class,
            "java": JAVA_VERSION,
            "spring_boot": SPRING_BOOT_VERSION,
        },
        "options": dict(sorted(options.items())),
        "validation": validation,
        "java_model": java_model,
        "jpa_model": jpa_model,
        "crud": crud_model,
        "postgresql": ({
            "configured": True,
            "dependency": "org.postgresql:postgresql",
            "scope": "runtime",
            "required_environment": ["DB_URL", "DB_USERNAME", "DB_PASSWORD"],
            "optional_environment": {"DB_DDL_AUTO": "validate"},
            "schema_created_automatically": False,
            "real_database_verified": False,
            "persistence_verified": False,
        } if jpa_active else None),
    }
    main_class = f"""package {coordinates.base_package};

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class {coordinates.main_class} {{
    public static void main(String[] args) {{
        SpringApplication.run({coordinates.main_class}.class, args);
    }}
}}
"""
    test_properties = (
        '(properties = "spring.autoconfigure.exclude='
        'org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration")'
        if jpa_active else ""
    )
    test_class = f"""package {coordinates.base_package};

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest{test_properties}
class {coordinates.main_class}Tests {{
    @Test
    void contextLoads() {{
    }}
}}
"""
    model_readme = """
## Modelo UML generado

Los clasificadores UML se encuentran en el paquete `model`. Cuando JPA está activo,
las entidades persistentes incluyen anotaciones Jakarta Persistence. Las operaciones
sin algoritmo incluyen stubs explícitos que lanzan `UnsupportedOperationException`.

Se generan clases, interfaces, abstracción, atributos, operaciones, herencia e
implementación de interfaces. Los tipos simples soportados son `String`, `Integer`,
`Long`, `Double`, `Boolean`, `LocalDate` y `void` solamente como retorno. Los
clasificadores se ordenan por su ID persistente y los miembros respetan su orden UML.
Como F02 no define visibilidad del clasificador, los tipos de nivel superior son públicos.

Los stubs indican firmas pendientes; no contienen algoritmos de negocio. Las
capacidades de persistencia aplicadas o pendientes se detallan en el manifiesto.
Las capas solicitadas se describen en las secciones siguientes.
""" if options.get("modelo") else ""
    jpa_readme = """
## Persistencia JPA de 7C

Las clases `entidad_persistente` incluyen Jakarta Persistence con acceso por campos.
Se admiten claves simples `String`, `Integer` y `Long`, sin `@GeneratedValue`.
`es_nulo=false` produce `@Column(nullable = false)` en atributos básicos no clave.

Solo se generan relaciones unidireccionales con navegabilidad, rol y multiplicidades
inequívocos. Las colecciones usan `List` sin inicialización; no se generan cascadas,
`orphanRemoval` ni `mappedBy`. Las jerarquías persistentes usan
`@Inheritance(strategy = InheritanceType.JOINED)`: la raíz declara la clave y las
subclases la comparten mediante `@PrimaryKeyJoinColumn`. Los nombres de tabla, columna
y claves foráneas quedan a las convenciones de JPA. La prueba de contexto excluye el
DataSource solo en el entorno de prueba; no valida una conexión PostgreSQL real.
""" if jpa_active else ""
    postgresql_readme = f"""
## PostgreSQL

El proyecto incluye el driver PostgreSQL administrado por Spring Boot. No contiene
credenciales ni crea una base de datos. Antes de ejecutar, cree manualmente una base
de desarrollo y un esquema compatible con las entidades generadas.

Configure las variables en PowerShell con valores propios:

```powershell
$env:DB_URL="jdbc:postgresql://localhost:5432/{coordinates.artifact_id}"
$env:DB_USERNAME="usuario_desarrollo"
$env:DB_PASSWORD="<configurar_localmente>"
$env:DB_DDL_AUTO="validate"
```

`DB_URL`, `DB_USERNAME` y `DB_PASSWORD` son obligatorias y no tienen valores por
defecto. `DB_DDL_AUTO` usa `validate` cuando se omite: Hibernate verifica un esquema
existente, pero no crea la base, tablas ni migraciones. No use `create`, `create-drop`
o `update` sin evaluar antes el efecto sobre una base aislada.

Compile con `mvn compile`. Cuando la base y el esquema existan, configure las
variables y ejecute `mvn spring-boot:run`. Estas instrucciones no acreditan arranque,
validacion Hibernate, persistencia ni CRUD real. La API generada no incluye Spring
Security y debe protegerse antes de exponerla fuera de un entorno controlado.
""" if jpa_active else ""
    crud_readme = ""
    if crud_plan and crud_plan.active:
        entities = ", ".join(item["name"] for item in crud_plan.entities.values())
        endpoints = "\n".join(
            f"- `/api/{item['route']}`: POST, GET; `/api/{item['route']}/{{id}}`: GET, PUT, DELETE."
            for item in crud_plan.entities.values()
        ) if options.get("controlador") else "- No se solicitaron controladores."
        crud_readme = f"""
## Capas CRUD de 7D

Entidades incluidas: {entities}.

Los repositorios extienden `JpaRepository`. Los servicios usan inyeccion por
constructor y transacciones Spring. Las claves las proporciona el cliente; no se
genera `@GeneratedValue`. Una clave repetida produce HTTP 409.

PUT exige la misma clave en la ruta y el cuerpo, conserva la identidad y copia
solo atributos basicos. Los campos UML no anulables se comprueban antes de guardar.
Las entidades incluyen getters y setters publicos para los atributos basicos.

### Endpoints

{endpoints}

POST devuelve 201, GET y PUT devuelven 200, y DELETE devuelve 204. Los errores
controlados usan 400, 404 y 409 sin exponer trazas o SQL.

No se generan DTO de entidades, Spring Security, paginacion ni CRUD de relaciones.
Servicios y controladores solo admiten entidades sin relaciones JPA. Configure un
DataSource aislado antes de iniciar la aplicacion o probar persistencia real.

Ejemplo de creacion (adapte los campos a su entidad):

```json
{{"id": 1, "nombre": "Ejemplo"}}
```
"""
    readme = f"""# {coordinates.artifact_id}

Proyecto Maven/Spring Boot generado por NodoBoard F24/7E.

## Descarga y estructura

Este ZIP fue producido desde la opcion **Generacion Java** de NodoBoard usando una
revision UML confirmada. Al descomprimirlo, abra la carpeta `{coordinates.artifact_id}`
en su IDE; contiene `pom.xml`, fuentes en `src`, este README y el manifiesto
`nodoboard-generation.json`.

## Requisitos

- Java {JAVA_VERSION}
- Maven {MINIMUM_MAVEN_VERSION} o posterior
- Spring Boot {SPRING_BOOT_VERSION}

Este artefacto no incluye Maven Wrapper. Use una instalación local de Maven.

## Comandos

```text
mvn test
mvn spring-boot:run
```

Generador NodoBoard: {GENERATOR_VERSION}. Revisión UML confirmada: {capture.revision}.

La aplicación base se genera siempre. El manifiesto registra exactamente las capas
solicitadas y las validaciones aplicadas.
{model_readme}
{jpa_readme}
{crud_readme}
{postgresql_readme}
"""
    application_properties = f"spring.application.name={coordinates.artifact_id}\n"
    if jpa_active:
        application_properties += (
            "spring.datasource.url=${DB_URL}\n"
            "spring.datasource.username=${DB_USERNAME}\n"
            "spring.datasource.password=${DB_PASSWORD}\n"
            "spring.datasource.driver-class-name=org.postgresql.Driver\n"
            "spring.jpa.hibernate.ddl-auto=${DB_DDL_AUTO:validate}\n"
            "spring.jpa.open-in-view=false\n"
        )
    files = {
        f"{root}/pom.xml": _pom_xml(
            coordinates,
            include_jpa=jpa_active,
            include_web=bool(options.get("controlador")),
        ),
        f"{root}/README.md": readme,
        main_path: main_class,
        f"{root}/src/main/resources/application.properties": application_properties,
        test_path: test_class,
        f"{root}/nodoboard-generation.json": json.dumps(
            manifest, ensure_ascii=False, indent=2, sort_keys=True
        ) + "\n",
    }
    files.update(model_files)
    # El conteo incluye el propio manifiesto y permite auditar los límites del ZIP.
    manifest["generated_file_count"] = len(files)
    files[f"{root}/nodoboard-generation.json"] = json.dumps(
        manifest, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n"
    return files


def _deterministic_zip(files: Mapping[str, str]) -> bytes:
    if len(files) > MAX_GENERATED_FILES:
        raise GenerationLimitError("archivos_generados", MAX_GENERATED_FILES, len(files))
    encoded = {name: content.encode("utf-8") for name, content in files.items()}
    for name, content in encoded.items():
        if len(content) > MAX_SINGLE_FILE_BYTES:
            error = GenerationLimitError(
                "archivo_individual_bytes", MAX_SINGLE_FILE_BYTES, len(content)
            )
            error.details["archivo"] = name
            raise error
    total = sum(len(content) for content in encoded.values())
    if total > MAX_UNCOMPRESSED_BYTES:
        raise GenerationLimitError("contenido_generado_bytes", MAX_UNCOMPRESSED_BYTES, total)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(encoded):
            if name.startswith(("/", "\\")) or ".." in name.split("/"):
                raise InvalidGenerationInput("archivo", "Se detectó una ruta ZIP insegura.")
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, encoded[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    payload = buffer.getvalue()
    if len(payload) > MAX_ZIP_BYTES:
        raise GenerationLimitError("zip_bytes", MAX_ZIP_BYTES, len(payload))
    return payload


def generate_spring_boot_base(
    capture: SpringGenerationCapture,
    *,
    project_name: str,
    base_package: str,
    options: Mapping[str, bool],
) -> GeneratedArchive:
    required = (
        ("repositorio", "modelo"),
        ("servicio", "repositorio"),
        ("controlador", "servicio"),
    )
    if any(
        options.get(option) and not options.get(dependency)
        for option, dependency in required
    ):
        raise InvalidGenerationInput(
            "opciones", "Las opciones no respetan sus dependencias."
        )
    coordinates = build_coordinates(project_name, base_package)
    files = _render_files(capture, coordinates, options)
    payload = _deterministic_zip(files)
    return GeneratedArchive(
        content=payload,
        filename=f"{coordinates.artifact_id}.zip",
        files=tuple(sorted(files)),
        coordinates=coordinates,
    )
