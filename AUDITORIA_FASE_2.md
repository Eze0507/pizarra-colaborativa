# Auditoría — Fase 2: asistentes de inteligencia artificial

Fecha de referencia: **30 de octubre de 2026**, America/La_Paz. Recomendaciones técnicas preliminares; ninguna autoriza implementación.

## A. Resumen ejecutivo

**Conservar y mejorar el asistente actual de NodoBoard es la alternativa preliminar más adecuada. No se justifica incorporar Diana completa ni crear un segundo asistente.** La ventaja comprobada de Diana reside en su frontera de operaciones tipadas, planes persistidos, validación, confirmación y aplicación autoritativa, no en una superioridad demostrada de comprensión o asesoría del modelo. Esos patrones requieren adaptación al dominio de NodoBoard.

NodoBoard conserva una superficie de chat Angular, texto y push-to-talk, el flujo de imagen y una integración con sus entidades/atributos/relaciones. Diana aporta contratos y pruebas para edición segura, pero también defectos documentados de idempotencia y una ventana adicional de revisión reproducida en esta fase. Ninguno implementa el sistema completo de conversación colaborativa atribuido a participantes, memoria grupal/individual, recuperación de diálogos y moderación requerido para el segundo parcial.

No se verificó la inteligencia real de Gemini, exactitud conceptual, comprensión de seguimientos ni calidad de recomendaciones. Se prohibieron y **no se realizaron llamadas reales a proveedores externos**. Las comparaciones de esas capacidades se califican NO VERIFICADO. El parser determinista local de Diana no es un modelo local.

### Alcance, raíces y vigencia

Se leyó la instrucción adjunta completa, AUDITORIA_MAESTRA.md y AUDITORIA_FASE_1.md. Este informe ejecuta únicamente fase 2 y las evaluaciones de integración/segundo parcial solicitadas expresamente para ella. No constituye auditoría comparativa general backend/frontend de fases siguientes. No hay puntuaciones, prioridades, ranking global, migración ni desarrollo.

| Alias | Raíz física verificada | Origin | HEAD |
|---|---|---|---|
| NB | D:/Informatica/8vo Semestre/sw1-2-2026/pizarra-colaborativa | https://github.com/Eze0507/pizarra-colaborativa.git | df5430d221ddfbdc23e0a7882e535dc402ceafc4 |
| DB | D:/swProyecto/backend | https://github.com/juanse8202/swbackend.git | 125dc3b72fed6a829299d5733f31277d0c789a1c |
| DF | D:/swProyecto/frontend | https://github.com/juanse8202/swfrontend.git | e200fc82b2fa6cb3b79e62b5411a6942ccd0cc7a |

Las referencias NB/DB/DF del informe resuelven desde estas raíces, no desde nombres del workspace. Se comprobó que AUDITORIA_FASE_2.md no existía. Se registra Git inicial y se crea el informe en modo exclusivo para evitar sobrescritura.

Estado inicial NB, git status --porcelain=v1 -uall:

```text
 M frontend/package-lock.json
?? AUDITORIA_FASE_1.md
?? AUDITORIA_MAESTRA.md
?? auditoria-diagramcraft-nodoboard.code-workspace
?? debug.log
```

DB y DF: limpios. Se conservaron los cambios previos. Git se consultó con --no-optional-locks y -c safe.directory limitado a cada comando, sin modificar configuración. No se encontraron AGENTS.md en la búsqueda de repositorios. Se aplicó la skill local diagramcraft-ai-uml-platform y se releyeron las instrucciones locales diagramcraft-ai-voice; son contratos esperados, no prueba de implementación.

**Vigencia comprobada:** se recuperó el manifiesto SHA-256 de fase 1 en T1/initial-hashes.json. Sus **1.885 archivos** siguen idénticos, incluidos fuentes, pruebas y manifiestos relevantes de IA. Los tres HEAD coinciden. No hay conclusiones comprometidas por cambios de código. La línea base nueva contiene **1.886 archivos**, agregando el informe de fase 1. SHA-256 actual de ese informe: 9f696d650923ca4b27da9c0d4a4b4215f9b8bda85783f702f6c631326f6d180c.

T1 = C:/Users/juan/AppData/Local/Temp/nodoboard-audit-52aff2032c65410ea64d503eabc879af.

T2 = C:/Users/juan/AppData/Local/Temp/nodoboard-phase2-f46ef03b467846458ffc3c28469ac040.

Se reutilizaron pruebas vigentes sin reejecutar sus suites. La coincidencia de hashes acredita vigencia de fuentes, no certifica cada paquete ignorado de .venv/node_modules ni servicios reales. Los resultados heredados se identifican como históricos, con sus límites originales. Nuevas comprobaciones: siete unidades del handler NB con proveedor simulado y una prueba de revisión durante interpretación DB; motivos y seguridad en K.

### Estados y confianza

- IMPLEMENTADO Y VERIFICADO: evidencia ejecutada de la propiedad concreta; no implica producto entero validado.
- IMPLEMENTADO PARCIALMENTE: solo parte de la capacidad requerida existe o está integrada/verificada.
- NO VERIFICADO: comportamiento identificado en código o dependiente del modelo/dispositivo no ejecutado. Para proveedor real también se indica PENDIENTE DE VERIFICACIÓN.
- NO IMPLEMENTADO: no se encontró flujo/modelo/contrato conectado que realice la capacidad requerida en el alcance inspeccionado.

SUPERIOR/INFERIOR describen una dimensión delimitada; EQUIVALENTE no implica calidad del modelo equivalente. ALTA/MEDIA/BAJA expresan confianza de la conclusión, no una nota ni prioridad.

## B. Diagnóstico de la IA de NodoBoard

### Proveedor y entrada

NB/backend/asistente/views.py:435::EjecutarInstruccionAsistenteView.post sirve POST /api/asistente/ejecutar-instruccion/, registrado en asistente/urls.py. Exige IsAuthenticated y JSONParser; recibe instruccion o comando y contexto_diagrama. No recibe un ID autoritativo de proyecto ni revisión. Google GenAI se importa al cargar el módulo (líneas 12–14). core/settings.py:198 configura GEMINI_API_KEY y GEMINI_MODEL, con nombre por defecto gemini-3.8-flash. La vista intenta además gemini-flash-latest, gemini-3.6-flash y gemini-3.5-flash-lite. Son literales del código; disponibilidad/latencia/calidad reales **NO VERIFICADAS**.

El cliente usa client.models.generate_content, JSON MIME, temperatura 0.1 y SYSTEM_PROMPT_INSTRUCCIONES. No hay adaptador seleccionable de proveedor ni un LLM local conectado. NB/backend/requirements.txt sí declara google-genai==2.23.0. El intérprete disponible de fase 1 carecía del SDK y el check completo NB falló en import; ese resultado sigue siendo límite de integración, no una prueba de indisponibilidad de Gemini en todas las instalaciones.

### Contexto y transformación de instrucciones

NB/frontend/src/app/features/whiteboard/services/asistente-ia.service.ts:735::extraerContextoDiagrama extrae IDs numéricos, nombre, estado, atributos y extremos/tipo/nombre de relaciones. Se vuelve a filtrar en views.py:458. **No incluye cardinalidades existentes, historial ni identidad del participante.** La sonda adicional confirma que esos datos no llegan al contenido del proveedor, aunque se añadan campos usuario/historial al request simulado.

SYSTEM_PROMPT_INSTRUCCIONES:301 define seis listas: entidades_a_crear/modificar/eliminar y relaciones_a_crear/eliminar, más mensaje. Pide renombrar entidades, agregar/cambiar/quitar atributos, crear relaciones con multiplicidad y construir clases de asociación para muchos-a-muchos. Limita tipos de atributo a string/integer/long/double/boolean/date; relaciones normales a asociación/agregación/composición/herencia. Es una política de modelado relacional que debe conservarse o revisarse deliberadamente; no equivale al dominio Java/JPA de Diana.

AsistenteIaService:845::procesarDelta convierte la respuesta a objetos del editor: IDs temporales, normalización de nombres/tipos/cardinalidades, clave primaria automática, resolución por ID o nombre, filtrado de bloqueados y upsert de atributos por nombre. Omite modificaciones cuyo destino no resuelve; puede construir la clase de asociación automáticamente. Estas defensas locales son código identificado, **NO VERIFICADO funcionalmente en navegador**. Los nombres duplicados pueden resolverse por el mapa/primera coincidencia sin una aclaración al usuario. No se localizó operación específica de actualizar relación existente; el contrato ofrece crear/eliminar relaciones.

### Ejecución, validación y autorización

NB/.../pages/whiteboard/whiteboard.page.ts:631::onEjecutarDeltaIA recorre el resultado, modifica JointJS, emite eventos individuales por WhiteboardSocketService y programa un snapshot. La respuesta del asistente no constituye una transacción autorizada del backend. El tipo TypeScript no valida el JSON recibido en runtime.

views.py:542 recupera JSON, incluso entre primeras/últimas llaves; exige dict, pero no valida tipos/semántica de cada lista. **Sonda nueva:** entidades_a_crear='invalid-list' produce 200 y devuelve esa cadena. El handler admite JSON incompleto y completa campos ausentes con []. La clave/falta de instrucción se controlan; no hay esquema estricto del lote, plan persistido ni revisión de diagrama.

ChatAsistenteIaComponent:229::manejarExitoInstruccion muestra el mensaje y emite ejecutarDeltaIA inmediatamente. No se localizó preview/confirmación de plan destructivo IA. Algunas confirmaciones manuales del editor no son confirmaciones del flujo IA.

Se conservan H-N01/H-N02/H-N03 de fase 1: visualizador con PATCH autorizado indebidamente, rutina de snapshot sin revalidar rol/membresía y aceptación de snapshots antiguos que borran trabajo posterior. Su reproducción fue en BD aislada; no un ataque WS real de extremo a extremo. El endpoint IA solo acredita identidad autenticada; no que el modelo conozca al participante ni que pueda modificar ese proyecto concreto. La escritura posterior debe imponer permisos y estado autoritativo en cualquier mejora futura.

### Errores, voz y experiencia de chat

Handler: clave ausente→500, instrucción vacía→400, modelos candidatos agotados→502, JSON inválido→500 con raw; también devuelve detalles del último error. Hay logging de excepciones del proveedor. Estas categorías se comprobaron en unidades simuladas; fallos reales de red/cuota siguen pendientes. El cliente convierte error.error en mensaje y toast, sin contrato común de código/elemento/revisión.

AsistenteIaService:113 inicia SpeechRecognition/webkitSpeechRecognition en es-ES, continuo con interimResults=true. Acumula texto final y provisional. detenerReconocimientoVoz:182 elimina callbacks, detiene y devuelve lo acumulado. ChatAsistenteIaComponent usa mantener/soltar espacio y botón para hablar/enviar; fallback escrito y errores de permiso. El envío puede incluir parcial; textoVozFinal$ es un nombre de canal, no una garantía de que isFinal haya sido verdadero. No se encontró síntesis conectada. Micrófono/UX real: **NO VERIFICADO**.

ChatAsistenteIaComponent:46 conserva mensajesChat en memoria, fecha y remitente usuario/asistente; HTML muestra Tú/Asistente. limpiarHistorial:215 vacía el array. No backend de conversaciones: asistente/models.py y tests.py son placeholders. No se envían mensajes anteriores al proveedor ni preguntas/respuestas por WS. La señal cargandoInstruccion evita envíos simultáneos locales, pero no constituye idempotencia persistida ni deduplicación de reintentos.

### Consultas sin mutación y entrada por imagen

El prompt en views.py:430 permite dudas conceptuales/saludos devolviendo mensaje y listas vacías. **Nueva unidad verificada:** una respuesta conceptual simulada se devuelve con seis listas vacías. Eso demuestra transporte, no exactitud conceptual ni seguridad frente a un modelo que mezcle explicación con mutaciones. El padre programa snapshot incluso para delta vacío; no existe un modo separado de consulta de solo lectura. Calidad conceptual/seguimientos: **PENDIENTE DE VERIFICACIÓN**, sin llamar al proveedor.

GenerarDiagramaDesdeImagenView:158 y /api/asistente/generar-diagrama-imagen/ están conectados con AsistenteIaService.generarDiagramaDesdeImagen, compresión/normalización y WhiteboardPage.onDiagramaIAGenerado. Es una capacidad existente por código que conviene conservar como entrada distinta de la edición incremental; procesamiento real de imagen **NO VERIFICADO**. No se deduce éxito por existir el endpoint.

Fortalezas actuales: integración nativa Angular/JointJS, flujo único de chat, texto/push-to-talk, política relacional y entrada por imagen. Límites: dependencia del cliente para ejecutar/normalizar, poca cobertura IA propia, falta de contexto conversacional/atribución grupal y fronteras de autorización/concurrencia defectuosas.

## C. Diagnóstico de Diana

### Interpretación y contratos

DB/diagramas/views.py:186::DiagramaViewSet.interpretar_ia atiende POST /api/diagramas/diagramas/{id}/interpretar-ia/. Obtiene diagrama desde queryset autorizado y exige EDIT_ROLES: propietario/arquitecto/editor. Un lector no puede usar este endpoint siquiera para una pregunta conceptual. DB/diagramas/ai_interpreter.py:225::validate_interpret_request exige instruction no vacía hasta 2.000 caracteres, selection con IDs existentes/no repetidos y campos permitidos; revisión/request_id opcionales validados.

project_create_proposal:36 y class_create_proposal:68 reconocen gramáticas acotadas en español, creando propuestas sin proveedor; hay tests vigentes para proyectos, class/entity/interface y atributos. No equivalen a comprensión general ni a inferencia de un modelo local. GeminiInterpreter:141 es una factory/adaptador separado, usa variables de entorno, modelo por defecto gemini-2.5-flash, timeout y client.interactions.create. No debe copiarse sin comprobar SDK/contrato, dependencia ausente H-D02 y compatibilidad con NB. No se probó proveedor real.

build_diagram_summary:193 usa nodes/edges autorizados de BD, posición, atributos, multiplicidades, wholeNodeId, etiqueta y selección. No transmite actor, historial conversacional ni contexto por participante; tampoco todo el detalle de métodos/JPA. _prompt:299 permite exclusivamente operaciones de modelado y devuelve ready/clarification/unsupported. validate_provider_response:262 impone campos exactos, límites y operaciones solo para ready; ready exige operaciones. No existe un tipo de respuesta conversacional answer separado. El canal question/unsupported puede mostrar texto, pero no implementa por sí solo asesoría conceptual.

### Operaciones, planes, confirmación y permisos

ai_operations.py:160::execute_operations trabaja sobre deepcopy y valida con DiagramaSerializer. Soporta crear/actualizar/mover/eliminar nodos, atributos, métodos, crear/actualizar/eliminar relaciones y project.create. Campos permitidos, IDs reales/temporales, semántica UML, tipos y lote inválido se controlan determinísticamente. No ejecuta código arbitrario del modelo. Aunque no usa ORM directamente, depende de DRF, DiagramaSerializer y del documento React Flow; no es portátil sin adaptación al ORM/snapshot de NB.

PlanIA en models.py:20 guarda propietario, diagrama, operaciones, revisión base, hashes, request_id, TTL y resultado de aplicación. create_plan/apply_plan en ai_plans.py recuperan operaciones servidor, exigen plan del usuario y diagrama, membresía vigente, revisión/caducidad y lote válido, dentro de transaction.atomic con select_for_update. Cambios de relaciones exigen propietario/arquitecto; editor no puede indirectamente borrar relaciones al borrar nodos. _requires_confirmation:61 exige confirmación de **toda** mutación, no solo borrados. Son controles verificados en tests fake, con las limitaciones de SQLite/ausencia de concurrencia real de fase 1.

POST .../aplicar-plan-ia/ devuelve nodes/edges/revision autoritativos. interpretar_ia persiste plan, pero no cambia el documento: el test denominado without_persisting acredita esa ausencia de mutación del diagrama, no ausencia de PlanIA en BD. La vista publica WS tras volver de apply_plan; es una publicación posterior a la transacción del servicio, no una garantía general de entrega única.

### Revisiones y duplicados: garantías acotadas

Datos: prueba original de retry idempotente sin expected_revision pasa. H-D03 de fase 1 demuestra que repetir el mismo body con revisión inicial después del éxito produce 409 antes de devolver resultado almacenado. Frontend genera nueva idempotencyKey al iniciar applyCurrentAiPlan; hace falta estudiar reintento de una respuesta perdida conservando clave. PlanIA solo tiene índices, no unicidad compuesta usuario/diagrama/request_id; la consulta previa no demuestra deduplicación de solicitudes concurrentes. La vista vuelve a publicar resultados applied incluso si son un resultado previamente aplicado; idempotencia de datos no equivale a una sola emisión WS.

**Hallazgo adicional H2-D01, reproducido:** interpretar_ia valida expected_revision al comienzo, pero en views.py:261 refresca solo revision tras el proveedor y crea el plan con esa revisión nueva, manteniendo la propuesta calculada sobre el contexto anterior. La sonda simuló cambio de título y revisión durante interpret: request esperado 0, diagrama pasa a 1, respuesta ready con plan base 1; aplicación autorizada esperando 1 acepta la propuesta y deja revisión 2. No demuestra carrera multihilo ni proveedor real. Demuestra que la frontera servidor no rechaza esa propuesta antigua en esa ventana; si el cliente conserva revisión 0, su aplicación sí podrá dar 409. No contradice tests previos de planes que se vuelven obsoletos después de crearse: cubre otra ventana antes de su creación. No se copian estas garantías como si fueran completas.

### Editor, colaboración, voz e historial

DF/src/api/aiApi.js:5/17 conecta interpretar/aplicar con Axios, sesión y CSRF. DiagramCanvas.jsx:568::interpretAiCommand guarda antes de interpretar, usa selección, cancela solicitudes tardías y comprueba diagrama actual. applyCurrentAiPlan:508 invalida autosaves y restaura respuesta autoritativa. utils/collaborationSync.js descarta generaciones/revisiones antiguas y ecos propios; useDiagramSocket.js reconecta/presencia. Backend realtime.py::publish_diagram_update emite el documento, no conversación. Transporte Redis/dos usuarios sigue parcialmente verificado.

DiagramCanvas.jsx:692 configura Web Speech sin provisionales, filtra isFinal y deduplica texto; utils/aiFlow.js::voiceFinalAction reconoce activación, detener, confirmar/cancelar. speakDiana:311 pausa reconocimiento, segmenta y usa speechSynthesis; utils/dianaVoice.js elige voz, preferencias es-BO/es-ES, limpia texto. Cancelar invalida petición/plan en cliente, sin endpoint de cancelación persistida; el plan almacenado conserva su TTL. Funciones puras probadas, micrófono/TTS real no verificado. VoiceCommand.jsx tiene **0 bytes**; la lógica está en DiagramCanvas.

Matiz de integración de voz: voiceFinalAction puede devolver send en estado wake ante una frase prefijada Diana, pero el bloque wake del componente (líneas 750–761) solo procesa wake y retorna antes del bloque send. No se acredita que todos los comandos admitidos por la utilidad funcionen igual desde UI. El flujo Hola Diana seguido de instrucción está identificado, no probado con audio real.

addAiHistory:308 conserva solo seis entradas locales. PlanIA registra operaciones, no diálogo recuperable; no hay memoria individual/grupal ni emisión WS de preguntas/respuestas. Ninguna prueba fake demuestra inteligencia conceptual o moderación. Fortalezas: separación proveedor/operaciones/planes, errores estructurados y tests. Límites: dependencia del documento React Flow/JPA, componente de editor muy concentrado, SDK remoto ausente, idempotencia/revisión incompletas y ausencia de conversación colaborativa requerida.

## D. Matriz comparativa de asistentes

Esta matriz es exclusivamente de IA, autorizada para fase 2. No es la matriz global cuantificada del maestro. Las referencias B/C remiten a archivos, funciones y endpoints detallados arriba; K vincula pruebas reales reutilizadas y nuevas. «Mejor» se limita a la dimensión indicada.

| ID / característica | IA NodoBoard | Diana | Mejor implementación | Evidencia | Recomendación preliminar |
|---|---|---|---|---|---|
| C01 Proveedor IA | Gemini generate_content; key/modelo y candidatos; SDK declarado. Real NO VERIFICADO. | Gemini interactions; factory/timeout; SDK no declarado/disponible en fase 1. Real NO VERIFICADO. | NO VERIFICADO para calidad/disponibilidad. Diana SUPERIOR en separación del adaptador; NB mejor declaración de dependencia, sin certificar SDK. | NB views:499, requirements; DB ai_interpreter:141/188; fase 1 H-D02. | CONSERVAR proveedor actual y ADAPTAR interfaz separable; no cambiar por supuesta inteligencia superior. |
| C02 Comprensión general | Prompt relacional y delta, sin medición real. | Parser local acotado y proveedor con esquema/fake. | NO VERIFICADO para comprensión abierta; no inferir superioridad del número de comandos. | NB SYSTEM_PROMPT_INSTRUCCIONES; DB class_create_proposal; test_ai_interprets_class_entity_interface_and_attributes_without_provider. | INVESTIGAR corpus local representativo y luego proveedor solo con autorización. |
| C03 Crear entidades/clases | Entidades relacionales, PK automática y es_intermedia; código, sin suite IA propia. | class/entity/interface y otras variantes aceptadas por ejecutor; creación local/fake probada. | Diana SUPERIOR en contrato/tipos validados; calidad NL NO VERIFICADO. | NB procesarDelta:871; DB execute_operations; tests de operaciones y creación local. | ADAPTAR contrato al dominio NB, sin importar toda la semántica JPA. |
| C04 Modificar atributos/métodos | Renombre/upsert/quitar atributos; seis tipos; semántica local. Métodos sin flujo IA localizado. | add/update/remove atributos y métodos tipados, validación backend. | Diana SUPERIOR en validación/cobertura; UX real NO VERIFICADO. | NB procesarDelta:924; DB OPERATION_FIELDS y test_ai_operations_support_add_update_and_remove_methods. | ADAPTAR validación servidor preservando política de atributos NB. |
| C05 Relaciones/multiplicidades | Cuatro tipos; crear/eliminar; clases de asociación; contexto omite cardinalidad. | Seis tipos, update_relation, multiplicidades, roles/whole/JPA; resumen incluye multiplicidades. | Diana SUPERIOR en contrato validado; equivalencia relacional NB requiere adaptación. | NB interface RelacionACrearIA y extraerContexto; DB RELATION_TYPES/build_diagram_summary; test_ai_complex_relation_proposals_pass_the_existing_contract. | ADAPTAR solo semántica compatible; INVESTIGAR realización/dependencia como alcance futuro. |
| C06 Reconocimiento de voz | Push-to-talk/continuo, finales+parciales; fallback texto. | Estados wake/instruction/confirmation, filtro final, dedupe; matiz wake/send en UI. | Diana SUPERIOR en filtro/dedupe de utilidades; experiencia/audio NO VERIFICADO. | NB iniciar/detenerReconocimiento; DF DiagramCanvas:692 y aiFlow.test.js. | ADAPTAR procesamiento final y estados; CONSERVAR interacción Angular por espacio. |
| C07 Síntesis de voz | NO IMPLEMENTADO en flujo inspeccionado. | Implementación identificada, utilidades probadas; dispositivo NO VERIFICADO. | Diana SUPERIOR en existencia/selección/segmentación, no en calidad audible probada. | DF speakDiana:311, dianaVoice.js/.test.js. | ADAPTAR opcionalmente a servicio Angular, respetando preferencias y fallback. |
| C08 Chat/UX | Panel Angular con mensajes, hora, estado de carga, texto y voz. | Panel integrado con preview de plan, confirmación/cancelación e historial corto. | NO VERIFICADO para usabilidad global. Diana SUPERIOR en visibilidad del plan; NB SUPERIOR en compatibilidad nativa con destino. | NB chat TS/HTML; DF aiHistory y aiPlan. | CONSERVAR un chat NB y ADAPTAR preview/errores; no duplicar interfaz. |
| C09 Contexto de documento | Snapshot del cliente sin selección/multiplicidades/actor/historial. | Snapshot autorizado BD con selección, posiciones y multiplicidades; no diálogo ni detalle completo de miembros. | Diana SUPERIOR en procedencia autoritativa y selección; no contexto conversacional. | NB extraerContexto:735 y views:458; DB build_diagram_summary:193; sonda NB nueva. | FUSIONAR contexto mínimo NB con patrón servidor/selección, sin copiar shape React Flow. |
| C10 Consultas conceptuales | Prompt las admite con mensaje/deltas vacíos; transporte fake verificado, respuesta real NO VERIFICADA. | Sin modo answer; ready requiere operaciones y unsupported/clarification sirven modelado. | NO VERIFICADO para exactitud/asesoría. NB tiene vía explícita identificada, no victoria semántica demostrada. | NB views:430; nueva test_conceptual_shaped_response...; DB validate_provider_response:286 y _prompt. | CONSERVAR intención NB y desarrollar canal de consulta separado de mutación. |
| C11 Validación de operaciones | JSON dict no garantiza listas; filtros cliente y snapshots. | Esquema, operaciones permitidas, ejecución determinista y validación del documento. | Diana SUPERIOR en frontera determinista; NB INFERIOR en ese control reproducido. | Nueva wrong_delta_type; DB test_ai_operations_reject_invalid_batches_without_mutating_inputs. | ADAPTAR ejecutor/validador al ORM y permisos NB. |
| C12 Confirmación | Sin preview/confirmación IA conectada; aplicación inmediata tras éxito. | Plan servidor; toda mutación exige confirm=true; preview/cancelación cliente. | Diana SUPERIOR en control probado. Audio de confirmación NO VERIFICADO. | NB manejarExito:229; DB _requires_confirmation/apply_plan, test_ai_plan_rejects_confirmation_conflict_expiry_and_invalid_batch. | ADAPTAR confirmación para cambios según política explícita; cancelar sin aplicar. |
| C13 Seguridad/usuario | JWT e IsAuthenticated; no proyecto/revisión del request IA; H-N01–03 en escritura. | Sesión+CSRF; plan ligado usuario/diagrama y roles; H-D04 heredado y H2-D01. | Diana SUPERIOR específicamente en permisos de planes; seguridad global no certificada. | DB require_role, test_ai_plan_rejects_other_user_and_editor_relation_changes; fase 1. | ADAPTAR controles a JWT y UserColaborador NB. No migrar autenticación ni APIs heredadas. |
| C14 Duplicados/idempotencia | Busy flag y upsert atributo; no request_id/plan persistido. | request_id/hash, plan/clave de aplicación y dedupe voz; retry esperado y unicidad concurrente incompletos. | Diana SUPERIOR en mecanismos existentes, sin garantía completa. | test_ai_request_id_is_persisted_idempotent_and_cannot_change_instruction; H-D03; PlanIA.Meta. | ADAPTAR tras resolver semántica de retry y emisión repetida; no copiar defectos. |
| C15 Conflictos/revisiones | No expected_revision; snapshot antiguo puede borrar entidades. | Revisión y lock al aplicar/guardar; ventana antes de crear plan permite rebase. | Diana SUPERIOR en rechazo de planes ya obsoletos; incompleta en H2-D01. | Fase 1 H-N03 y test_document_writes_require_matching_expected_revision; sonda nueva DB. | ADAPTAR revisión coherente en todas las vías de escritura; exigir misma base de interpretación. |
| C16 WebSocket | Eventos individuales cliente y snapshot posterior; chat no compartido. | Respuesta autoritativa y publicación servidor; revisión/generación en store; chat no compartido. | Diana SUPERIOR en frontera persistir→publicar identificada; E2E NO VERIFICADO. | NB onEjecutarDeltaIA, PizarraConsumer; DB aplicar_plan_ia/realtime, DF collaborationSync. | ADAPTAR payload autoritativo a grupos de proyecto NB; desarrollar eventos de conversación aparte. |
| C17 Errores | Categorías HTTP y texto/raw; puede aceptar delta inválido. | code/message/target/current_revision y errores de lote; UI enfoca elemento. | Diana SUPERIOR en contrato/diagnóstico probado; red real NO VERIFICADA. | Nuevas NB error cases; DB test_ai_interpretation_rejects_invalid_provider_payload_and_errors. | ADAPTAR DTO de errores a IDs NB y evitar raw/detalles sensibles. |
| C18 Historial/seguimientos | Array local, sin recuperación backend ni envío de historia. | Hasta seis entradas locales; planes persistidos no son diálogos. | EQUIVALENTE en carencia de memoria conversacional persistida; seguimientos NO VERIFICADOS. | NB mensajesChat/models; DF addAiHistory:308; DB PlanIA/build_diagram_summary. | Desarrollo nuevo de conversaciones grupales/por participante. |
| C19 Extensibilidad | Vista mezcla prompts, proveedor/parser; servicio mezcla voz/normalización/delta. | Factory, intérprete, ejecutor/planes separados; UI concentrada en canvas. | Diana SUPERIOR en separación backend; no portable directamente. | Archivos ai_interpreter/ai_operations/ai_plans frente a NB views/service. | ADAPTAR límites y tests; CONSERVAR arquitectura Angular/Django. |
| C20 Mantenibilidad | Servicio/componente Angular existentes reducen cambio de superficie. Sin tests IA propios. | Tests de límites y módulos backend; canvas muy concentrado y deuda de revisión/idempotencia. | Diana SUPERIOR en testabilidad backend; NB SUPERIOR en ajuste nativo al destino. Global NO VERIFICADO. | Fase 1: diagramas 59 tests y utilidades 28; NB asistente/tests placeholder. | ADAPTAR cobertura/contratos y evitar portar componente monolítico. |
| C21 Entrada por imagen | Endpoint, compresión y normalización integrados; modelo real NO VERIFICADO. | No flujo de boceto→modelo equivalente localizado en módulos Diana analizados. | NB tiene capacidad adicional identificada; calidad NO VERIFICADA. | GenerarDiagramaDesdeImagenView y generarDiagramaDesdeImagen/normalizarRespuestaIA. | CONSERVAR entrada y validar su salida con la misma frontera segura futura. |
| C22 Proveedores/LLM local | Parámetros Gemini; no selector multiadaptador/local. | Factory Gemini y parser local; no otro proveedor/LLM local. | EQUIVALENTE en falta de multiproveedor/local conectado; factory Diana extensible. | Settings y get_ai_provider; sin adaptadores alternativos localizados. | ADAPTAR interfaz sustituible; modelo local opcional, sin reemplazo obligatorio. |

## E. Capacidades de Diana aprovechables y puntos de integración

Decisiones **preliminares**. No se propone copiar migraciones/modelos/endpoints automáticamente ni componentes React en Angular. No se identificó módulo cuya migración literal completa esté justificada; predominan ADAPTAR/FUSIONAR. Crear nuevos archivos/modelos es una posibilidad futura, no trabajo ejecutado.

| Capacidad y decisión | Alternativa actual NB / origen real | Punto de integración NB | Dependencias e incompatibilidades | Beneficio y riesgos |
|---|---|---|---|---|
| E1 Operaciones tipadas — ADAPTAR | NB procesarDelta normaliza en cliente. DB ai_operations.py::execute_operations, OPERATION_FIELDS, _strict_object, _validate_document. | backend/asistente/views.py entre salida IA y ejecución; modelado/models.py/serializers.py y rutina de escritura; interfaz DeltaInstruccionIARespuesta/AsistenteIaService. | DRF/DiagramaSerializer y shape nodes/edges deben sustituirse por validación NB, IDs enteros, PK/nulabilidad, estados y clase_asociacion. No mezclar autoridad ORM con un segundo documento React Flow. | Rechazar tipos/campos/IDs inválidos y lotes parciales. Riesgo: pérdida semántica por coerciones y alterar políticas relacionales. Necesita tests de equivalencia sobre entidades reales. |
| E2 Plan persistido/confirmación — ADAPTAR | NB aplica delta inmediatamente. DB models.py::PlanIA, ai_plans.py::{create_plan,apply_plan,_requires_confirmation}, views.py::_plan_response. | Apps asistente/modelado; chat-asistente-ia.component.ts/.html y WhiteboardPage.onEjecutarDeltaIA. | Autoridad usuario/proyecto, revisión, caducidad y resultado; diseño futuro propio y estrategia de persistencia. No copiar migraciones ni FK Diagrama/ProyectoMiembro. | Preview autorizado y aplicación atómica. Riesgos: caducidad, revocación, confirmar plan cambiado, tratar cancelación local como revocación servidor; requieren contrato nuevo coherente. |
| E3 Revisión/autosave autoritativo — ADAPTAR | NB eventos/snapshot sin revisión. DB apply_plan/save_diagram_if_user_can_access/realtime; DF invalidatePendingSaves/replaceWithAuthoritativeDocument/collaborationSync.js. | PizarraConsumer._guardar_snapshot_db, modelado/realtime.py, WhiteboardSocketService, WhiteboardPage y servicios canvas. | PostgreSQL/transacciones, revisión monotónica y respuesta con remapeos. Debe cubrir toda escritura relacionada, no solo endpoint IA; integración con importación/REST se evaluará en fase autorizada futura. | Evitar perder cambios y mostrar verdad persistida. Riesgos: snapshot antiguo, carrera H2-D01, eco/remapeo y cierres abruptos. No importar garantía incompleta de Diana. |
| E4 Dedupe/idempotencia — ADAPTAR | NB busy flag/upsert no bastan. DB request_fingerprint, request_id, PlanIA y apply_plan; DF aiRequestRef/voiceRequestIdsRef y aiFlow. | Endpoint IA/planes futuros, AsistenteIaService, chat y servicio socket NB. | IDs de solicitud estables, asociación usuario/proyecto, hash/resultado; decisiones sobre retry, unicidad concurrente y entrega de eventos. | Evitar duplicar creación o aplicación. Riesgo: H-D03, nueva clave por reintento, repetir publicación y tratar dos instrucciones iguales legítimas como duplicadas. |
| E5 Errores estructurados — ADAPTAR | NB raw/error y filtros silenciosos. DB api_errors.py/OperationError/PlanError, vistas; DF foco por target. | Respuestas backend/asistente, interfaces IA, toasts/chat y canvas NB. | Mapear target node/edge a entidad/relación numérica y remapeos temporales; códigos estables, no dependencia React. | Diagnóstico accionable/recuperación; riesgo de filtrar datos sensibles o foco sobre ID obsoleto. |
| E6 Voz final/confirmación/TTS — ADAPTAR | NB ya tiene push-to-talk. DF aiFlow.js::voiceFinalAction/voiceRecognitionError, dianaVoice.js y speakDiana/onresult del canvas. | AsistenteIaService y ChatAsistenteIaComponent existentes. | Web Speech y APIs de navegador, Angular/RxJS, preferencias del usuario, estados de plan. No portar JSX, hooks ni exigir nombre Diana. | Menos envíos parciales y confirmación accesible; TTS opcional. Riesgos: feedback acústico, disponibilidad de voz/red del navegador, falsos finales; corregir coherencia wake/send antes de reutilizarla. |
| E7 Contexto servidor/proveedor — FUSIONAR conceptos | NB prompt relacional/imágenes y Gemini SDK declarado. DB build_diagram_summary, get_ai_provider/GeminiInterpreter, validate_provider_response. | views.py, core/settings.py y extraerContextoDiagrama; servicio proveedor separable dentro de asistente como opción futura. | Obtener documento autorizado desde proyecto/ORM, incluir multiplicidades/selección relevantes; mantener JSON/contexto mínimo. SDK de NB y dos APIs Google no se asumen equivalentes. | Proveedor reemplazable y contexto fiable sin abandonar asistente actual. Riesgos: contexto antiguo, nombres ambiguos, prompt injection y acoplar modelo a dato visual/JPA. |
| E8 Preview integrado — CONSERVAR NB y ADAPTAR interacción | NB ya tiene chat; DF estado aiPlan/aiStatus, resumen/confirmar/cancelar. | Componente Angular actual y sus interfaces; no nueva aplicación React. | Estados claros, separar respuesta/plan/resultado; conservar errores y progreso, render seguro de texto. | Un flujo único comprensible. Riesgos: mostrar éxito antes de persistencia, confianza engañosa del preview y duplicar conversaciones. |
| E9 Parser determinista — INVESTIGAR | NB usa proveedor para comandos; DB project_create_proposal/class_create_proposal, pruebas de gramática. | Antes de adaptador NB, sujeto al mismo validador/plan/permisos. | Traducir gramática al dominio relacional y aclarar nombres ambiguos; no reemplaza asesoría o seguimiento. | Algunas órdenes funcionan sin proveedor; beneficio condicionado a corpus real. Riesgo: unir palabras/normalizar nombres incorrectamente, parser que capture instrucciones fuera de su gramática. |
| E10 Tests de fronteras — ADAPTAR | NB asistente/tests.py vacío. DB tests fake/operations/plans y DF aiFlow/dianaVoice/collaborationSync tests. | Tests backend asistente/modelado y tests Angular de servicio/componente. | Reescribir fixtures, roles y payloads; test runner Angular en entorno compatible. No copiar suites dependientes de Diagrama/React Flow. | Regresiones reproducibles sin proveedor; riesgo de dar por buena la inteligencia solo porque pasa un fake. Incluir hallazgos H-D03/H2-D01 en futuros casos. |

Todas estas capacidades requieren resolver primero su contrato en el dominio de NodoBoard para autorizar ejecución. Esto describe dependencias lógicas y condiciones; no fija secuencia global, prioridad ni ranking.

## F. Funcionalidades que NodoBoard debe conservar

1. **Un solo asistente y el chat Angular existente.** ChatAsistenteIaComponent ya conecta entrada escrita/voz, mensajes, carga y errores con WhiteboardPage. Para el destino evita trasladar React/Zustand/React Flow. Es superior en compatibilidad de integración con NodoBoard; no se declara superioridad de usabilidad sin ensayo de usuarios. Conservar componente no implica conservar aplicación inmediata insegura del delta.
2. **JWT y el modelo de pertenencia propio.** IsAuthenticated, UserColaborador y grupos por proyecto deben seguir siendo la autoridad, endureciendo autorización/revocación donde fase 1 encontró defectos. No introducir sesiones/allauth solo para importar Diana. No conservar los fallos H-N01–03.
3. **El dominio de entidades, atributos, estados y clases de asociación.** AsistenteIaService.procesarDelta y modelado.models trabajan con IDs numéricos, es_clave/es_nulo y entidad intermedia. Los mecanismos tipados deben traducirse a estas reglas, sin convertir silenciosamente todo a entidades JPA ni reemplazar los datos por JSON React Flow.
4. **Texto y push-to-talk con fallback.** La UX por espacio ya está integrada; adaptar finales/dedupe y confirmaciones es compatible con mantenerla. La activación nominal de Diana no es requisito académico ni razón para cambiar el nombre del asistente.
5. **Entrada por imagen y normalización espacial.** GenerarDiagramaDesdeImagenView y onDiagramaIAGenerado ofrecen un camino distinto. Conservar su superficie, con proveedor real pendiente y validación autoritativa futura; no confundir generación completa desde boceto con edición incremental de una instrucción.
6. **Gemini actual y parámetros configurables, mientras se valida la opción técnicamente.** No hay evidencia de que reemplazar proveedor mejore comprensión/coste/latencia. Separar adaptador y permitir selección futura es distinto de sustituirlo ahora. Mantener key exclusivamente backend y evitar registrar datos sensibles.
7. **Servicios canvas/socket y flujos existentes del proyecto.** Usarlos como puntos de integración, ajustando contratos de revisión/persistencia cuando se autorice, evita un segundo canal de edición o una autoridad paralela.

No se ha demostrado ninguna ventaja de inteligencia general de NB o Diana. Las ventajas propias NB acreditadas son integración nativa, políticas de dominio y existencia de entradas concretas, con estados de ejecución diferenciados.

## G. Funcionalidades redundantes o sin traslado justificado

| Elemento | Decisión preliminar y fundamento |
|---|---|
| Segundo chat/personaje Diana junto al actual | DESCARTAR duplicación. No aporta memoria compartida por sí mismo y fragmenta historia/contexto; un solo asistente puede incorporar los mecanismos útiles. |
| Componentes React/DiagramCanvas/Zustand/React Flow como reemplazo Angular | DESCARTAR traslado de UI. Sus contratos no son JointJS/servicios Angular; adaptar patrones, no JSX/hooks. |
| Sesiones, allauth y nuevas rutas auth para este propósito | CONSERVAR JWT NB; DESCARTAR reemplazo de autenticación como dependencia de la IA. No se justifica por planes o voz. |
| Tablas heredadas ClaseUML/AtributoUML/RelacionUML del donante | DESCARTAR como segunda persistencia. No son autoridad del canvas Diana y existe brecha heredada H-D04; fuera del contrato deseado NB. |
| Copiar migraciones y PlanIA literalmente | DESCARTAR copia literal. FKs/roles/revisión/modelo del diagrama difieren. ADAPTAR el concepto, sin cambiar esquema durante esta fase. |
| Otro cliente Gemini/configuración de claves paralelo | FUSIONAR el patrón de adaptador con proveedor existente. Dos rutas de proveedor sin una interfaz común aumentan mantenimiento y divergencia. |
| Historial local de seis entradas como solución al historial académico | DESCARTAR como sustituto de persistencia. Puede servir para preview, pero no recupera preguntas/respuestas ni contexto por usuario. |
| Rehacer reconocimiento básico que NB ya tiene | CONSERVAR base; ADAPTAR procesamiento final, dedupe y TTS opcional. No migrar todo para agregar solo un micrófono. |
| project.create y soporte de generación Spring/JPA por el mero hecho de venir con Diana | Sin traslado justificado para las brechas de conversación de fase 2. INVESTIGAR solo si un requisito posterior autorizado lo necesita; no importar permisos/operaciones extra por defecto. |

## H. Evaluación frente al segundo parcial

Estados se refieren al requisito completo; evidencia de un submecanismo se aclara expresamente. La tabla no convierte un mock en una respuesta inteligente real.

| Requisito | NodoBoard | Diana | Evidencia y brecha / origen de la mejora |
|---|---|---|---|
| 1 Identificar participante que pregunta y responder atribuyendo su identidad | IMPLEMENTADO PARCIALMENTE | IMPLEMENTADO PARCIALMENTE | NB autentica request pero muestra Tú; DB vincula PlanIA.usuario. Ningún contexto al proveedor contiene participante/diálogo ni garantiza mención personalizada. Desarrollo nuevo de atribución de conversación sobre usuarios autorizados. |
| 2 Preguntas y respuestas visibles para todos | NO IMPLEMENTADO | NO IMPLEMENTADO | mensajesChat/aiHistory locales; eventos WS inspeccionados transmiten diagrama/presencia, no hilo IA. Desarrollo nuevo de mensajes grupales y sus eventos/permisos. |
| 3 Contexto grupal conversacional | NO IMPLEMENTADO | NO IMPLEMENTADO | Estado del diagrama no equivale a conversaciones, acuerdos/decisiones de equipo. Diana ayuda con contexto autoritativo de documento; memoria grupal requiere desarrollo nuevo. |
| 4 Contexto individual | NO IMPLEMENTADO | NO IMPLEMENTADO | Sin mensajes/hilo participante persistidos ni input equivalente al proveedor. Desarrollar separación por actor dentro del contexto compartido y límites de acceso. |
| 5 Preguntas de seguimiento | NO VERIFICADO | NO VERIFICADO | No se envía historial. Puede haber referencias a nombres del diagrama, pero no prueban anáfora de conversaciones individuales. Memoria/resolución requieren desarrollo nuevo; calidad modelo pendiente de proveedor autorizado. |
| 6 Explicaciones conceptuales UML | NO VERIFICADO | NO IMPLEMENTADO como modo asesor explícito; inteligencia NO VERIFICADA | NB prompt admite duda y transporte fake sin delta; no respuesta real validada. Diana no tiene answer y bloquea lector. Desarrollar modo consulta de solo lectura y evaluar contenido sin inferirlo de un plan. |
| 7 Recomendar mejoras de diseño | NO VERIFICADO | NO VERIFICADO | No corpus/criterios de asesoría verificados. Delta/plan ejecutable no equivale a recomendación razonada. Desarrollo de respuestas/recomendaciones y separación de propuesta/modificación. |
| 8 Interpretar instrucciones para modificar | IMPLEMENTADO PARCIALMENTE | IMPLEMENTADO PARCIALMENTE | NB recorrido de delta conectado y handler simulado; Diana gramáticas locales y ejecutor/fake verificados. Comprensión abierta del proveedor no probada. Adaptables operaciones/validación de E1/E7/E9. |
| 9 Confirmación antes de modificar | NO IMPLEMENTADO en flujo IA conectado | IMPLEMENTADO Y VERIFICADO en backend/contrato | NB chat aplica al éxito; Diana toda mutación exige confirmación y plan de usuario (tests existentes). UI/voz reales parcialmente verificadas. ADAPTAR E2, sin declarar click/micrófono ensayado. |
| 10 Sincronizar operaciones autorizadas entre usuarios | IMPLEMENTADO PARCIALMENTE | IMPLEMENTADO PARCIALMENTE | NB WS/snapshot con defectos permisos/revisión. Diana persistencia/publicación autoritativa y utilidades probadas, sin Redis/dos sesiones y con H2-D01. Adaptar E3/E4 más prueba E2E futura. |
| 11 Recuperar historial conversacional | NO IMPLEMENTADO | NO IMPLEMENTADO | Ningún modelo/API de conversación recuperable; PlanIA es registro operativo. Desarrollo nuevo de persistencia/consulta y UI de historial. |
| 12 Configurar diferentes proveedores | IMPLEMENTADO PARCIALMENTE | IMPLEMENTADO PARCIALMENTE | Configuran key/modelo de Gemini, sin conmutación de proveedores implementada; factory Diana facilita extensión. Requisito multifuente completo NO IMPLEMENTADO. ADAPTAR E7 y desarrollar adaptadores que se autoricen. |
| 13 Modelo local opcional | NO IMPLEMENTADO | NO IMPLEMENTADO | Gramática local Diana no es LLM. Extensión opcional futura; no obliga a reemplazar Gemini ni es condición de esta auditoría. |

Conectarse desde sesiones/dispositivos diferentes es infraestructura parcialmente identificada, no prueba de chat compartido. Que cualquier integrante pueda preguntar necesita política separada: Diana exige rol de edición incluso al interpretar; lectores quedarían excluidos de un futuro canal conceptual si se copiara esa regla sin adaptación. El permiso de consultar puede ser distinto de modificar, manteniendo pertenencia y autorización de proyecto.

**Existente:** entrada texto/voz/chat visual, contexto de diagrama, autenticación y flujos de cambios. **Reutilizable con adaptación:** fronteras deterministas, planes, confirmación, errores, selección/contexto autoritativo, revisión/dedupe/voz de Diana. **Desarrollo nuevo:** conversación compartida persistida, actor real en cada pregunta/respuesta, contexto grupal/individual, modo asesor/moderador, recuperación y contratos de mensaje/respuesta/propuesta. **Pendiente de evaluación real:** exactitud/seguimientos/recomendaciones del modelo, operación multiusuario y dispositivos.

## I. Riesgos y dependencias

- **Dato y autoridad:** Diana ejecuta sobre nodes/edges JSON y valida JPA/Java. NB mantiene ORM más snapshot; convertir formatos indiscriminadamente puede perder IDs, clase de asociación, estado, cardinalidad, posiciones o atributos. Un validador/servicio de escritura propio debe ser autoridad; no añadir tablas heredadas o un segundo canvas como atajo.
- **Versiones/SDK:** NB declara Django 5.2/Channels 4.2.2/DRF 3.17.1; DB Django 6.1.1/Channels 4.3.2/DRF 3.18.0. Dos APIs Google distintas y SDK remoto ausente en entorno DB. No se deduce compatibilidad por compartir Python/Django. No instalar/actualizar como parte de esta fase.
- **Permisos:** UserColaborador NB no tiene arquitecto y usa visualizador; Diana diferencia arquitecto/editor/lector. Resolver reglas por acción, pertenencia vigente y permisos de pregunta frente a edición. Las vulnerabilidades H-N01–03 impiden tratar al frontend como barrera. H-D04 demuestra que no debe darse por segura toda la API donante.
- **Concurrencia:** revisión debe ser la base usada para interpretar y aplicar; no refrescarla silenciosamente después del proveedor. También deben participar otros escritores de snapshot/documento. SQLite prueba secuencias, no locks/carreras PostgreSQL.
- **Idempotencia/entrega:** diferenciar solicitud interpretada, plan confirmado, aplicación y evento. Reusar clave ante respuesta perdida; distinguir retry de dos instrucciones idénticas deliberadas; no confundir resultado almacenado con emisión única ni registro de índice con unicidad concurrente.
- **Conversación:** preguntas/respuestas compartidas necesitan actor y proyecto ligados por servidor, acceso a historial, orden/IDs y contexto limitado. Modificar el diagrama debe seguir autorización propia. No reenviar secretos o usar contenido de mensajes como instrucciones de sistema.
- **Proveedor y salida no confiable:** prompt con reglas no basta. NB acepta tipos inválidos; ambos dependen de salida del modelo para interpretación abierta. Esquema/allowlist/límites y validación semántica deben limitar lo ejecutable. El fake no certifica resistencia global a prompt injection.
- **Voz:** APIs de navegador no garantizan offline; pueden usar servicios remotos del navegador. No se activó micrófono. TTS debe ser opcional y evitar realimentación; corregir coherencia wake/send y no convertir parciales en confirmación.
- **UI/mantenimiento:** el canvas donante concentra voz/IA/edición; copiarlo aumentaría acoplamiento y rompería Angular. Preferir servicios y estados pequeños en componentes existentes. No introducir segundo historial visual o segundo asistente.
- **Errores y datos:** NB devuelve raw y detalle de excepciones; DF imprime transcripción en console.debug. Revisar exposición de datos sin afirmar filtración real ocurrida. Logging mínimo e identificación técnica de errores son patrones adaptables.

La dificultad de integrar validación/errores puros es acotada respecto a revisar todos los escritores, persistencia de planes y conversación colaborativa. Esta es una inferencia cualitativa a partir de dependencias, sin estimación numérica ni orden global de ejecución.

## J. Evaluación cualitativa preliminar y confianza

Abreviaturas de estado: **IV**=IMPLEMENTADO Y VERIFICADO en el límite citado; **IP**=IMPLEMENTADO PARCIALMENTE; **NV**=NO VERIFICADO; **NI**=NO IMPLEMENTADO. Cada fila remite a D/E para archivos/funciones/contratos específicos; aquí se explicitan ventaja, beneficio, dificultad y confianza.

| Funcionalidad | NB / Diana | Juicio cualitativo delimitado | Evidencia | Ventajas y límites | Beneficio NB / dificultad | Recomendación | Confianza |
|---|---|---|---|---|---|---|---|
| Proveedor/comprensión | IP/NV ambos; gramática Diana IV | NO VERIFICADO para comprensión; Diana SUPERIOR en separación | C01–02, get_ai_provider; tests locales | Factory permite fake, no demuestra modelo mejor; SDK falta | Sustitución/testabilidad; adaptar APIs/dominio y validar SDK | CONSERVAR proveedor, ADAPTAR interfaz | ALTA separación; BAJA inteligencia |
| CRUD de entidades/miembros | IP / IV ejecutor, IP NL | Diana SUPERIOR en validación probada | C03–04, execute_operations/tests | Campos/IDs tipados, no consulta general; semántica JPA difiere | Lotes más fiables; adaptar PK/tipos/IDs/estados | ADAPTAR E1/E10 | ALTA límites de código; MEDIA portabilidad |
| Relaciones/contexto de diagrama | IP / IV contrato, IP contexto completo | Diana SUPERIOR en contrato/selección | C05/C09, summary/serializer | Seis tipos/whole y multiplicidades; no equivalente a dominio NB ni memoria | Contexto más preciso; clases asociación/roles NB incompatibles | ADAPTAR E1/E7 | ALTA evidencia; MEDIA integración |
| Validación y errores | IP / IV en casos existentes | Diana SUPERIOR; NB INFERIOR en validar listas | C11/C17, nueva wrong_delta_type, tests de invalid batch | Rechazo determinista frente a dict genérico; red real pendiente | Evitar ejecución defectuosa, error por elemento; adaptar DTO y ORM | ADAPTAR E1/E5 | ALTA |
| Planes/confirmación/permisos | NI planes, IP auth / IV planes, IP seguridad global | Diana SUPERIOR en planes, no global | C12/C13, PlanIA/apply_plan/tests | Usuario/diagrama/caducidad/rol, pero vulnerabilidades donantes subsisten | Control y trazabilidad; nuevo contrato/persistencia y mapeo roles | ADAPTAR E2 | ALTA mecanismo; MEDIA integración |
| Duplicados/revisión/autosave | IP / IP | Diana SUPERIOR en mecanismos parciales | C14/C15, H-D03, H2-D01, collaborationSync | Existen rechazo/guardas pero no garantía completa | Reducir pérdidas/duplicados; todos los escritores y retries deben concordar | ADAPTAR E3/E4 sin defectos | ALTA límites; MEDIA solución futura |
| WS de cambios | IP / IP | Diana SUPERIOR en frontera autoritativa; E2E NO VERIFICADO | C16, realtime y test WS de revisión | Datos persistidos frente a eventos optimistas; chat no incluido | Sincronización más confiable; adaptar snapshot/remapeo/proyecto | ADAPTAR E3 | MEDIA integración real |
| Voz final/activación | IP / IP, IV utilidades | Diana SUPERIOR en filtro/dedupe; audio NO VERIFICADO | C06, onresult/aiFlow tests | Control de finales útil, wake/send no plenamente consistente | Menos envíos accidentales; integrar estados Angular/dispositivo | CONSERVAR push-to-talk, ADAPTAR E6 | ALTA estática; BAJA audio |
| TTS | NI / IP, IV utilidades | Diana SUPERIOR en capacidad identificada | C07, dianaVoice tests/speakDiana | Preferencias/segmentación, sin validación audible | Accesibilidad opcional; compatibilidad/preferencia/feedback | ADAPTAR E6 si se requiere | MEDIA |
| Chat e integración Angular | IP / IP | NB SUPERIOR para destino; UX global NO VERIFICADO | C08/C20, chat TS/HTML y canvas | Un componente nativo existe; falta preview y memoria | Menor reemplazo de UI; estados de plan/consulta nuevos | CONSERVAR NB, ADAPTAR E8 | ALTA compatibilidad; MEDIA ahorro inferido |
| Conceptos/asesoría | NV / NI modo explícito, NV inteligencia | NO VERIFICADO para calidad | C10, prompt NB:430, nueva respuesta fake | NB ya permite mensaje sin delta; no prueba exactitud. Diana no tiene answer | Separar explicación/propuesta; diseño de contrato y evaluación nueva | CONSERVAR intención NB, desarrollo nuevo | ALTA carencia de contrato; BAJA calidad |
| Historial, grupo y participante | IP local/NI compartido ambos | EQUIVALENTE en carencia de conversación persistida | C18, modelos/requests/WS | Arrays locales/planes no son memoria de equipo | Cumplir moderación/contexto/recuperación; persistencia y política de diálogo nuevas | Desarrollo nuevo en NB | ALTA alcance inspeccionado |
| Extensibilidad/mantenimiento | IP ambos | Diana SUPERIOR separación/tests backend; global NO VERIFICADO | C19/C20 y E10 | Pruebas de límites útiles, canvas concentrado y deuda real | Mejor aislamiento/testabilidad; no importar acoplamiento React | ADAPTAR patrones, CONSERVAR arquitectura | ALTA análisis; MEDIA resultado futuro |
| Imagen y dominio relacional | IP / NI equivalente localizado | NB aporta capacidad propia; calidad NO VERIFICADA | C21, GenerarDiagramaDesdeImagenView/procesarDelta | Ya conecta boceto/dominio; validación/proveedor pendientes | Preservar funcionalidad y evitar regresión; validar salida común | CONSERVAR y endurecer límite | ALTA conexión; BAJA salida real |
| Multiproveedor/modelo local | IP parámetros/NI conmutación ambos | EQUIVALENTE en implementación incompleta | C22, settings/factory | Límite sustituible Diana facilita trabajo, sin adaptador local real | Configuración futura sin segundo asistente; pruebas/operación adicionales | ADAPTAR interfaz, INVESTIGAR local opcional | ALTA estado; MEDIA viabilidad |

Criterios solicitados: para el segundo parcial pesan especialmente conversación compartida y seguridad de mutaciones, no cantidad de comandos. El beneficio probado de Diana es estructural; compatibilidad y facilidad favorecen conservar UI/domino NB; calidad/tests favorecen adoptar límites probados, sin heredar defectos. Mantenibilidad exige separar responsabilidades y evitar duplicación. La experiencia de usuario comparada exige pruebas reales pendientes. Ninguna de estas valoraciones constituye selección definitiva de módulos ni cuantificación.

## K. Pruebas y limitaciones

### K.1 Evidencia reutilizada de fase 1

No se repitieron suites que siguen respaldadas por fuentes/pruebas idénticas. Los logs T1 continúan disponibles y se consultaron sus resultados; son ejecuciones de la fase 1, no nuevas pruebas.

| Evidencia | Resultado histórico y alcance reutilizado | Límites preservados |
|---|---|---|
| DB diagramas/tests.py: 59 casos de contrato | Todos pasaron dentro de suite original de 85. Para IA: test_ai_operations_create_update_move_attributes_and_relations, ...support_temp_references_and_cascade_delete, ...reject_invalid_batches_without_mutating_inputs, ...support_add_update_and_remove_methods. | Demuestran ejecutor/contrato con fixtures, no interpretación inteligente real. |
| Interpretación fake/local DB | test_ai_interpretation_returns_valid_plan_without_persisting; ...returns_clarification_without_mutation; ...rejects_invalid_provider_payload_and_errors; ...requires_edit_permission_and_strict_request; test_ai_complex_relation_proposals_pass_the_existing_contract; ...interprets_class_entity_interface_and_attributes_without_provider. | Fake y gramáticas: no disponibilidad/calidad de Gemini. without_persisting sí crea PlanIA; no modifica Diagrama. |
| Planes y permisos DB | test_ai_plan_applies_once_atomically_and_is_idempotent; ...rejects_confirmation_conflict_expiry_and_invalid_batch; ...rejects_other_user_and_editor_relation_changes; test_ai_request_id_is_persisted_idempotent_and_cannot_change_instruction. | Reintento probado sin expected_revision; no garantía de unicidad concurrente ni de entrega única. |
| Revisión y escritura WS | test_document_writes_require_matching_expected_revision y test_websocket_save_rejects_stale_snapshot_without_overwrite. | Se prueba frontera de guardado, no Redis/dos navegadores/carreras PostgreSQL ni ventana de interpretación nueva. |
| DF test Node | 28/28, 0 fallos/omitidos. Entre archivos: aiFlow.test.js, dianaVoice.test.js y collaborationSync.test.js; también XMI/runtimeUrls. | No son 28 pruebas exclusivamente IA ni pruebas de componentes/audio real. Se reutilizan las que corresponden a cada dimensión. |
| NB tests y sondas | Tres tests propios de proyecto y cinco sondas temporales pasaron; estas reprodujeron permisos/snapshots antiguos/bigint. | No suite IA NB real; autorización de snapshot probada en rutina subyacente, no handshake WS ofensivo completo. |
| DB sonda idempotencia y API heredada | T1/dc-retry-probe.log y dc-legacy-probe.log: caso esperado de conflicto en retry y traslado heredado ajeno confirmados. | Defectos del donante vigentes; no presentarlos como seguridad satisfactoria. |
| Suite completa y entorno | 85 DB: 69 éxitos, 1 fallo por expected_revision omitida en test antiguo y 15 errores jsonb_array_length sobre SQLite. NB check completo bloqueado por Google SDK ausente. | No suite global verde. Errores SQLite no prueban fallo PostgreSQL; SDK ausente no demuestra que el proveedor remoto falle en otra instalación. |
| Calidad frontend fase 1 | DF lint/build y NB tsc pasaron; NB build bloqueado por permisos, Karma/Chrome no inició. | No se repitieron builds generales ajenos a nuevas conclusiones IA. Templates/audio/UX/E2E continúan pendientes. |

Comandos originales relevantes, ejecutados **en fase 1** sobre T1:

```text
python-explicito -B T1/django_runner.py dc_backend test --noinput -v 2
python-explicito -B T1/django_runner.py nb test modelado.tests audit_probes --noinput -v 2
python-explicito -B T1/django_runner.py dc_backend test audit_dc_probes --noinput -v 2
python-explicito -B T1/django_runner.py dc_backend test audit_dc_legacy --noinput -v 2
node --test src/api/xmiApiContract.test.js src/utils/aiFlow.test.js src/utils/dianaVoice.test.js src/utils/collaborationSync.test.js src/utils/runtimeUrls.test.js src/utils/xmiImport.test.js
```

Los comandos NB originales utilizaban el subset de URLconf y versiones distintas de sus requisitos, como explica AUDITORIA_FASE_1.md. No se elevó su alcance de verificación en este informe.

### K.2 Verificaciones adicionales: necesidad, aislamiento y resultados

Motivo de nuevas pruebas: fase 1 no ejecutó el handler IA NB por ausencia de Google SDK y no cubrió cambios de revisión **durante** la interpretación DB. Se añadieron únicamente estas verificaciones; no se repitieron las suites anteriores.

**Condiciones comprobadas antes de ejecutarlas:**

- T2 fue creado como directorio nuevo fuera de repositorios. No existía informe final y se registraron Git/hash antes de pruebas.
- NB usa AST de su post real, leído sin importar el módulo completo. Se compila únicamente ese método, sin editarlo; Response/settings/status y cliente SDK son objetos locales simulados. No importa Google, no carga .env, no consulta BD y no abre UI. Un audit hook rechaza red y escrituras fuera de T2. Es una unidad del handler, no un test DRF de autenticación/middleware/endpoints completos.
- DB se copió a T2/dc_backend desde archivos locales, excluyendo .env/.git/.agents/staticfiles/repositorios Maven. No se instalaron paquetes ni se alteraron originales. Se copió el harness aislado de fase 1 a T2, sin modificar el original.
- El runner DB configura SQLite exclusivamente de prueba en memoria, Channels/caché/correo en memoria, clave ficticia, dotenv deshabilitado y restricciones de escritura/red. Los únicos sockets permitidos son mecanismos internos de despertar Windows heredados del harness, no proveedor/Redis/PostgreSQL/SMTP.
- Se parcheó get_ai_provider para devolver una clase fake local. La actualización ORM dentro de su interpret ocurre solo en la base nueva de prueba y simula un cambio intermedio; no es migración ni escritura de BD real.
- Python explícito DB/.venv/Scripts/python.exe con -B y PYTHONDONTWRITEBYTECODE=1; TEMP/TMP=T2. subprocess con cwd T2, timeout de 60 s por prueba y logs nuevos allí. No se sobrescribieron artefactos de pruebas anteriores ni se limpiaron directorios ajenos.

Comandos nuevos:

```powershell
& 'D:\swProyecto\backend\.venv\Scripts\python.exe' -B 'T2\snapshot.py' 'T2'
& 'D:\swProyecto\backend\.venv\Scripts\python.exe' -B 'T2\run_additional.py' 'T2'
# Subprocesos de run_additional.py, cwd T2:
& 'D:\swProyecto\backend\.venv\Scripts\python.exe' -B 'T2\nb_handler_probe.py'
& 'D:\swProyecto\backend\.venv\Scripts\python.exe' -B 'T2\django_runner.py' dc_backend test phase2_probe --noinput -v 2
```

T2 en estos ejemplos se sustituye por la ruta completa definida en A; es una abreviatura documental, no una variable configurada en los repositorios.

| Prueba nueva | Resultado observado | Qué acredita y qué no |
|---|---|---|
| test_empty_instruction_is_rejected_without_provider | 400; 0 llamadas fake | Rechazo de instrucción vacía en método real; no prueba IsAuthenticated. |
| test_missing_key_rejected_without_provider | 500; 0 llamadas fake | Rama de clave ausente, con entorno simulado sin leer secretos. |
| test_conceptual_shaped_response_is_delivered_with_empty_deltas | 200, mensaje fake y seis listas vacías | Transporte de respuesta sin delta; NO exactitud conceptual ni clasificación inteligente de pregunta. |
| test_wrong_delta_type_is_accepted_by_handler | 200 y entidades_a_crear permanece cadena invalid-list | Defecto de validación de tipo; no se ejecutó ese dato en UI ni BD. |
| test_invalid_json_returns_raw_error | 500 y raw de entrada fake | Manejo de parseo y exposición raw; no filtración real de secreto demostrada. |
| test_context_drops_multiplicity_and_no_actor_or_history_is_sent | Contenido fake carece de cardinalidad_, historia prior e identidad 23 | El método real no incorpora esos campos al prompt; no garantiza privacidad general del contenido del diagrama. |
| test_provider_outage_returns_502_after_candidate_attempts | 502 tras 4 intentos fake | Fallback/categoría de error; no latencia, cuota ni servicio externo reales. |
| test_provider_context_revision_is_rebound_after_concurrent_change | Interpret 200 con base_revision=1 pese a request inicial 0; apply con revisión 1→200, título Proposal.java y revisión 2 | H2-D01 en frontera servidor con escritura intercalada simulada. No carrera multihilo, no todos los clientes necesariamente sobreescriben: cliente aún en 0 puede rechazar al aplicar. |

**Resultado nuevo: 7/7 unidades NB + 1/1 prueba DB, ambos subprocesos exit 0.** Los casos que aceptan un defecto tienen aserciones sobre ese comportamiento inseguro: OK no significa control correcto. T2/nb-handler.log y T2/dc-interpret-revision.log conservan resultados. La prueba DB emite en logs la etiqueta de producción «Gemini llamado/respuesta recibida» porque proviene del logger de la vista: **get_ai_provider estaba sustituido por fake y no se realizó llamada Gemini**. Warning sobre T2/static ausente es propio de raíz aislada sin collectstatic, sin afectar el resultado.

Los mensajes Applying migrations/Destroying test database corresponden solo a creación/destrucción automática de BD en memoria nueva. No se ejecutó migrate contra ninguna base existente.

### K.3 Pruebas no realizadas y limitaciones

| Verificación | Estado y razón |
|---|---|
| Respuestas Gemini reales, imagen, exactitud conceptual, NL abierto, seguimientos y asesoría | PENDIENTE DE VERIFICACIÓN. Prohibición explícita de proveedores externos en la instrucción de fase 2. Ningún código/diagrama/usuario/credencial fue enviado por las pruebas a un proveedor. La ausencia del SDK en entorno es un límite adicional, no motivo para eludir la prohibición. |
| Proveedores alternativos o LLM local | NO IMPLEMENTADO conectado; no instalar/modelar/configurar como parte de auditoría. Gramática local no es prueba de modelo local. |
| Reconocimiento/TTS reales o capturar audio | NO VERIFICADO. No se activó navegador/micrófono/servicios de voz; pruebas heredadas son funciones puras. |
| Dos usuarios, Redis, sesiones en dispositivos y conversación compartida | NO VERIFICADO E2E; no hay infraestructura certificada aislada y falta contrato de conversación. No iniciar aplicaciones sobre datos existentes. |
| Concurrencia PostgreSQL o entrega WS exactamente una vez | NO VERIFICADO. SQLite y secuencias simuladas no reemplazan prueba de locks/múltiples procesos/red. |
| CSRF/JWT de extremo a extremo en nuevas unidades NB | NO VERIFICADO por las unidades extraídas. Se reutiliza solo evidencia de código/pruebas de fase 1 con su alcance. |
| Reejecutar builds/lint/suites completas | Omitido deliberadamente: fuentes iguales, evidencia existente suficiente para dimensiones comparadas, sin cambios/fallos nuevos que lo justifiquen. |
| Corregir dependencias, migraciones, código, prompts o permisos | No autorizado. Solo se crearon scripts/copias nuevas fuera del repositorio e informe final. |

### K.4 Trazabilidad de inspección

Consultas de lectura ejecutadas: Test-Path, git rev-parse/remote/status/ls-files (con safe.directory por comando), Get-Content UTF8 y Select-Object por tramos, Get-Item (VoiceCommand.jsx: 0 bytes), rg --files y rg -n sobre funciones/contratos/tests/IA/WS, lectura de logs T1 y comparación SHA-256 con hashlib. Se leyó el maestro completo y el informe anterior por tramos para evitar truncación de salida. Se verificaron las rutas reales y el control de existencia del informe antes de escribirlo.

Artefactos nuevos únicamente en T2: snapshot.py, baseline.json, initial-git.json, validity.json, nb_handler_probe.py, run_additional.py, django_runner.py, dc_backend/phase2_probe.py y copias de fuentes DB, nb-handler.log, dc-interpret-revision.log, report-body.txt y script/resumen final de creación/verificación. No se agregaron pruebas ni configuración a los repositorios originales. Un primer intento de crear T2 usó New-Item -LiteralPath, parámetro no admitido; falló y se creó un directorio nuevo con -Path. No afectó archivos de proyectos.

No se consultaron fuentes web, servicios conectados ni servidores. No commits/pushes, despliegue, instalación o alteración de infraestructura. Los temporales pueden desaparecer por limpieza habitual del sistema; el informe conserva evidencia, comandos, resultados y límites suficientes.

## L. Recomendación final

1. **¿Conservar la IA actual de NodoBoard? Sí, como único asistente y superficie de integración.** Conservar Angular/Django, chat, entradas y dominio; sustituir o endurecer el mecanismo inseguro de aceptación/ejecución de deltas cuando se autorice. Conservar no significa aprobar sus fallos actuales.
2. **¿Incorporar Diana completa? No está justificado.** No resuelve memoria grupal/individual ni conversación atribuida y trae contratos incompatibles/deuda de revisión/idempotencia. Tampoco existe evidencia de calidad del modelo superior. Un reemplazo excepcional necesitaría evidencia adicional que aquí no existe.
3. **¿Qué aprovechar?** Patrones de operaciones tipadas/allowlist, validación de documento, planes vinculados a usuario y revisión, preview/confirmación, atomicidad, errores estructurados, control de autosave/eco, contexto servidor, factory de proveedor y procesamiento de voz final/TTS opcional. Adaptaciones E1–E10, resolviendo defectos conocidos, sin copiar modelos/JSX/migraciones literalmente.
4. **¿Qué desarrollar directamente en NodoBoard?** Conversaciones y mensajes persistidos/autorizados por proyecto con actor real, difusión grupal, recuperación, contexto grupal e individual y seguimientos; modo de consulta/asesoría separado de mutación; contratos de respuesta/propuesta/plan y moderación. La política de quién puede preguntar no debe heredarse de permisos de editar. Las mejoras del motor seguro se integran en su dominio ORM/snapshot.
5. **¿Qué es redundante?** Segundo chat/personaje, autenticación alternativa, segundo modelo de diagrama y cliente de proveedor paralelo, reemplazo React y un historial corto local presentado como conversación persistente. project.create/JPA no se trasladan por venir incluidos.
6. **¿Qué reduce esfuerzo y riesgo?** Mantener un solo flujo Angular y adaptar límites backend y patrones puros probados. Es una inferencia cualitativa fundada en compatibilidad y superficie afectada; no una estimación cuantificada. Menos riesgo exige arreglar permisos/revisión de todos los escritores relevantes: portar Diana sin esto no es una solución segura. Separación del adaptador/ejecutor/planes sería más mantenible que duplicar asistentes o concentrar todo en una nueva vista/canvas.
7. **¿Qué necesita para el segundo parcial?** Identidad de participante incluida en cada intercambio y respuesta individualizada, preguntas/respuestas compartidas, memoria y recuperación grupal/individual, interpretación/asesoría conceptual evaluada, autorización de mutaciones, confirmaciones y sincronización autoritativa, con proveedor parametrizable y extensión multiproveedor si se requiere. LLM local es opcional y no fuerza reemplazo del proveedor actual.

¿Se pueden fusionar enfoques sin reemplazar el asistente? **Sí, conceptualmente:** conservar experiencia/entradas/política relacional de NB y adaptar el límite determinista validado de Diana. No se han fusionado archivos ni subsistemas durante esta ejecución. Ninguna recomendación exige dos asistentes.

¿En qué es superior cada uno? Diana tiene ventajas concretas comprobadas en validación, permisos/confirmación de planes y testabilidad backend; NB ofrece ajuste nativo al proyecto destino, dominio relacional e interfaz/entrada por imagen ya conectados. La superioridad de inteligencia, asesoría o usabilidad global de cualquiera es **NO VERIFICADA**. Esto permite una recomendación de integración sin inventar una comparación semántica de modelos.

### Verificación final y detención

Se contrastan los 1.886 archivos existentes registrados al inicio de fase 2 y Git de los tres repositorios. La única adición autorizada dentro de los repositorios es este informe. El informe de fase 1 y el maestro se preservan íntegros. El resultado real de comprobación se añade a continuación durante la creación exclusiva del archivo, sin sobrescribir un informe preexistente.

**Resultado final:** 1886 archivos existentes contrastados por SHA-256; **0 diferencias**. Git conserva el estado inicial excluyendo únicamente AUDITORIA_FASE_2.md: **True**.

Git final en D:\Informatica\8vo Semestre\sw1-2-2026\pizarra-colaborativa:

```text
 M frontend/package-lock.json
?? AUDITORIA_FASE_1.md
?? AUDITORIA_FASE_2.md
?? AUDITORIA_MAESTRA.md
?? auditoria-diagramcraft-nodoboard.code-workspace
?? debug.log

```

Git final en D:\swProyecto\backend:

```text
(limpio)
```

Git final en D:\swProyecto\frontend:

```text
(limpio)
```

No se detectaron modificaciones no autorizadas de los archivos registrados. No se revirtieron cambios previos. Única adición en repositorios: NB/AUDITORIA_FASE_2.md. Sin llamadas externas de IA por aplicaciones/pruebas, sin implementación ni avance de fase.

Control editorial: se comprobaron secciones A–L y ausencia de puntuaciones/prioridades. El primer control de encabezados falló por regex del script temporal; se corrigió ese control y pasó. El primer guardado exclusivo creó este archivo nuevo vacío, pero falló por un parámetro de salto de línea. Se verificaron sus cero bytes y creación posterior al script de esta ejecución; se completó mediante append, sin truncar ni sobrescribir contenido previo. Scripts/resultados temporales: check_staged.py, check_staged_v2.py, create_report.py, complete_report.py y final-verification.json.

**FASE 2 FINALIZADA. EJECUCIÓN DETENIDA. No continuar a fase 3 sin autorización expresa del usuario.**

