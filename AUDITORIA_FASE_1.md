# Auditoría integral — Fase 1

Fecha: **30 de octubre de 2026**, America/La_Paz. Auditoría local del contenido de trabajo existente.

## 1. Alcance y evidencia

Se leyó completamente `AUDITORIA_MAESTRA.md` como UTF-8. Se ejecutó únicamente la fase 1 y las pruebas no destructivas necesarias para establecer el estado actual. No se desarrollaron comparaciones detalladas de fases posteriores, matriz comparativa, puntuaciones, prioridades, ranking, selección de módulos ni implementación.

Estados utilizados: **Verificada** significa ejecución de la propiedad concreta descrita, bajo las condiciones registradas; **Parcial** significa código e integración inspeccionados o ejecución de solo parte del flujo; **Pendiente** significa comportamiento no comprobado. **No localizada** indica que no se encontró implementación conectada en los módulos activos, sin afirmar una imposibilidad absoluta. Un test que reproduce un defecto y termina en OK demuestra ese defecto; no convierte el control en seguro.

Se inventariaron los tres repositorios y se revisaron arquitectura, dependencias, modelos, API, consumidores, servicios, componentes, configuración y pruebas. Se analizaron sintácticamente 123 archivos Python originales. La revisión cubre las 25 áreas de fase 1 mediante los registros siguientes. No equivale a inspección manual línea por línea de bibliotecas externas, binarios, recursos visuales o los artefactos Maven de verificaciones anteriores. No se realizó análisis externo de vulnerabilidades de dependencias. Los archivos `.env` no se imprimieron ni se utilizaron en pruebas.

## 2. Repositorios e integridad inicial

Se comprobó existencia física, raíz Git, origin y HEAD; corresponden a las identidades solicitadas.

| Alias | Raíz real | Origin | HEAD |
|---|---|---|---|
| NB | `D:\Informatica\8vo Semestre\sw1-2-2026\pizarra-colaborativa` | `https://github.com/Eze0507/pizarra-colaborativa.git` | `df5430d221ddfbdc23e0a7882e535dc402ceafc4` |
| DB | `D:\swProyecto\backend` | `https://github.com/juanse8202/swbackend.git` | `125dc3b72fed6a829299d5733f31277d0c789a1c` |
| DF | `D:\swProyecto\frontend` | `https://github.com/juanse8202/swfrontend.git` | `e200fc82b2fa6cb3b79e62b5411a6942ccd0cc7a` |

`git status --porcelain=v1 -uall` inicial de NB:

```text
 M frontend/package-lock.json
?? AUDITORIA_MAESTRA.md
?? auditoria-diagramcraft-nodoboard.code-workspace
?? debug.log
```

DB y DF: salida vacía. No se revirtieron cambios previos. El informe no existía al iniciar; su creación final usa modo exclusivo para detenerse si aparece antes de escribirlo.

Git inicialmente rechazó DB/DF por `detected dubious ownership`: usuario sandbox distinto del propietario. Se resolvió exclusivamente en cada consulta mediante `git -c safe.directory=<raíz> --no-optional-locks -C <raíz> ...`. No se cambió configuración Git global/local.

No se encontraron `AGENTS.md` dentro de los repositorios ni en los ancestros relevantes consultados. Se leyó la skill personal `C:/Users/juan/.codex/skills/diagramcraft-ai-uml-platform/SKILL.md` y las instrucciones locales de DiagramCraft en `.agents/skills/` para IA/voz, relaciones, XMI y Spring. Se trataron como contratos esperados, nunca como evidencia de funcionalidad implementada.

## 3. Aislamiento de pruebas

Directorio nuevo y exclusivo, denominado **T** en el resto del informe:

```text
C:\Users\juan\AppData\Local\Temp\nodoboard-audit-52aff2032c65410ea64d503eabc879af
```

Antes de las pruebas se comprobaron estas condiciones:

- Fuentes copiadas a `T/nb`, `T/dc_backend`, `T/dc_frontend`, sin `.env`, `.git`, `.agents`, dist/staticfiles ni repositorios Maven anteriores. Copias originales: 203 archivos NB, 72 DB, 55 DF. node_modules existentes se copiaron físicamente a destinos temporales nuevos; no se enlazaron a originales.
- Django usa `T/django_runner.py`: SQLite de prueba **en memoria**, Channels/caché/correo en memoria, credenciales ficticias, GEMINI_API_KEY vacía y dotenv deshabilitado. Python `-B` evita bytecode. Un audit hook bloquea escrituras fuera de T y red; solo permite los mecanismos internos socketpair/waker de Windows, no proveedores, PostgreSQL, Redis ni SMTP.
- Cada test Django construyó/destruyó su base efímera. Los mensajes Applying migrations corresponden exclusivamente a esa base nueva. No se aplicaron migraciones a bases existentes.
- Cwd, salidas, cachés y perfil de Chrome/Karma se aislaron en T. No se instalaron/actualizaron dependencias, no se usó Docker Compose ni se desplegó. Los runners tienen límites de 60–180 s.
- Se registraron SHA-256 de **1.885 archivos existentes** rastreados o sin seguimiento no ignorados: NB 205, DB 845, DF 835. Incluye archivos previos no copiados a pruebas; no todos los ignorados de node_modules/.venv/cachés. Se contrastan junto con Git al cierre.

Entorno disponible: Node `24.19.0`; Python `DB/.venv/Scripts/python.exe` versión `3.14.7`; Django `6.1.1`, DRF `3.18.0`, Channels `4.3.2`, channels-redis `4.3.0`, SimpleJWT `5.5.1`, lxml `6.1.3`. El alias python.exe del PATH no se pudo ejecutar: acceso al archivo denegado; se utilizó el ejecutable explícito.

**Límite de versiones:** NB declara Django `>=5.2,<5.3`, DRF `3.17.1`, Channels `4.2.2`, google-genai `2.23.0`, psycopg2-binary `2.9.12`. El intérprete disponible es el de DB, difiere en versiones y carece de los dos últimos paquetes. Las pruebas parciales NB no certifican su entorno declarado. DB declara las versiones instaladas, pero su requirements.txt no incluye google-genai aunque el adaptador lo importa. `pip check` pasa: valida distribuciones instaladas, no integridad de los manifiestos de las aplicaciones.

## 4. NodoBoard: arquitectura y registro funcional

Rutas relativas a NB. Django/DRF con apps usuario/modelado/asistente/generador; JWT, Channels, PostgreSQL y Redis configurados. Angular 19 + JointJS 4 + RxJS. `backend/modelado/models.py` contiene Proyecto, Entidad, Atributo y Relacion; `backend/usuario/models.py::UserColaborador` contiene rol/estado. `Proyecto.datos_diagrama` coexiste con tablas normalizadas; `_guardar_snapshot_db` sincroniza ambas representaciones y remapea IDs temporales. Atomicidad individual no equivale a protección frente a estados antiguos.

| Área de fase 1 | Evidencia, integración y dependencias | Estado y límites |
|---|---|---|
| 1. Usuarios/autenticación | `backend/usuario/views.py::{RegisterView,ActivateAccountView,LoginView,LogoutView,BuscarUsuariosView}`; serializers `UserRegisterSerializer`, `CustomTokenObtainPairSerializer`, `LogoutSerializer`. `/api/usuario/{registro,activar,login,logout,token/refresh,buscar}/`. `frontend/.../auth/services/auth.service.ts`, `core/services/token-storage.service.ts`. User, SimpleJWT, firma Django y correo. | **Parcial:** flujo trazado, sin correo/activación/renovación reales. Tokens en localStorage; isAuthenticated frontend comprueba presencia, backend valida JWT. |
| 2. Proyectos/colaboradores | `modelado/views.py::{ProyectoListCreateView,ProyectoDetailView,InvitarColaboradorView,...}`, serializers e invitaciones firmadas. `/api/modelado/proyectos/`, `{id}/`, `invitar/`, `colaboradores/`, `invitaciones/` y aceptar/rechazar. Roles propietario/editor/visualizador; estado pendiente/activo. | **Verificada** restricción DELETE y serializer con 3 tests existentes; **parcial** invitaciones. PATCH visualizador defectuoso, H-N01. |
| 3–5. Diagramas, clases/entidades/atributos y CRUD | `frontend/src/app/features/whiteboard/services/{whiteboard-canvas,whiteboard-entity,whiteboard-relationship}.service.ts`, `pages/whiteboard/whiteboard.page.ts`; `PizarraConsumer.receive/_guardar_snapshot_db`. JointJS, eventos, ORM y snapshot. Carga `/api/modelado/proyectos/{id}/diagrama/`. | **Parcial:** integración seguida y persistencia probada, sin editor en navegador. Modelo activo de entidades/atributos; no acreditado soporte diferenciado class/interface/entity o métodos UML completos. |
| 6. Relaciones/cardinalidades | `modelado/models.py::Relacion.Tipo`: asociación, agregación, composición, herencia; clean/save validan formato. `clase_asociacion` enlaza entidad intermedia; selectores UI y servicios XMI. | **Parcial:** no tests semánticos existentes. No realización/dependencia en enum activo. Regex de cardinalidad no demuestra coherencia de intervalos como 5..2. |
| 7. XMI | `generador/views.py::{ImportarDiagramaXMLView,ExportarDiagramaXMLView}`, `services/xmi_importer.py::XMIImporter.importar_xml`, `xmi_exporter.py::XMIExporter.exportar_xml`, Angular GeneradorService. GET/POST `/api/generador/proyectos/{id}/{exportar-xml,importar-xml}/`; ElementTree, multipart/JSON. | **Verificada** fixture: importó 9 entidades, 33 atributos, 10 relaciones; exportación parseable y reimportación conservó conteos. **Parcial** semántica/layout y EA real. Error bigint H-N05. |
| 8. Generación de código/servicios/apps | Router `generador/urls.py` y servicio Angular conectan solo importación/exportación XML. Paquete_base es metadato. | **No localizada** generación conectada de ZIP/aplicación ejecutable. No se infiere del nombre generador. |
| 9–10. WS/sincronización | `core/asgi.py`, `modelado/{routing,middleware,consumers,realtime}.py`; JwtAuthMiddleware, PizarraConsumer, notificar_evento_proyecto_sync; WhiteboardSocketService. `/ws/pizarra/{id}/?token=...`; debounce snapshot 2 s. Presencia en `_conexiones_por_proyecto`. | **Parcial:** función de persistencia y contratos, sin Redis real/dos clientes. Presencia es memoria por proceso, no acredita consistencia multiworker. |
| 11. Conflictos/concurrencia | Consumer anuncia bloquear/desbloquear y mantiene set por conexión; snapshot transaccional, sin revisión/compare-and-swap/lock de fila observado. | **Verificada** pérdida secuencial por snapshot antiguo, H-N03. Bloqueo visual no acredita exclusión mutua en servidor. |
| 12,14–15. Texto/asistente/operaciones IA | `asistente/views.py::EjecutarInstruccionAsistenteView.post`, `/api/asistente/ejecutar-instruccion/`; Gemini devuelve delta. `AsistenteIaService.ejecutarInstruccion/procesarDelta`, chat y WhiteboardPage.onEjecutarDeltaIA aplican al canvas/WS. | **Parcial por código:** dependencia Google ausente impide check completo. asistente/tests.py no contiene casos; no proveedor real. |
| 13. Voz | AsistenteIaService.iniciarReconocimientoVoz/detenerReconocimientoVoz; chat push-to-talk espacio y texto alternativo. Web Speech español, finales y provisionales acumulados. | **Parcial:** sin micrófono. Al detener puede enviar texto acumulado provisional; no garantiza solo transcripción final. No síntesis speechSynthesis conectada localizada. |
| 16. Validación/confirmación IA | Backend exige autenticación y JSON objeto; listas de delta pasan a cliente, que normaliza y filtra algunos cambios. El prompt pide respetar bloqueos. | **Parcial:** no plan persistido usuario/proyecto/revisión ni validación determinista atómica del lote localizada. Chat emite delta al éxito sin confirmación explícita de borrado localizada. H-N04. |
| 17. Historial/contexto | ChatAsistenteIaComponent.mensajesChat local; limpiarHistorial vacía array. Request lleva instrucción/diagrama sin conversación previa ni identidad de participante. | **Parcial** chat visual; no persistencia/difusión grupal/contexto individual localizados. No acredita seguimientos conceptuales sostenidos. |
| 18. Persistencia | ORM + Proyecto.datos_diagrama, carga inicial y remapeo IDs; migraciones modelado hasta 0011, usuario 0001. | **Verificada** en pruebas SQLite de proyectos/snapshots/XMI; **pendiente** PostgreSQL, locks y migraciones aplicadas en bases existentes. |
| 19–20. Arquitectura/calidad/tests | Features/servicios frontend y apps backend. Prompts/proveedor/parser concentrados en asistente/views.py; sincronización extensa en consumer. 3 tests modelado, asistente placeholder; único spec Angular app.component con 2 casos básicos. | **Verificados** AST de 59 Python y tsc. Sin tests de negocio de voz/editor/IA localizados. No lint configurado en package.json/angular.json. |
| 21. Errores | DRF Response; IA intenta modelos alternativos, devuelve 502 y a veces detalle/raw. Snapshot captura excepción, imprime y retorna exito:false; acuse y toasts. | **Parcial:** sin errores reales de cuota/proveedor; riesgo de detalle sensible y estructura desigual. |
| 22. Estado frontend | RxJS Subjects/BehaviorSubjects, canvas JointJS, mapas de entidades y remapeo tras snapshot. | **Parcial:** TypeScript pasa; sin prueba de múltiples pestañas, reconexión o carrera de autosave. |
| 23. Integración HTTP | Servicios Auth/Projects/Asistente/Generador usan routers reales. environment.ts construye HTTP hostname:8000; socket explícito ws://hostname:8000. | **Parcial:** contratos inspeccionados, HTTPS/WSS/despliegue pendientes. |
| 24. Seguridad endpoints/WS | GET filtra pertenencia; DELETE exige propietario; XML import exige editor/propietario; connect WS JWT+miembro activo. PATCH/snapshot no restringen igual por rol. | **Verificados** defectos H-N01/H-N02. AllowedHostsOriginValidator con hosts wildcard no representa allowlist de origen estricta. |
| 25. Proveedor e imagen | Settings GEMINI_API_KEY/GEMINI_MODEL y candidatos en vistas; GenerarDiagramaDesdeImagenView acepta multipart/base64, `/api/asistente/generar-diagrama-imagen/`, devuelve estructura sin persistir. | **Parcial:** sin imagen/proveedor real. No selector conectado multiproveedor/LLM local. Nombres de modelos no acreditan disponibilidad comercial. |

### Hallazgos NB

**H-N01: visualizador modifica por REST, reproducido.** `backend/modelado/views.py:51::ProyectoDetailView` permite queryset de colaborador activo; solo perform_destroy exige propietario. `ProyectoDetailSerializer` mantiene nombre/descripcion/paquete_base/datos_diagrama escribibles. Sonda `audit_probes.ObservedBehaviorTests.test_reader_can_patch_project_and_snapshot_field`: PATCH de visualizador con nombre y snapshot devolvió 200 y persistió el nombre. No se afirma sincronización automática de tablas normalizadas por este PATCH.

**H-N02: snapshot sin autorización por rol ni revocación en cada escritura, reproducido en rutina.** `modelado/consumers.py:55` valida acceso en connect; receive:387 delega guardar_snapshot a `_guardar_snapshot_db:483`, que busca proyecto por ID sin comprobar usuario/rol/membresía vigente. Sondas con visualizador y miembro eliminado llamaron la función real bajo database_sync_to_async; snapshot vacío devolvió éxito y borró entidades. Se verificó la rutina y se trazó su llamada desde receive; no un handshake WS ofensivo completo.

**H-N03: estado antiguo elimina trabajo posterior, reproducido.** La sonda `test_older_snapshot_can_remove_newer_entities_without_revision` preparó estado vacío, creó una entidad posterior y guardó aquel estado: éxito y cero entidades. La transacción individual no evita esto. La rutina elimina elementos ausentes y recrea atributos; no revisión ni select_for_update. Carreras simultáneas PostgreSQL pendientes.

**H-N04: frontera IA autoritativa incompleta, inspección.** `asistente/views.py:443` usa contexto del cliente y retorna listas del modelo tras validar principalmente JSON/dict. Cliente interpreta/aplica. No plan ligado a usuario/proyecto/revisión ni confirmación destructiva conectada localizada. El prompt no sustituye validación/permisos. No se inventó salida de Gemini.

**H-N05: tipo XMI bigint degradado, reproducido.** `_mapear_tipo_dato` en generador/services/xmi_importer.py comprueba 'int' antes de long/bigint; sonda confirmó bigint→integer. Roundtrip de conteos no certifica semántica. Serializer limita archivo a 10 MB, sin límite equivalente observado para contenido_xml JSON; parser sin límites explícitos de profundidad/elementos. No se ejecutaron cargas hostiles ni se declara explotación XXE.

**H-N06: defaults permisivos y transporte fijo, inspección.** core/settings.py: fallback inseguro de SECRET_KEY, DEBUG por defecto, ALLOWED_HOSTS wildcard, CORS abierto con credenciales. environment.ts/WhiteboardSocketService usan HTTP/WS y puerto fijo; JWT en query puede quedar en logs de infraestructura. No se consultó configuración efectiva de servidores ni se afirma exposición real de una instalación.

## 5. DiagramCraft Backend: arquitectura y registro funcional

Rutas relativas a DB. Django/DRF, sesiones/allauth, PostgreSQL, Channels/Redis; apps proyectos, diagramas y modelador. Autoridad activa del lienzo: `Diagrama.nodes/edges/revision`; subsisten tablas/APIs heredadas ClaseUML, AtributoUML, RelacionUML y VersionDiagrama. No se asumió sincronización de las tablas heredadas con el canvas.

| Área | Evidencia, modelos, rutas y dependencias | Estado y límites |
|---|---|---|
| 1. Usuarios/autenticación | `config/authentication.py::{EmailOrUsernameBackend,CsrfTokenView,CurrentUserView,LoginView,RegistroView,LogoutView}`; `/api/{csrf,me,login,registro,logout}/`, `/accounts/`. Sesiones, CSRF explícito login/registro, SessionAuthentication; allauth Google/GitHub/GitLab. | **Verificada** config.tests 6/6. **Parcial** OAuth y CSRF adversarial; cliente habitual de pruebas no acredita todos los rechazos CSRF. |
| 2. Proyectos/colaboradores | `proyectos/models.py::{Proyecto,ProyectoMiembro,InvitacionProyecto}`, permissions.py::{role_for,require_role,require_owner}, services.py::create_project_with_main_diagram. `/api/proyectos/{proyectos,usuarios,invitaciones}/` y acciones de invitación, archivo/restauración, duplicado, salida, roles, expulsión. Propietario/arquitecto/editor/lector. | **Parcial:** 20 tests existentes: 4 pasan, 15 errores SQLite y 1 fallo por revisión faltante. No se acredita todo el flujo por existencia de endpoints. |
| 3–6. Documento, tipos, miembros/relaciones | `diagramas/views.py::DiagramaViewSet`, `serializers.py::DiagramaSerializer.validate`, `ai_operations.py::execute_operations`, foreign_keys.py::normalize_legacy_foreign_keys. Nodes class/entity/interface, atributos/métodos; seis relaciones y jpaManaged. CRUD JSON `/api/diagramas/diagramas/`; CRUD heredado clases/atributos/relaciones. | **Verificadas** reglas de contrato: extremos/multiplicidades, herencia/ciclos, miembros y JPA en suite diagramas. **Parcial** editor real/documentos no cubiertos. Brecha heredada H-D04. |
| 7. XMI | `diagramas/xmi.py::{parse_xmi,export_xmi,apply_xmi_mapping}`; `/api/diagramas/diagramas/{id}/{importar-xmi,exportar-xmi}/`; class/entity/auto, dry_run, layout/IDs/roles/multiplicidades, FKs/captions. lxml sin entidades/red/DTD y límites 2 MB, 20.000 elementos, profundidad 100. | **Verificados** roundtrip seis relaciones/tipos de nodo, rechazo DTD/duplicados, mapping/layout/rutas. **Pendiente** EA real y dialectos no cubiertos. |
| 8. Generación de código | `diagramas/spring_generator.py::{normalize_diagram,generate_spring_boot_zip}`, UmlNode, Jinja2 StrictUndefined, ZIP en TemporaryDirectory; POST `.../{id}/generar-spring-boot/` desde JSON autorizado. | **Verificadas** estructura/fracciones ZIP, capas CRUD, entity/class/interface, herencia/realización y reglas JPA. **Pendiente** compilación/ejecución Java. Test `generated_java_compiles` inspecciona texto, no ejecuta compilador. |
| 9–11. Colaboración/concurrencia | `consumers.py::{DiagramaConsumer,save_diagram_if_user_can_access,register_presence,active_members}`, realtime.py::publish_diagram_update. `/ws/diagrams/{id}/` y `/ws/diagramas/{id}/`. ORM presencia con actividad/expiración; rol, revisión y select_for_update al guardar; REST/XMI on_commit para publicar. | **Verificados** rechazo de revisión obsoleta sin sobreescritura y revisión REST. **Parcial** Redis/multiworker/reconexión y carreras PostgreSQL: SQLite no reproduce locks de fila. |
| 12,14–15. Diana/texto/operaciones | `ai_interpreter.py::{project_create_proposal,class_create_proposal,GeminiInterpreter,validate_interpret_request,validate_provider_response}`, ai_operations.py::execute_operations y views.py::interpretar_ia. POST `.../{id}/interpretar-ia/`; parser determinista previo a Gemini para algunas creaciones. | **Verificados** interpretación fake/local, aclaración, errores y operaciones incrementales. Parser local no es LLM local. **Pendiente** Gemini real; SDK ausente, H-D02. |
| 16. Planes/seguridad | `ai_plans.py::{create_plan,apply_plan}`, PlanIA con usuario/diagrama/revisión/operaciones/caducidad/hashes/request_id/idempotency_key/resultado; POST `.../{id}/aplicar-plan-ia/`. Servidor recupera operaciones persistidas, valida rol/confirmación y aplica atómicamente. | **Verificados** permisos, rollback, validación, caducidad, conflicto e idempotencia del caso cubierto. Retry con revisión explícita tiene defecto reproducido H-D03. No se certifica idempotencia universal/concurrente. |
| 17. Historial/contexto | PlanIA registra operaciones/resultados; proveedor recibe instrucción, selección y resumen actual, sin hilo grupal. VersionDiagrama ofrece API de snapshots manuales. | **Parcial** contexto de documento/historial operativo. No conversación grupal persistente atribuida ni contexto individual localizados. Planes no equivalen a memoria conversacional. |
| 18. Persistencia | Diagrama JSON/revisión, PlanIA, PresenciaDiagrama, proyectos; migraciones diagramas hasta 0007, proyectos hasta 0005. | **Verificada en SQLite** para casos exitosos; dry-run sin cambios de modelos. **Pendiente** historial aplicado de BD existente y particularidades PostgreSQL. |
| 19–20. Arquitectura/calidad/tests | Intérprete, operaciones puras, planes, serializador, XMI y generador separados. 64 Python sin errores AST. Tests originales: config 6, diagramas 59, proyectos 20. Módulos y suite de contrato extensos; superficie heredada adicional. | **69 pruebas originales pasan, 1 fallo y 15 errores**. No se declara suite verde. |
| 21. Errores | api_errors.py::DiagramApiError, PlanError, OperationError, XmiError, DiagramGenerationError; códigos/revisión/elementos. Logging de metadatos de intérprete. | **Verificados** varios errores estructurados con fake. **Parcial** timeout/cuota/transporte real. |
| 23–24. Integración/seguridad | Cliente usa prefijo real duplicado `/api/diagramas/diagramas/`. JSON revalida permisos en escrituras; ASGI usa AuthMiddlewareStack, sin OriginValidator explícito. Serializers heredados exponen fields='__all__'. | **Verificados** contratos principales y H-D04. **Parcial** protección de origen WS: cookies/SameSite/proxy condicionan riesgo; no prueba cross-site ejecutada. |
| 13,22. Voz/estado frontend | En DF se encuentran implementación de micrófono/TTS y estado de UI. Backend consume instrucción/transcripción. | **Parcial** extremo a extremo; utilidades DF probadas. |
| 25. Proveedor | Settings key/modelo/timeout/max operaciones/TTL; GeminiInterpreter importa Google GenAI perezosamente y llama client.interactions.create. get_ai_provider sustituible por fake. | **Parcial:** sin SDK/proveedor real ni validación de cuota/modelo. No adaptador conectado a LLM local/otro proveedor localizado. |

### Hallazgos DB

**H-D01: prueba de proyecto desalineada con contrato vigente.** `proyectos/tests.py:374::test_diagram_nodes_and_edges_are_persisted_after_patch` envía nodes/edges sin expected_revision y espera 200; `diagramas/views.py:127::perform_update` exige ese dato y responde 400. Fallo real `AssertionError: 400 != 200`. La prueba nueva `diagramas/tests.py:81` exige ese rechazo y pasa. Es incoherencia prueba/contrato; no autoriza eliminar control de concurrencia ni demuestra fallo del cliente actual.

**H-D02: dependencia IA remota no declarada/disponible.** `diagramas/ai_interpreter.py:149::GeminiInterpreter.interpret` importa google.genai. requirements.txt no declara google-genai y metadata no lo encuentra en .venv. Import perezoso permite pasar check/tests fake sin acreditar proveedor. No se hicieron instalaciones ni llamadas con claves reales. Una instalación basada solo en manifiesto no asegura el adaptador.

**H-D03: retry con misma revisión inicial da conflicto, reproducido.** `ai_plans.py:117::apply_plan` compara expected_revision antes de devolver resultado de plan ya aplicado. Sonda `audit_dc_probes.RetryBehaviorTests.test_retry_with_same_expected_revision_returns_conflict`: primer body con revisión 0→200/revisión 1; repetición exacta, misma clave→409 stale_revision. Test original de idempotencia omite revisión y pasa. Cliente `DF/src/components/editor/DiagramCanvas.jsx` sí manda revisión y genera clave al iniciar aplicación. Recuperación UI de respuesta de red perdida pendiente. La sonda no prueba duplicación: prueba que este retry no devuelve el resultado almacenado.

**H-D04: API heredada permite mover clase a diagrama ajeno, reproducido.** `diagramas/serializers.py:12::ClaseUMLSerializer` expone diagrama; `views.py:435::ClaseUMLViewSet.perform_update` valida permiso solo en diagrama original. Sonda `audit_dc_legacy.LegacyAuthorizationTests.test_class_can_be_moved_to_foreign_diagram_without_destination_permission`: dos usuarios/proyectos sintéticos, PATCH `/api/diagramas/clases/{id}/` con ID ajeno→200 y nuevo diagrama_id persistido. Impacto probado: registro heredado escrito en ámbito ajeno, no nodes/edges del canvas. Patrones similares en APIs de atributos/relaciones/versiones requieren prueba específica; no se generaliza automáticamente el resultado.

**H-D05: SQL PostgreSQL impide suite completa SQLite.** `proyectos/views.py:61,66` usa jsonb_array_length. Quince tests fallan `OperationalError: no such function: jsonb_array_length`. No acredita fallo sobre PostgreSQL configurado. No se emuló SQL ni cambió código para forzar tests verdes.

## 6. DiagramCraft Frontend: registro independiente

Rutas relativas a DF. React 19, Vite 8, React Flow, Zustand, Axios y Router. package.json declara reactflow y @xyflow/react; editor usa la biblioteca existente, sin migración.

| Capacidad/área | Implementación e integración | Estado y pruebas |
|---|---|---|
| Usuarios/autenticación (1,23,24) | `src/api/{authApi,axios}.js`, stores/authStore.js, routes/AppRouter.jsx, páginas login/registro. Axios credentials y CSRF en escrituras; utils/runtimeUrls.js. | **Parcial** sesión real/OAuth; runtime URLs probado. Sin suite de login en navegador. |
| Proyectos/colaboradores (2) | pages/ProjectsPage.jsx, components/collaboration/{CollaboratorsDialog,ActiveUsers}.jsx, diálogos de proyectos/personas y api/diagramApi.js. | **Parcial:** API/roles/UI conectados, sin multiusuario ni todos los diálogos ejercitados. |
| Editor UML (3–6) | components/editor/{DiagramCanvas,ClassNode,RelationEdge,PropertiesPanel,EditorToolbar}.jsx; stores/diagramStore.js. Nodes/edges JSON, clases/entidades/interfaces, miembros, relaciones/cardinalidades/JPA. | **Parcial** interacción; build no demuestra cada gesto. Validaciones backend correspondientes sí probadas. |
| XMI/generación (7–8) | api/diagramApi.js, api/xmiApiContract.js, utils/xmiImport.js; callbacks canvas de import/export/generación, descarga binaria, errores y resultado autoritativo. | **Verificadas** utilidades multipart/dry_run, selección/preview/errores; **parcial** descarga real, EA y Java externo. |
| Colaboración/estado (9–11,18,22) | hooks/useDiagramSocket.js, utils/collaborationSync.js y Zustand. invalidatePendingSaves, generaciones/revisión y replaceWithAuthoritativeDocument descartan estados obsoletos y reconocen ecos. | **Verificadas** utilidades puras de generación/revisión/eco; **parcial** eventos reales/reconexión/undo colaborativo. WebSocket no acredita CRDT/OT. |
| IA/confirmación/errores (12,14–16,21) | api/aiApi.js::{interpretAi,applyAiPlan}; DiagramCanvas sincroniza antes de interpretar, invalida autosave, cancela AbortController, comprueba diagrama/solicitud vigente, presenta plan y aplica respuesta autoritativa. utils/aiFlow.js. | **Verificadas** utilidades confirmación/aclaración/error; **parcial** flujo UI/proveedor. VoiceCommand.jsx no aporta lógica activa en el archivo inspeccionado; implementación real reside en DiagramCanvas. |
| Voz/TTS (13) | Canvas usa SpeechRecognition, filtra isFinal/deduplica/activa por nombre, confirma/cancela; speechSynthesis y utils/dianaVoice.js eligen voz, limpian/segmentan texto. | **Verificadas** funciones puras; **pendiente** micrófono/altavoz/permisos/compatibilidad. No se afirma funcionamiento offline. |
| Historial/contexto (17) | addAiHistory/estado local en canvas. Request manda instrucción, selección, revisión, request_id, sin mensajes anteriores. | **Parcial** historial visual; no persistencia/difusión grupal/contexto individual localizados. |
| Calidad/proveedor (19–20,25) | Separación stores/API/utils, pero DiagramCanvas concentra editor/voz/IA/XMI/autosave. Clave Gemini permanece backend. Seis archivos de pruebas Node. | **28 tests, lint y build pasan.** Bundle avisa >500 kB. No tests montados de componentes React/E2E en suite ejecutada. |

## 7. Pruebas: comandos y resultados definitivos

**Forma de comando Django:** `& 'D:\swProyecto\backend\.venv\Scripts\python.exe' -B "$T\django_runner.py" <nb|dc_backend> <args>`. Nunca manage.py contra settings/BD reales. Runners capturan logs y limitan duración. Cwd siempre temporal.

| ID | Comando/verificación | Resultado real |
|---|---|---|
| P01 | prepare.py T: ast.parse de fuentes sin importar app ni emitir bytecode. | 59 Python NB + 64 DB = **123 sin errores sintácticos**. No valida imports/comportamiento. |
| P02 | Python explícito `-B -m pip check`; importlib.metadata.version. | Exit 0, No broken requirements found. Google GenAI/psycopg2-binary ausentes; no garantiza manifiestos completos. |
| P03 | Runner `dc_backend check`, todos los servicios en memoria. | Exit 0, System check identified no issues. |
| P04 | Runner `dc_backend test --noinput -v 2`, fake de proveedor y ZIP/temporales aislados. | Exit 1, **85 tests: 69 pasan, 1 fallo, 15 errores**. Diagramas 59/59; config 6/6; proyectos 4/20. |
| P05 | Runner `dc_backend makemigrations --check --dry-run --noinput`. | Exit 0, No changes detected. Sin escribir migraciones; no informa historial de BD real. |
| P06 | Runner `nb check`, URLconf original. | Exit 1 final: ModuleNotFoundError: No module named 'google' en asistente/views.py:12. Check completo bloqueado. |
| P07 | `$env:AUDIT_NB_SUBSET='1'`; runner `nb test modelado.tests audit_probes --noinput -v 2`, antes de agregar test fixture. URLconf temporal usuario/modelado/generador, Daphne excluido para unidades; no Google falso. | Exit 0, **8/8: tres tests existentes y cinco sondas**. Cuatro sondas reproducen defectos permisos/concurrencia; una bigint. No certifica configuración NB completa. |
| P08 | Subset NB runner `check` y `makemigrations --check --dry-run --noinput`. | Check sin incidencias y No changes detected. Validez parcial por subset/Django distinto. |
| P09 | Subset NB `test audit_probes.XmiFixtureTests --noinput -v 2`, fixture copiada, BD efímera, export/import/parseo. | **1/1 OK**, conteos 9/33/10 en ambas importaciones. No igualdad semántica/layout completa. Pipeline PowerShell mostró exit 1 al tratar stderr nativo, aunque unittest imprimió Ran 1 test / OK; se distinguen ambos resultados. |
| P10 | DB `test audit_dc_probes --noinput -v 2`, sin proveedor. | Exit 0, **1/1 sonda**; retry revisión anterior→409 luego de 200. |
| P11 | DB `test audit_dc_legacy --noinput -v 2`, usuarios/proyectos de prueba. | Exit 0, **1/1 sonda**, traslado heredado a diagrama ajeno aceptado. |
| P12 | En T/dc_frontend: `node --test src/api/xmiApiContract.test.js src/utils/aiFlow.test.js src/utils/dianaVoice.test.js src/utils/collaborationSync.test.js src/utils/runtimeUrls.test.js src/utils/xmiImport.test.js`. Tests puros, sin servicios. | Exit 0, **28 pasan, 0 fallan, 0 omitidos**. |
| P13 | Mismo cwd: `node node_modules/eslint/bin/eslint.js .`, sin --fix/caché. | Exit 0, sin incidencias. |
| P14 | Mismo cwd: `node node_modules/vite/bin/vite.js build`, dependencia y output copiados. | Exit 0, 268 módulos, JS 609,27 kB (gzip 182,72), CSS 56,12 kB. Avisos chunk >500 kB/tiempos plugin. |
| P15 | T/nb/frontend: `node node_modules/@angular/cli/bin/ng.js build`, analytics deshabilitado. | Exit 1: Cannot read directory ../../../../../..: Acceso denegado, luego resolución de CSS/main.ts/zone.js/styles. Bloqueo de entorno; no se atribuyen todos los archivos a errores de código. |
| P16 | Mismo cwd: `node node_modules/@angular/cli/bin/ng.js test --watch=false --browsers=ChromeHeadless`, perfil Karma temporal. | Exit 1: bundles generados, Chrome falla dos veces al iniciar, GPU no utilizable/permisos/caché. Los dos casos Jasmine no quedaron ejecutados exitosamente. |
| P17 | Mismo cwd: `node node_modules/typescript/bin/tsc --noEmit -p tsconfig.app.json`. | Exit 0. TypeScript válido; no acredita templates, bundle producción ni navegador. |

### Intentos fallidos del harness y limitaciones del entorno

- Primer hook impidió sockets internos de asyncio/socketpair. Se permitió exclusivamente ese mecanismo. Primer DB override mezcló MAILERS con EMAIL_BACKEND: se corrigió solo harness temporal a MAILERS locmem para Django 6.1.
- Segundo NB impedía waker Twisted/Daphne; se ajustó solo hook. Check completo final alcanzó la ausencia real de google. Ningún settings original cambió.
- Primer runner frontend: 28 tests pasaron pero imprimir símbolo Unicode de éxito falló por cp1252. Con PYTHONIOENCODING=utf-8 se reejecutó 28/28; no se cuentan como 56 tests diferentes.
- Primera sonda snapshots: tres TypeError coroutine not subscriptable por acceso incorrecto al decorador en código de auditoría. Se corrigió solo sonda usando inspect.getattr_static(...).func; resultado final 8/8. No se tocó el consumidor.
- Fixture XMI primero falló al leerse UTF-8 en byte 0xf1; se releyó Windows-1252, coherente con fallback del serializer, sin modificar fixture. Resultado final OK.
- Warning DB de directorio estático T/static ausente: raíz aislada sin collectstatic, sin invalidar casos exitosos.
- Búsquedas iniciales rg con glob como ruta dieron sintaxis Windows; se continuó buscando directorios con -g, sin deducir ausencia desde error.
- Preparar inicialmente un cuerpo de informe demasiado largo en un único comando PowerShell falló antes de iniciar el proceso (Windows 206). Se dividió la preparación temporal; no creó ni sobrescribió informe en repositorio.

Los 15 errores de P04 son todos `no such function: jsonb_array_length`, en `proyectos.tests.CollaborativeProjectTests`:

```text
test_archive_duplicate_and_filters
test_collaborator_can_leave_but_owner_cannot_leave
test_collaborator_cannot_invite_another_user
test_creator_can_create_project_and_invite_collaborator
test_destroy_cascades_diagrams_members_and_invitations
test_listing_does_not_create_a_personal_workspace
test_owner_can_change_member_role
test_owner_can_resend_or_cancel_a_pending_invitation
test_project_list_counts_react_flow_nodes_and_edges
test_project_list_includes_entity_and_relationship_totals
test_projects_are_isolated_until_an_invitation_is_accepted
test_removed_collaborator_loses_list_and_diagram_write_access
test_restore_cleans_collaborators_from_legacy_archived_project
test_restore_does_not_restore_former_collaborators
test_trash_is_private_and_collaborator_cannot_restore
```

El único fallo de aserción P04 es test_diagram_nodes_and_edges_are_persisted_after_patch, H-D01. Los fallos del harness no se suman a estos resultados definitivos.

### Pruebas omitidas o pendientes

| Comprobación | Motivo |
|---|---|
| NB completo con versiones declaradas | No entorno Python NB compatible disponible; falta google-genai. No se autorizó instalar. Se conserva fallo completo y subset explícito, sin simular proveedor para fingir arranque completo. |
| DB sobre PostgreSQL | Configuración existente podría apuntar a desarrollo. No se conectó ni creó base en instancia existente; no se garantizó servidor efímero independiente. Se documentan errores SQLite sin forzar suite. |
| showmigrations/migrate --plan en bases existentes | Requiere historial real de BD; se evitó cargar credenciales/conectar. Solo coherencia modelos/migraciones mediante --check --dry-run y creación de BD de prueba. Aplicaciones reales pendientes. |
| Redis/dos navegadores/dispositivos/reconexión/carreras | Sin infraestructura extremo a extremo verificada como aislada. Función WS y utilidades puras no certifican sincronización real. |
| Gemini real, imagen, cuota/modelo | Sin uso de claves personales/red/facturación; SDK ausente. Fakes/parsers locales solo acreditan límites que se probaron. |
| Micrófono/TTS/permisos reales | No interacción con dispositivos. Tests de utilidades no sustituyen esa verificación. |
| Enterprise Architect | Sin vuelta manual externa; solo fixtures y procesamiento/roundtrip en código. |
| Compilar/arrancar Java/Maven/Gradle | No se garantizó toolchain/repositorio de dependencias aislado sin descarga. ZIP/texto verificado, compilación no acreditada. |
| Lint NB | No script ni target configurado; no se instalaron/configuraron herramientas. |
| Corregir builds/tests o relajar sandbox | Fuera de alcance. No se cambió código, versiones/contratos/migraciones ni se desactivaron protecciones de navegador. |
| Deploy/AWS/Docker Compose/commits/pushes | Prohibidos por alcance; no ejecutados. |

## 8. Bitácora de inspección y artefactos

Además de los comandos exactos P01–P17 se ejecutaron estas formas de consulta, agrupando las lecturas repetidas por archivo/tramo y búsqueda:

```powershell
Test-Path -LiteralPath <ruta> -PathType Container
Test-Path -LiteralPath <NB\AUDITORIA_FASE_1.md>
git -C <raiz> rev-parse --show-toplevel
git -C <raiz> remote -v
git --no-optional-locks -C <raiz> status --porcelain=v1 -uall
# Tras detectar propiedad diferente; excepción no persistente:
git -c safe.directory=<raiz> --no-optional-locks -C <raiz> status --porcelain=v1 -uall
git -c safe.directory=<raiz> -C <raiz> rev-parse HEAD
git -c safe.directory=<raiz> -C <raiz> ls-files --cached --others --exclude-standard
Get-Content -LiteralPath <archivo> -Raw
Get-Content <archivo> -Encoding UTF8 | Select-Object -First/-Skip/-Last <cantidad>
Get-ChildItem -LiteralPath <raiz> -Force
Get-ChildItem <raiz\.agents> -Recurse -File
rg --files <raiz> -g <patron>
rg --files --hidden -g AGENTS.md -g '!node_modules' -g '!.git' -g '!venv' -g '!.venv' <raiz>
rg -n <patron> <archivos/directorios>
Select-String -LiteralPath <log> -Pattern <resultados/errores>
Get-FileHash -LiteralPath <archivo existente> -Algorithm SHA256
Get-Command python,node,npm -ErrorAction SilentlyContinue
python --version  # alias no ejecutable en sandbox
node --version
& <DB\.venv\Scripts\python.exe> -B -c <versiones con importlib.metadata>
```

Patrones de inspección: clases/funciones, routers/endpoints, roles/permisos, transacciones/revisiones, tests/mocks, efectos de escritura/subprocess/red, XMI/ZIP, contexto/historial, reconocimiento/síntesis, almacenamiento, errores y autosave. Se acompañaron con lectura de flujos relevantes; el maestro se releyó en dos tramos UTF-8. Ancestros AGENTS se verificaron mediante Test-Path. Hubo una búsqueda adicional de AGENTS en D:/Informatica y D:/swProyecto; sin hallazgos reportados. Las consultas son de lectura; no se usó Git para limpiar nada.

Scripts creados solo en T:

- prepare.py, copy_deps.py: fuentes/AST/metadatos y copia física de dependencias.
- django_runner.py, run_backend.py, adjust_harness.py: settings, hook y ejecución Django aislados.
- run_frontend.py, extra_checks.py: tests/lint/build/pip/tsc con timeout.
- prepare_nb_subset.py, run_nb_probes.py, run_fixture_probes.py, run_legacy_probe.py: sondas. audit_nb_urls.py, audit_probes.py, audit_dc_probes.py y audit_dc_legacy.py existen únicamente en copias temporales.
- summarize.py, verify_before_report.py, create_report.py: inventario, hashes y creación exclusiva/verificación final.

Logs principales en T:

```text
dc_backend-check.log
dc_backend-test.log
dc_backend-makemigrations.log
nb-full-check-final.log
nb-subset-check.log
nb-subset-migrations.log
nb-probes-final.log
nb-xmi-fixture-final.log
dc-retry-probe.log
dc-legacy-probe.log
react-test.log
react-lint.log
react-build.log
angular-build.log
angular-test.log
angular-tsc.log
pip-check.log
```

También se conservan logs de intentos iniciales/subsets/fixtures y `attempt1-*`; resúmenes `django-results.json`, `frontend-results.json`, `initial-hashes.json`, `pre-report-verification.json`, `final-verification.json`. Los logs registran rutas/trazas, sin claves de los .env de los repositorios. Su permanencia depende de limpieza habitual de temporales del sistema. El informe contiene resultados suficientes para no depender de leerlos todos.

## 9. Estado comprobado y límites

NodoBoard posee flujos conectados de proyectos, editor de entidades/atributos/relaciones, eventos/snapshots, XMI y asistente con texto/voz/imagen. Se acreditaron tres tests propios de proyectos, persistencia aislada, roundtrip de conteos XMI y TypeScript. Permisos de visualizador y aceptación de snapshots antiguos presentan defectos reproducidos. Proveedor, producción Angular, navegador y colaboración real permanecen parcialmente comprobados o pendientes.

DiagramCraft posee contrato de documento, planes tipados, revisión, operaciones deterministas, XMI y exportación Spring con pruebas ejecutadas. Su suite original no está totalmente verde. La API heredada tiene brecha de autorización reproducida y la idempotencia con revisión explícita tiene un caso no cubierto por el test original. No quedaron certificados proveedor real, PostgreSQL/Redis, compilación Java ni interacción real de editor/voz.

No se encontró evidencia suficiente de un chat grupal persistente que difunda preguntas/respuestas atribuidas y mantenga contexto individual de participantes en ninguno de los sistemas. Es observación del estado actual, no evaluación detallada ni implementación del segundo parcial.

No se decide que un sistema sea globalmente superior ni si corresponde trasladar Diana. Tales decisiones requieren autorización de fases posteriores.

## 10. Integridad y cierre

Antes de crear este informe se recalcularon los 1.885 hashes de línea base: **cero archivos modificados/desaparecidos**. Git coincidía exactamente con estado inicial en los tres repositorios. La verificación siguiente se obtiene con el informe ya creado y excluye únicamente este archivo al contrastar Git.

Comprobación final: **1885 archivos existentes contrastados SHA-256; 0 diferencias**. Estado Git inicial preservado al excluir el informe: **True**.

Estado final `D:\Informatica\8vo Semestre\sw1-2-2026\pizarra-colaborativa`:

```text
 M frontend/package-lock.json
?? AUDITORIA_FASE_1.md
?? AUDITORIA_MAESTRA.md
?? auditoria-diagramcraft-nodoboard.code-workspace
?? debug.log
```

Estado final `D:\swProyecto\backend`:

```text
(limpio)
```

Estado final `D:\swProyecto\frontend`:

```text
(limpio)
```

Única adición en los repositorios: `NB/AUDITORIA_FASE_1.md`. No se implementaron correcciones ni otras fases. **Ejecución detenida al completar la fase 1; continuación sujeta a autorización expresa del usuario.**
