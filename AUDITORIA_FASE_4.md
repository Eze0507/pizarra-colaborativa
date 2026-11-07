# Auditoría — Fase 4 de trabajo: evaluación cuantitativa y priorización preliminar

Fecha de referencia: 30 de octubre de 2026, America/La_Paz. Evaluación local; ninguna recomendación ha sido implementada.

## A. Resumen ejecutivo

**La alternativa preliminar sustentada por las auditorías sigue siendo conservar Angular + Django, el editor y un único asistente de NodoBoard, adaptando controles concretos de DiagramCraft y desarrollando las capacidades conversacionales que ninguno posee.** La puntuación no convierte un módulo donante en una solución lista para incorporar.

Se evalúan 32 funcionalidades consolidadas, sin ordenarlas por puntuación. 26 tienen total numérico y 6 quedan NO EVALUABLES (F08, F09, F17, F20, F23, F29). Los totales evaluables van de 19.0 a 80.0 /100; no hay alternativas del inventario que alcancen 85 con la evidencia actual. Las notas son juicios técnicos calibrados por una rúbrica explícita, no mediciones de inteligencia, tiempos reales o probabilidades. La evidencia permite reproducir el cálculo y discutir cada juicio; no elimina la incertidumbre.

Las brechas académicas que requieren DESARROLLO NUEVO son F16 (mensajes grupales atribuidos y respuestas dirigidas), F17 (memoria grupal/individual y seguimientos), F18 (historial persistido/recuperable) y F20 (moderación/asesoría contextual de equipo). Sus estimaciones no son pruebas de una implementación. F17 y F20 quedan sin total numérico por calidad/garantías no evaluables; **siguen siendo P0 por obligatoriedad**. F16 y F18 tienen estimación de viabilidad apoyada en componentes reutilizables, no calidad de mensajes/historial ya implementados.

Las capacidades adaptables de DiagramCraft incluyen validación determinista, planes/confirmación, revisión, contexto autorizado, deduplicación con correcciones y presencia/reconexión. La escritura y revocación de permisos, los snapshots antiguos y la reconciliación necesitan atención P0 por seguridad/integridad, independientemente de la nota de una solución particular. No corresponde copiar las garantías incompletas del donante.

XMI de NodoBoard debe conservarse como base. El fallo X3 (nueve clasificadores de la fixture NB → cero nodos en parser DC sin errores) es reproducido; no acredita un borrado real ni que toda exportación XMI sea incompatible. Preview/límites del donante son aprovechables tras adaptar perfiles y exigir revisión al confirmar. La generación Spring añade una capacidad real por código y ZIP/texto, pero no es requisito explícito del chat y la compilación Java no se verificó. Ambas se mantienen separadas de las brechas académicas.

No hay evidencia de superioridad de comprensión de Gemini entre proyectos. Tampoco es obligatorio cambiar entre varios proveedores o ejecutar un LLM local: el maestro exige proveedor configurable, y deja modelo local opcional. La parametrización existente de Gemini es una base a conservar y verificar, con un adaptador único como mejora.

### Correspondencia de alcance

Esta fase 4 de trabajo utiliza los apartados 7 (matriz), 8 (puntuación), 9 (prioridades), 10 (esfuerzo/riesgo) y 11 (requisitos académicos) del maestro. Los análisis de alternativas y recomendaciones son preliminares. No se ejecutan sus apartados 12 (ranking definitivo), 13 como selección final ni 14 como plan/informe final de migración. No se repiten las auditorías técnicas 1–3, ni se desarrolla el segundo parcial.

### Identidad y estado inicial

| Alias | Ruta real verificada | Origin | Rama | HEAD |
|---|---|---|---|---|
| NB | D:\Informatica\8vo Semestre\sw1-2-2026\pizarra-colaborativa | https://github.com/Eze0507/pizarra-colaborativa.git | feat/integrar-diagramcraft | df5430d221ddfbdc23e0a7882e535dc402ceafc4 |
| DB | D:\swProyecto\backend | https://github.com/juanse8202/swbackend.git | main | 125dc3b72fed6a829299d5733f31277d0c789a1c |
| DF | D:\swProyecto\frontend | https://github.com/juanse8202/swfrontend.git | main | e200fc82b2fa6cb3b79e62b5411a6942ccd0cc7a |

Cada alias NB, DB o DF se resuelve desde estas rutas. Se comprobaron existencia, raíz Git y origin antes de evaluar. AUDITORIA_FASE_4.md no existía; se creará con modo exclusivo. No se encontraron AGENTS.md mediante búsquedas dentro de los repositorios; se mantiene la aplicación de instrucciones locales ya leídas y la skill diagramcraft-ai-uml-platform como guía, sin considerar sus capacidades descritas como evidencia de código.

Estado inicial NB:

~~~text
 M frontend/package-lock.json
?? AUDITORIA_FASE_1.md
?? AUDITORIA_FASE_2.md
?? AUDITORIA_FASE_3.md
?? AUDITORIA_MAESTRA.md
?? auditoria-diagramcraft-nodoboard.code-workspace
?? debug.log
~~~

DB y DF están limpios. Se conservan todos los cambios preexistentes. No se modificó configuración de Git; safe.directory se suministró sólo a cada comando y --no-optional-locks evitó escrituras opcionales.

### Vigencia y contradicciones resueltas sólo en este informe

Los cuatro documentos fueron leídos completos, usando tramos cuando una salida se truncó. Los 1885 archivos inventariados en fase 1, 1886 en fase 2 y 1887 en fase 3 siguen idénticos por SHA-256. Sus commits coinciden. El inventario inicial actual contiene 1888 archivos existentes rastreados/no ignorados. Esto respalda vigencia de fuentes, no identidad de todo node_modules/.venv ignorado ni de servicios reales.

| Documento conservado | Bytes | SHA-256 |
|---|---|---|
| AUDITORIA_MAESTRA.md | 29803 | e31d7c76755987a6542d033720f65276d3dbe1db5ff8026eb8405498d9deca41 |
| AUDITORIA_FASE_1.md | 43325 | 9f696d650923ca4b27da9c0d4a4b4215f9b8bda85783f702f6c631326f6d180c |
| AUDITORIA_FASE_2.md | 73304 | 0c229547359d479c290ba3c51bac714c854feec788e1152de6b4e97839405d0a |
| AUDITORIA_FASE_3.md | 98399 | 3d6c99f155e4120c8675a6af1f79160f4a0f9a2ca7e83826e62acc38be511325 |

Se adoptan estas precisiones documentales sin editar informes previos:

- La fase 1 enumeró authStore/AppRouter/ProjectsPage/ActiveUsers como parte del frontend. Fase3 y lectura actual acreditan cinco archivos vacíos, incluido VoiceCommand. La cadena real es main → App → autenticación o DiagramCanvas. F30 no les adjudica capacidad.
- La validez del roundtrip XMI NB y las pruebas internas DC no certifican compatibilidad cruzada. X3 agrega un perfil fallido; no invalida los conteos NB ni todos los perfiles DC.
- H-N03 (pérdida secuencial por snapshot viejo) no es lo mismo que R3 (dos heurísticas de reconciliación en método Angular). Ambos se tratan en F06, pero sólo el primero probó borrado persistido.
- S3 reproduce handlers sin cierre y entrega posterior simulada; no acredita explotación de red completa. La revalidación de escritura DC sigue existiendo.
- La tabla H12 de fase 2 interpretó configuración como diferentes proveedores. El texto literal R19 del maestro exige proveedor configurable; **no exige múltiples marcas simultáneas ni un modelo local**. F32 conserva parámetros y evalúa separación del adaptador; F29 trata extensión opcional.
- La carencia de memoria/conversación es verificable por modelos/requests/eventos. La calidad conceptual y de moderación del modelo sigue NO VERIFICADA: no se deduce incapacidad semántica de una ausencia de infraestructura ni éxito de un mock.

## B. Metodología

### Criterios, fórmula y evidencia

| Clave | Criterio exacto | Peso |
|---|---|---:|
| R | Relevancia para el segundo parcial | 25 |
| B | Beneficio funcional frente a NodoBoard | 20 |
| C | Compatibilidad arquitectónica | 15 |
| I | Facilidad de integración | 15 |
| Q | Calidad, seguridad y pruebas existentes | 10 |
| M | Mantenibilidad futura | 10 |
| U | Impacto positivo en la experiencia del usuario | 5 |
| Total | | 100 |

Para cada criterio se asigna g entre 0 y 5. Contribución = g/5 × peso; puntuación = suma de las siete contribuciones, redondeada a un decimal. No se agregan esfuerzo, riesgo o confianza como pesos adicionales. Las notas enteras producen contribuciones enteras con estos pesos, pero se muestra siempre un decimal.

Interpretación obligatoria: 85–100 Muy recomendable para migrar o adaptar; 70–84,9 Recomendable, sujeto a dependencias; 50–69,9 Conveniencia condicionada; 30–49,9 Baja conveniencia; 0–29,9 No recomendable actualmente. Estas etiquetas describen conveniencia de la alternativa evaluada; no convierten CONSERVAR en MIGRAR y no anulan vetos de seguridad o arquitectura.

Calibración aplicada:

| Nota | R | B | C | I | Q | M | U |
|---|---|---|---|---|---|---|---|
| 5 | Requisito explícito o garantía indispensable de seguridad/colaboración | Cubre brecha ausente o bloqueo de integridad | Nativo al destino, sin cambio de arquitectura | Conservar con comprobación focalizada | Cobertura suficiente y garantías integradas demostradas | Límites claros, contratos y pruebas con alta reutilización | Beneficio directo para participación/claridad y control |
| 4 | Prerrequisito amplio del modelador seguro | Mejora importante sobre mecanismo parcial/defectuoso | Encaja en Django/Angular con contrato acotado | Adaptación localizada en módulos existentes | Contrato probado sólidamente en su límite | Separación y contratos reutilizables | Mejora clara y localizada de interacción |
| 3 | Apoyo importante al uso/cumplimiento | Capacidad adicional útil | Adaptación de DTO/roles/agregado | Varios módulos, alcance identificable | Pruebas parciales o garantías conocidas con límites | Mantenible si se define y aísla el alcance | Beneficio indirecto/limitado al flujo |
| 2 | Capacidad útil no obligatoria | Refinamiento frente a capacidad existente | Diferencias importantes de dominio/estado | Modelos, API y UI con integración transversal | Sólo bases reutilizables o cobertura débil | Acoplamiento/mantenimiento significativo | Beneficio pequeño o afectado por regresiones |
| 1 | Complementaria/opcional | Incremento marginal | Incompatibilidad material/reescritura amplia | Adaptación grande o sin algoritmo de alto nivel reutilizable | Evidencia mínima o defectos relevantes | Duplicación y deuda importantes | Incremento mínimo en destino |
| 0 | Sin relación útil con alcance | Ningún beneficio incremental de sustitución | Viola restricción arquitectónica | Traslado literal inviable en alcance o reconstrucción completa | No garantías aplicables y evidencia negativa suficiente | Sin solución sostenible en condiciones evaluadas | Sin beneficio identificado |

Esta rúbrica hace explícitos los juicios; no los convierte en medición empírica objetiva. Cada fila tiene sus razones particulares en D. Q valora el límite real probado, no el volumen de código. C y M son estimaciones de adaptación sustentadas en arquitectura; U es beneficio esperado, no estudio de usuarios.

### Tratamiento de incertidumbre y desarrollo nuevo

Un dato desconocido es NO EVALUABLE (NE), nunca cero. Si cualquier criterio es NE, el **total es NO EVALUABLE**: no se prorratea ni se normaliza sobre el resto. Se muestran las notas conocidas para conservar la trazabilidad. INVESTIGAR corresponde a alternativas cuya conveniencia aún no puede decidirse. Si la ausencia del requisito obligatorio sí está acreditada, se conserva DESARROLLO NUEVO como clasificación de la brecha aunque su total quede NE; la solución concreta requiere investigación. Esto concilia ambas reglas sin ocultar la obligación.

F16/F18 tienen C/I/M/U estimados sobre ORM/DRF/Channels/Angular existentes; Q=2 califica sólo esas bases reutilizables con sus fallos y cobertura parcial. **No otorga calidad probada al módulo nuevo**, a sus mensajes ni a su historial. F17/F20 no tienen una base equivalente de memoria/evaluación de moderación que permita asignar Q razonablemente: queda NE. No se penaliza su inexistencia con cero. La capacidad real del modelo no se puntúa en esas filas ni en la interpretación estructural F10/F19.

ALTA significa evidencia suficiente del estado/límite que motiva la decisión; no una garantía sobre una integración futura. MEDIA indica evidencia parcial o estimación de diseño razonable. BAJA expresa incógnitas materiales. Prioridad del problema se separa de conveniencia de solución; las notas no se suman entre funcionalidades. Las dependencias compartidas no representan varios beneficios acumulables en un puntaje global.

### Esfuerzo, riesgo y gates

Esfuerzo 1: preservar/verificar alcance localizado; 2: cambio pequeño de servicio/componente; 3: varios módulos con contrato conocido; 4: API/datos/frontend y pruebas transversales; 5: agregado/estado o funcionalidad nueva compleja con migraciones y validación extensas. Son escalas ordinales, no días ni presupuesto. Si no hay alcance suficiente se indica NE.

Riesgo 1 muy bajo, 2 bajo, 3 moderado, 4 alto, 5 crítico. El número es exposición estimada de una integración defectuosa/condiciones actuales, **no probabilidad medida ni prueba de explotación**. La justificación por fila señala seguridad, integridad o regresión. Un riesgo5 es veto para trasladar sin resolver controles; no se compensa con puntos.

P0: requisito obligatorio o bloqueo de seguridad/integridad; P1: mejora importante; P2: útil no imprescindible; P3: complementaria/redundante/costosa sin justificación. Una fila CONSERVAR/P0 significa proteger una base necesaria, no programar su reescritura. Una fila NE/P0 puede representar una obligación clara cuya solución no está evaluada. No se fija secuencia temporal, sprint ni ranking definitivo.

## C. Inventario consolidado

Cada ID delimita una capacidad; sus subfunciones se evalúan juntas para no puntuar varias veces lo equivalente. F01 reúne edición básica y gestos; F02 UML ampliado/métodos; F03 validación; F06 revisión y reconciliación; F07 presencia/reconexión. F10 interpreta operaciones, F11 confirma/aplica plan y F12 identifica reintentos: son límites distintos que dependen entre sí, no tres implementaciones de una misma orden. Spring/F24 incluye capas, persistencia y validación del código generado, sin puntuación separada por cada archivo. F16 comparte mensajes/actor/destinatario; F17 usa el historial de F18, pero memoria para contexto y recuperación de registros son capacidades diferentes.

| ID / funcionalidad | Estado NB | Aporte DC real | Decisión preliminar | Evidencia |
|---|---|---|---|---|
| F01 Editor base: entidades/clases relacionales, atributos y operaciones visuales | Parcial: Angular/JointJS y ORM conectados; tsc y persistencia acotada | Editor React Flow conectado; no sustituir motor | CONSERVAR | E01,E02 |
| F02 UML ampliado: kinds, métodos, realización/dependencia y ownership | Sin métodos/kinds diferenciados y sólo cuatro relaciones | Contrato de seis relaciones, métodos y kinds validado | ADAPTAR | E01,E03 |
| F03 Validación determinista del dominio, tipos y multiplicidades | Validación parcial; tipos/deltas débiles y bigint degradado | Serializer/operaciones con reglas y tests | ADAPTAR | E01,E03,E07,E14 |
| F04 Autenticación JWT, proyectos e invitaciones base | Flujos propios; tres tests de proyectos y aceptación interna conectada | Sesión/CSRF/allauth y proyectos con otro contrato | CONSERVAR | E02,E04 |
| F05 Autorización uniforme y revocación REST/WS | Defectos reproducidos en PATCH y rutina snapshot tras revocación | Revalida escritura; S3 no cierra lectura y legacy vulnerable | ADAPTAR | E04,E05,E06 |
| F06 Revisión, reconciliación y guardado autoritativo | Snapshot obsoleto elimina entidades; R3 reintroduce relaciones por heurística | expected_revision/lock/409 y filtros de estado; carrera F2 conocida | ADAPTAR | E05,E07,E08 |
| F07 Conectividad colaborativa: presencia, reconexión y resync | Presencia por proceso y sin retry efectivo localizado | Presencia ORM/TTL, heartbeat y hook retry con buffer limitado | ADAPTAR | E06,E08,E09 |
| F08 Bloqueo fuerte por elemento con lease | Avisos visuales y set por conexión; no exclusión fuerte acreditada | No equivalente de lease fuerte verificado | INVESTIGAR | E05,E09 |
| F09 Undo/redo colaborativo seguro | Sin equivalente colaborativo sólido verificado | Historial local de 50 snapshots, no inversas concurrentes | INVESTIGAR | E10 |
| F10 Lenguaje natural a operaciones estructuradas del modelador | Delta cliente conectado, sin validación runtime estricta | execute_operations y gramáticas/fakes probados | ADAPTAR | E03,E07,E11 |
| F11 Plan IA persistido, preview y confirmación autorizada | Aplicación inmediata al éxito; sin PlanIA equivalente | Plan usuario/diagrama/TTL, confirmación y aplicación atómica | ADAPTAR | E07,E11,E12 |
| F12 Dedupe, retry e identidad de solicitud/aplicación | Busy flag no es idempotencia persistida | request_id/hash y resultado, con retry409 y sin unique compuesto | ADAPTAR | E07,E12 |
| F13 Contexto autoritativo del diagrama y selección | Contexto cliente omite multiplicidades; no revisión | build_diagram_summary de documento autorizado y selección | FUSIONAR | E07,E11 |
| F14 Voz: conservar push-to-talk y adaptar transcripción final | Entrada implementada por código con provisionales acumulados | isFinal/dedupe/estados probados en utilidades; matiz wake/send | ADAPTAR | E13 |
| F15 Síntesis de voz opcional | Sin speechSynthesis conectado localizado | speakDiana y dianaVoice: selección/segmentación probadas | ADAPTAR | E13 |
| F16 Chat grupal: preguntas/respuestas compartidas, actor y destinatario | mensajesChat local, sin broadcast de conversación | aiHistory local; PlanIA.usuario no es mensaje grupal | DESARROLLO NUEVO | E04,E06,E15,R2-R7 |
| F17 Memoria grupal/individual y continuidad de seguimientos | No historia enviada ni memoria por actor | Sin memoria conversacional; resumen sólo de diagrama | DESARROLLO NUEVO | E15,E16,R8-R11 |
| F18 Persistencia y recuperación autorizada del historial IA | Array volátil y limpiarHistorial local | Seis entradas locales; planes guardados no son diálogos | DESARROLLO NUEVO | E04,E15,R18 |
| F19 Consulta conceptual de sólo lectura separada de mutación | Prompt permite mensaje sin delta; fake200 verificado | Sin modo answer; contrato de operaciones/clarificación | FUSIONAR | E07,E11,E16,R12 |
| F20 IA moderadora/asesora contextual del equipo y recomendaciones | Intención conceptual; no flujo de moderación de equipo | Planes de modelado; no moderación grupal equivalente | DESARROLLO NUEVO | E15,E16,R13-R14 |
| F21 XMI actual de NodoBoard: conservar entrada/salida | Fixture importa/exporta/reimporta9/33/10; límites semánticos | Otro perfil parser; X3 incompatible con fixture NB | CONSERVAR | E14,E17 |
| F22 XMI: perfiles compatibles, límites seguros y preview versionado | Importación directa, sin preview equivalente | Límites/mapping/dry_run útiles; X3 y preview sin expected_revision | FUSIONAR | E14,E17,E18 |
| F23 Interoperabilidad semántica/visual certificada con EA | Conteos de fixture, sin EA manual | Perfiles/layout probados parcialmente, sin vuelta EA real | INVESTIGAR | E14,E17 |
| F24 Exportación Spring Boot por capas y validación del artefacto | No generador Java conectado; generador sólo XML | ZIP Maven/Java21/Spring3.4/PostgreSQL; repos/service/controller/DTO/mapper | MIGRAR | E03,E19 |
| F25 Ciclo de proyectos: archivar/restaurar/duplicar y roles extendidos | Base proyectos e invitaciones propia | Acciones/servicios específicos, con tests PG pendientes | ADAPTAR | E02,E04,E20 |
| F26 Errores estructurados, foco y accesibilidad básica | Toasts/roles/labels, errores heterogéneos | Códigos/element_id, Escape/aria-live y enfoque | FUSIONAR | E08,E16,E21 |
| F27 Contratos, separación de responsabilidades y pruebas de frontera | Servicios propios; tests IA vacíos y entorno NB no fiel | Módulos/fakes/tests útiles, Canvas concentrado y deuda | ADAPTAR | E01,E08,E11,E22 |
| F28 Entrada por imagen de NodoBoard | Endpoint/compresión/normalización conectados, proveedor no probado | Sin equivalente de boceto a diagrama localizado | CONSERVAR | E07,E23 |
| F29 Proveedor alternativo/LLM local opcional | Parámetros Gemini; sin adaptador local/multiproveedor conectado | Factory Gemini y gramática; no LLM local real | INVESTIGAR | E07,E11,E24,R20 |
| F30 Incorporación integral de Diana/React/auth/ORM legacy | Un asistente Angular y dominio propio activos | UI/estado/sesión/legacy completos pero no chat grupal persistente | DESCARTAR | E02,E06,E15,E25 |
| F31 Completar enlace de invitación firmado sin reemplazar invitaciones | Backend genera /invitacion/token; Angular no tiene ruta | Flujo distinto de invitaciones en API, no parche directo | ADAPTAR | E02,E26 |
| F32 Proveedor IA configurable y adaptador único en backend | GEMINI_API_KEY/MODEL y SDK declarado | get_ai_provider separado, SDK ausente en requirements | FUSIONAR | E07,E11,E24,R19 |

### Registro trazable de evidencia

Las referencias siguientes son la evidencia común de C/D/E/F/G/L; cada fila cita una o varias. Las pruebas siguen siendo las ejecutadas en su fase original, no ejecuciones nuevas.

| ID | Fuente original y comportamiento acreditado | Auditoría/prueba y límite |
|---|---|---|
| E01 | NB/backend/modelado/models.py::Proyecto,Entidad,Atributo,Relacion; frontend/src/app/features/whiteboard/services/whiteboard-entity.service.ts, whiteboard-relationship.service.ts, whiteboard-canvas.service.ts, diagrama-parser.service.ts | F1§4/P07/P17; F3§B/E/I. Editor conectado, persistencia acotada y tsc; no todos los gestos/template |
| E02 | NB/backend/modelado/views.py::ProyectoListCreateView,ProyectoDetailView y vistas de invitaciones; usuario/models.py::UserColaborador; Angular dashboard/projects.service.ts, invitaciones.service.ts y app.routes.ts | F1 tres tests de proyectos; F3§B/E/H. Aceptación interna existe; SMTP y navegador pendientes |
| E03 | DB/diagramas/serializers.py::DiagramaSerializer; ai_operations.py::execute_operations; DF/src/stores/diagramStore.js y components/editor/PropertiesPanel.jsx | F1 diagramas/tests.py de miembros, seis relaciones/JPA; F2§C/D; F3§D/I. JSON no intercambiable con ORM NB |
| E04 | NB/backend/usuario/views.py, serializers.py y models.py; core/asgi.py; DB/config/authentication.py y proyectos/permissions.py::role_for,require_role,require_owner | F1 config6/6, pruebas NB subset; F3§B/C/H. JWT vs sesión, roles diferentes; no auth global certificada |
| E05 | NB/backend/modelado/views.py::ProyectoDetailView; consumers.py::PizarraConsumer._guardar_snapshot_db/receive | F1 H-N01/H-N02/H-N03: PATCH visualizador, snapshots visualizador/revocado y borrado por snapshot viejo en rutina aislada; no ataque red completo |
| E06 | DB/diagramas/consumers.py::DiagramaConsumer.member_removed,diagram_update,save_diagram_if_user_can_access; proyectos/realtime.py; DF/src/components/editor/DiagramCanvas.jsx::onSocketMessage | F3 S3: AST de handlers, no cierre y update posterior enviado; escritura revalidada, cliente obedece retiro; Redis/handshake sin prueba |
| E07 | NB/backend/asistente/views.py::EjecutarInstruccionAsistenteView.post, GenerarDiagramaDesdeImagenView; asistente-ia.service.ts::extraerContextoDiagrama/procesarDelta | F2 siete probes: delta mal tipado200, contexto sin cardinalidad/actor/historia, mensaje fake sin delta; F1 H-N04. No proveedor real |
| E08 | DB/diagramas/views.py::DiagramaViewSet.perform_update y consumers.py::save_diagram_if_user_can_access; DF/src/utils/collaborationSync.js y DiagramCanvas autosave | F1 tests de expected_revision y WS obsoleto; F3§D/H. Normalización WS raw difiere de validated_data por inspección; sin PG multiworker |
| E09 | DB/diagramas/models.py::PresenciaDiagrama y consumers.py register_presence/active_members; DF/src/hooks/useDiagramSocket.js; NB WhiteboardSocketService | F3§D/F: TTL45s, heartbeat20s, retry2s/buffer último evento; NB memoria por proceso y envío se descarta desconectado. E2E pendiente |
| E10 | DF/src/stores/diagramStore.js::undo,redo,restore y DiagramCanvas que programa save | F3§F/G/K; historial50 snapshots, no operaciones inversas colaborativas probadas |
| E11 | DB/diagramas/ai_interpreter.py::validate_interpret_request,validate_provider_response,build_diagram_summary,get_ai_provider y ai_operations.py; DF/src/api/aiApi.js | F1 tests locales/fakes; F2§C/D. Ready requiere operaciones; no answer conversacional ni LLM local |
| E12 | DB/diagramas/models.py::PlanIA, ai_plans.py::create_plan/apply_plan, views.py::interpretar_ia/aplicar_plan_ia; DF/DiagramCanvas y utils/aiFlow.js | F1 H-D03 retry409, tests de permisos/TTL/lote; F2 H2-D01 revisión refrescada tras fake proveedor. Índice request_id no unique; entrega única no probada |
| E13 | NB AsistenteIaService.iniciarReconocimientoVoz/detenerReconocimientoVoz; DF/DiagramCanvas onresult/speakDiana, src/utils/aiFlow.js,dianaVoice.js | F2§B/C/D y Node de utilidades; finales/parciales/wake-send conocidos; micrófono/TTS reales pendientes |
| E14 | NB/backend/generador/services/xmi_importer.py::XMIImporter.importar_xml y _mapear_tipo_dato, xmi_exporter.py::XMIExporter.exportar_xml; serializers.py y GeneradorService | F1 fixture9/33/10 y bigint→integer; F3§D/H. Conteos no igualdad semántica/EA |
| E15 | NB/backend/asistente/models.py placeholder; ChatAsistenteIaComponent.mensajesChat/limpiarHistorial; DB/diagramas/models.py::PlanIA sin mensajes; DF/src/components/editor/DiagramCanvas.jsx::addAiHistory | F2§B/C/H y F3§A/F/N; request/eventos sin conversación compartida. Autenticación/planes no equivalen a actor/historia enviados al modelo |
| E16 | NB SYSTEM_PROMPT_INSTRUCCIONES y post; DB/diagramas/ai_interpreter.py::_prompt,validate_provider_response; resumen sin historial/actor | F2 test conceptual fake sólo transporte y test omisión de contexto; recomendaciones/moderación/seguimientos no probados |
| E17 | NB/backend/generador/fixtures/diagramaExamen.xml y exportador; DB/diagramas/xmi.py::_attr,parse_xmi | F3 X3 y T3/cross-xmi-final.log: nueve packagedElement→0nodes/0edges/errors[],warning ea_core_only; namespace viejo no reconocido. No reemplazo real |
| E18 | DB/diagramas/xmi.py::parse_xmi/apply_xmi_mapping/export_xmi y views.py::importar_xmi; DF/src/api/xmiApiContract.js, utils/xmiImport.js | F1 tests internos XML/preview y F3§D/H: límites2MB/20000/depth100, lxml sin DTD/red, dry_run y selección. Confirmación sin expected_revision por inspección |
| E19 | DB/diagramas/spring_generator.py::normalize_diagram/generate_spring_boot_zip, UmlNode; views.py::generar_spring_boot; DF/src/api/diagramApi.js | F1 ZIP/texto y F3§D/H/L: Maven/Java21/Spring3.4/Postgres, capas y JPA; generated_java_compiles no ejecuta javac |
| E20 | DB/proyectos/views.py::ProyectoViewSet, models.py/permissions.py/services.py::create_project_with_main_diagram; DF/src/components/editor/ProjectsDialog.jsx | F1 suite proyectos4pasan/1 fallo/15 errores jsonb_array_length SQLite; F3§C/H. Archivo/restauración/duplicado son capacidades por código, no ciclo E2E certificado |
| E21 | DB/diagramas/api_errors.py y errores de generador; DF/DiagramCanvas, hooks/useEscapeClose.js; NB ToastNotificationService y modales/chat | F2/F3 contratos de error/foco y roles/aria por fuente; lector de pantalla/teclado pendientes |
| E22 | NB/backend/requirements.txt y frontend/package.json/lock; DB/requirements.txt, diagramas/tests.py; DF/src/**/*test.js | F1 suite85:69 pasan/1 fallo/15 errores; Node28pasan/lint/build; NB tsc pero build/Karma bloqueados; F3§J/N versiones distintas |
| E23 | NB/backend/asistente/views.py::GenerarDiagramaDesdeImagenView; AsistenteIaService.generarDiagramaDesdeImagen y WhiteboardPage.onDiagramaIAGenerado | F2§B/F; flujo identificado, imagen/proveedor real no probados |
| E24 | NB/backend/core/settings.py::GEMINI_API_KEY/GEMINI_MODEL y requirements.txt; DB/diagramas/ai_interpreter.py::GeminiInterpreter/get_ai_provider y requirements.txt | F1 H-D02, F2 C01/C22, F3§J. Parámetros existentes, adaptador separado DC, SDK ausente en manifiesto/env DC |
| E25 | DF/src/main.jsx,App.jsx,components/editor/DiagramCanvas.jsx; AppRouter/authStore/ProjectsPage/ActiveUsers/VoiceCommand vacíos; DB ClaseUMLViewSet.perform_update | F3 F3 corrección de inferencia; F1 H-D04 mover registro legacy al diagrama ajeno. No autoridad del canvas ni ventaja de copiar React |
| E26 | NB/backend/modelado/serializers.py::InvitarColaboradorSerializer genera /invitacion/token; AceptarInvitacionView; Angular app.routes.ts | F3 I3 inspección y contraste actual. No ruta invitacion, sí activar/:token y notificaciones internas; no correo real |

Para rutas abreviadas de Angular: todos los servicios de whiteboard están en NB/frontend/src/app/features/whiteboard/services; ChatAsistenteIaComponent en components/chat-asistente-ia; WhiteboardPage en pages/whiteboard. Las abreviaturas DF/DiagramCanvas se refieren a DF/src/components/editor/DiagramCanvas.jsx. Las secciones de informes citadas contienen endpoints y recorridos originales; no se inventan rutas nuevas.

### Cobertura exhaustiva del enunciado académico

R1–R20 corresponden a los 20 requisitos de AUDITORIA_MAESTRA.md§11. R20 es opcional; R1–R19 se consideran obligatorios a los efectos de esta evaluación. El propósito moderador del párrafo inicial se vincula a F20. Parcial no equivale a cumplimiento completo ni a ausencia total.

| Req. | Necesidad | NodoBoard | DiagramCraft | Evidencia / salida evaluada |
|---|---|---|---|---|
| R1 | Dispositivos/sesiones independientes | Parcial: JWT/Channels y tablero por proyecto | Parcial: sesión/Channels/presencia | E04/E09; CONSERVAR F04 y ADAPTAR F07; dos dispositivos no probados |
| R2 | Chat grupal visible | No implementado como hilo compartido | No implementado | E15; DESARROLLO NUEVO F16 |
| R3 | Cualquier integrante pregunta | Entrada autenticada local; sin canal grupal/política por proyecto completa | Interpretación restringida a EDIT_ROLES, no consulta de reader | E07/E11/E15; DESARROLLO NUEVO F16 para participación grupal; preguntar no es editar |
| R4 | Todos ven preguntas | No implementado | No implementado | E15; F16 nuevo, sin puntuación duplicada de R2 |
| R5 | Todos ven respuestas | No implementado | No implementado | E15; F16 nuevo |
| R6 | IA identifica participante | Autenticación existe; actor no llega al contexto conversacional | PlanIA.usuario existe; actor no llega al contexto conversacional | E04/E07/E15; F16 nuevo sobre identidad existente |
| R7 | Respuesta individualizada mencionando actor | Sin flujo atribuido conectado | Sin flujo atribuido conectado | E15/E16; F16 nuevo; exactitud de personalización futura pendiente |
| R8 | Contexto general de equipo | Contexto de diagrama parcial, no memoria de diálogo | Resumen autorizado del diagrama, no memoria de equipo | E07/E11/E15/E16; F17 nuevo usa F13, no confundir ambos contextos |
| R9 | Contexto individual | No implementado | No implementado | E15/E16; F17 nuevo; separar actor dentro del contexto compartido no presupone chat privado oculto |
| R10 | Comprende seguimiento | Sin envío de historia; calidad real no verificada | Igual carencia de historia; calidad no verificada | E16; F17 nuevo para continuidad, evaluación semántica pendiente |
| R11 | Distingue diálogos individuales dentro del grupo | No implementado | No implementado | E15/E16; F17 nuevo con actor/orden de conversación |
| R12 | Dudas conceptuales | Parcial: prompt y transporte fake sin delta | Sin modo answer; inteligencia no probada | E16; F19 FUSIONAR intención existente con contrato seguro; calidad no evaluable como éxito real |
| R13 | Asesora diseño UML | Intención conceptual/contexto parcial; desempeño no verificado | Operaciones/resumen no prueban asesoría | E11/E16; F19 parcial y F20 DESARROLLO NUEVO de flujo asesor grupal |
| R14 | Recomienda mejoras | Sin flujo de recomendaciones de equipo acreditado; capacidad modelo no probada | Plan ejecutable no equivale a consejo contextual | E16; F20 DESARROLLO NUEVO de política/flujo, no afirmar que un LLM carece de conocimiento |
| R15 | Interpreta modificaciones | Parcial: deltas cliente | Parcial: gramáticas/fake/operaciones tipadas | E07/E11; ADAPTAR F10, calidad de NL abierto no verificada |
| R16 | Autoriza cambios cuando corresponde | Sin plan/confirmación IA conectados | Plan/confirmación backend probados, con límites F2 | E12; ADAPTAR F11 y permisos F05 |
| R17 | Sincroniza cambios autorizados | Parcial; defectos permisos/revisión | Parcial; revisión/WS y fakes, E2E pendiente | E05/E08/E09; ADAPTAR F05/F06/F07/F12 |
| R18 | Conserva y recupera historial | No implementado; sólo array | No implementado; planes no son diálogo | E15; DESARROLLO NUEVO F18 |
| R19 | Proveedor configurable | Key/modelo Gemini configurables; servicio real pendiente | Configuración/factory Gemini; SDK no declarado | E24; F32 FUSIONAR y conservar parámetros; multiproveedor no obligatorio |
| R20 | LLM local opcional | No implementado | No implementado; parser no es LLM | E24; F29 INVESTIGAR, P3; no se etiqueta como obligación ni migración existente |

No se ha marcado como disponible en el donante ningún requisito nuevo. Para requisitos parciales se distingue la parte reutilizable del flujo faltante; no se afirma inexistencia absoluta porque falte una prueba de proveedor.

## D. Matriz de puntuación

En cada celda se muestra **nota /5 → contribución ponderada**. NE propaga el total a NO EVALUABLE. El orden es el inventario temático, no un ranking.

| ID / alternativa | Base de evaluación | R | B | C | I | Q | M | U | Total /100 | Interpretación |
|---|---|---|---|---|---|---|---|---|---|---|
| F01 Editor base: entidades/clases relacionales, atributos y operaciones visuales | BASE/ADAPTACIÓN | 4/5 → 20.0 | 0/5 → 0.0 | 5/5 → 15.0 | 5/5 → 15.0 | 2/5 → 4.0 | 4/5 → 8.0 | 4/5 → 4.0 | 66.0 | Conveniencia condicionada |
| F02 UML ampliado: kinds, métodos, realización/dependencia y ownership | BASE/ADAPTACIÓN | 2/5 → 10.0 | 3/5 → 12.0 | 2/5 → 6.0 | 2/5 → 6.0 | 4/5 → 8.0 | 3/5 → 6.0 | 3/5 → 3.0 | 51.0 | Conveniencia condicionada |
| F03 Validación determinista del dominio, tipos y multiplicidades | BASE/ADAPTACIÓN | 4/5 → 20.0 | 4/5 → 16.0 | 3/5 → 9.0 | 3/5 → 9.0 | 4/5 → 8.0 | 4/5 → 8.0 | 4/5 → 4.0 | 74.0 | Recomendable, sujeto a dependencias |
| F04 Autenticación JWT, proyectos e invitaciones base | BASE/ADAPTACIÓN | 5/5 → 25.0 | 0/5 → 0.0 | 5/5 → 15.0 | 5/5 → 15.0 | 3/5 → 6.0 | 4/5 → 8.0 | 4/5 → 4.0 | 73.0 | Recomendable, sujeto a dependencias |
| F05 Autorización uniforme y revocación REST/WS | BASE/ADAPTACIÓN | 5/5 → 25.0 | 5/5 → 20.0 | 3/5 → 9.0 | 2/5 → 6.0 | 2/5 → 4.0 | 4/5 → 8.0 | 4/5 → 4.0 | 76.0 | Recomendable, sujeto a dependencias |
| F06 Revisión, reconciliación y guardado autoritativo | BASE/ADAPTACIÓN | 5/5 → 25.0 | 5/5 → 20.0 | 3/5 → 9.0 | 2/5 → 6.0 | 3/5 → 6.0 | 4/5 → 8.0 | 5/5 → 5.0 | 79.0 | Recomendable, sujeto a dependencias |
| F07 Conectividad colaborativa: presencia, reconexión y resync | BASE/ADAPTACIÓN | 5/5 → 25.0 | 4/5 → 16.0 | 3/5 → 9.0 | 3/5 → 9.0 | 3/5 → 6.0 | 4/5 → 8.0 | 5/5 → 5.0 | 78.0 | Recomendable, sujeto a dependencias |
| F08 Bloqueo fuerte por elemento con lease | BASE/ADAPTACIÓN | 2/5 → 10.0 | NE | 3/5 → 9.0 | NE | NE | NE | 3/5 → 3.0 | NO EVALUABLE | NE: sin total ni normalización |
| F09 Undo/redo colaborativo seguro | BASE/ADAPTACIÓN | 2/5 → 10.0 | NE | 2/5 → 6.0 | NE | NE | NE | 4/5 → 4.0 | NO EVALUABLE | NE: sin total ni normalización |
| F10 Lenguaje natural a operaciones estructuradas del modelador | BASE/ADAPTACIÓN | 5/5 → 25.0 | 4/5 → 16.0 | 3/5 → 9.0 | 3/5 → 9.0 | 3/5 → 6.0 | 4/5 → 8.0 | 4/5 → 4.0 | 77.0 | Recomendable, sujeto a dependencias |
| F11 Plan IA persistido, preview y confirmación autorizada | BASE/ADAPTACIÓN | 5/5 → 25.0 | 5/5 → 20.0 | 3/5 → 9.0 | 2/5 → 6.0 | 3/5 → 6.0 | 4/5 → 8.0 | 5/5 → 5.0 | 79.0 | Recomendable, sujeto a dependencias |
| F12 Dedupe, retry e identidad de solicitud/aplicación | BASE/ADAPTACIÓN | 4/5 → 20.0 | 4/5 → 16.0 | 3/5 → 9.0 | 2/5 → 6.0 | 2/5 → 4.0 | 4/5 → 8.0 | 4/5 → 4.0 | 67.0 | Conveniencia condicionada |
| F13 Contexto autoritativo del diagrama y selección | BASE/ADAPTACIÓN | 5/5 → 25.0 | 4/5 → 16.0 | 3/5 → 9.0 | 3/5 → 9.0 | 3/5 → 6.0 | 4/5 → 8.0 | 4/5 → 4.0 | 77.0 | Recomendable, sujeto a dependencias |
| F14 Voz: conservar push-to-talk y adaptar transcripción final | BASE/ADAPTACIÓN | 2/5 → 10.0 | 2/5 → 8.0 | 4/5 → 12.0 | 3/5 → 9.0 | 3/5 → 6.0 | 3/5 → 6.0 | 4/5 → 4.0 | 55.0 | Conveniencia condicionada |
| F15 Síntesis de voz opcional | BASE/ADAPTACIÓN | 1/5 → 5.0 | 3/5 → 12.0 | 4/5 → 12.0 | 3/5 → 9.0 | 3/5 → 6.0 | 3/5 → 6.0 | 4/5 → 4.0 | 54.0 | Conveniencia condicionada |
| F16 Chat grupal: preguntas/respuestas compartidas, actor y destinatario | ESTIMACIÓN: DESARROLLO NUEVO | 5/5 → 25.0 | 5/5 → 20.0 | 4/5 → 12.0 | 2/5 → 6.0 | 2/5 → 4.0 | 3/5 → 6.0 | 5/5 → 5.0 | 78.0 | Recomendable, sujeto a dependencias |
| F17 Memoria grupal/individual y continuidad de seguimientos | ESTIMACIÓN: DESARROLLO NUEVO | 5/5 → 25.0 | 5/5 → 20.0 | 4/5 → 12.0 | 1/5 → 3.0 | NE | 3/5 → 6.0 | 5/5 → 5.0 | NO EVALUABLE | NE: sin total ni normalización |
| F18 Persistencia y recuperación autorizada del historial IA | ESTIMACIÓN: DESARROLLO NUEVO | 5/5 → 25.0 | 5/5 → 20.0 | 4/5 → 12.0 | 2/5 → 6.0 | 2/5 → 4.0 | 4/5 → 8.0 | 5/5 → 5.0 | 80.0 | Recomendable, sujeto a dependencias |
| F19 Consulta conceptual de sólo lectura separada de mutación | BASE/ADAPTACIÓN | 5/5 → 25.0 | 4/5 → 16.0 | 4/5 → 12.0 | 3/5 → 9.0 | 2/5 → 4.0 | 4/5 → 8.0 | 5/5 → 5.0 | 79.0 | Recomendable, sujeto a dependencias |
| F20 IA moderadora/asesora contextual del equipo y recomendaciones | ESTIMACIÓN: DESARROLLO NUEVO | 5/5 → 25.0 | 5/5 → 20.0 | 3/5 → 9.0 | 1/5 → 3.0 | NE | 3/5 → 6.0 | 5/5 → 5.0 | NO EVALUABLE | NE: sin total ni normalización |
| F21 XMI actual de NodoBoard: conservar entrada/salida | BASE/ADAPTACIÓN | 2/5 → 10.0 | 0/5 → 0.0 | 5/5 → 15.0 | 5/5 → 15.0 | 3/5 → 6.0 | 4/5 → 8.0 | 3/5 → 3.0 | 57.0 | Conveniencia condicionada |
| F22 XMI: perfiles compatibles, límites seguros y preview versionado | BASE/ADAPTACIÓN | 2/5 → 10.0 | 4/5 → 16.0 | 2/5 → 6.0 | 2/5 → 6.0 | 2/5 → 4.0 | 4/5 → 8.0 | 4/5 → 4.0 | 54.0 | Conveniencia condicionada |
| F23 Interoperabilidad semántica/visual certificada con EA | BASE/ADAPTACIÓN | 2/5 → 10.0 | NE | NE | NE | NE | NE | 4/5 → 4.0 | NO EVALUABLE | NE: sin total ni normalización |
| F24 Exportación Spring Boot por capas y validación del artefacto | CAPACIDAD DONANTE: MIGRACIÓN CON ADAPTADOR | 1/5 → 5.0 | 5/5 → 20.0 | 2/5 → 6.0 | 1/5 → 3.0 | 3/5 → 6.0 | 3/5 → 6.0 | 4/5 → 4.0 | 50.0 | Conveniencia condicionada |
| F25 Ciclo de proyectos: archivar/restaurar/duplicar y roles extendidos | BASE/ADAPTACIÓN | 1/5 → 5.0 | 3/5 → 12.0 | 3/5 → 9.0 | 3/5 → 9.0 | 2/5 → 4.0 | 4/5 → 8.0 | 4/5 → 4.0 | 51.0 | Conveniencia condicionada |
| F26 Errores estructurados, foco y accesibilidad básica | BASE/ADAPTACIÓN | 3/5 → 15.0 | 3/5 → 12.0 | 4/5 → 12.0 | 4/5 → 12.0 | 3/5 → 6.0 | 4/5 → 8.0 | 5/5 → 5.0 | 70.0 | Recomendable, sujeto a dependencias |
| F27 Contratos, separación de responsabilidades y pruebas de frontera | BASE/ADAPTACIÓN | 4/5 → 20.0 | 3/5 → 12.0 | 4/5 → 12.0 | 3/5 → 9.0 | 3/5 → 6.0 | 5/5 → 10.0 | 3/5 → 3.0 | 72.0 | Recomendable, sujeto a dependencias |
| F28 Entrada por imagen de NodoBoard | BASE/ADAPTACIÓN | 1/5 → 5.0 | 0/5 → 0.0 | 5/5 → 15.0 | 5/5 → 15.0 | 1/5 → 2.0 | 3/5 → 6.0 | 3/5 → 3.0 | 46.0 | Baja conveniencia |
| F29 Proveedor alternativo/LLM local opcional | BASE/ADAPTACIÓN | 1/5 → 5.0 | NE | 4/5 → 12.0 | NE | NE | NE | NE | NO EVALUABLE | NE: sin total ni normalización |
| F30 Incorporación integral de Diana/React/auth/ORM legacy | BASE/ADAPTACIÓN | 2/5 → 10.0 | 1/5 → 4.0 | 0/5 → 0.0 | 0/5 → 0.0 | 1/5 → 2.0 | 1/5 → 2.0 | 1/5 → 1.0 | 19.0 | No recomendable actualmente |
| F31 Completar enlace de invitación firmado sin reemplazar invitaciones | BASE/ADAPTACIÓN | 3/5 → 15.0 | 3/5 → 12.0 | 5/5 → 15.0 | 4/5 → 12.0 | 2/5 → 4.0 | 4/5 → 8.0 | 4/5 → 4.0 | 70.0 | Recomendable, sujeto a dependencias |
| F32 Proveedor IA configurable y adaptador único en backend | BASE/ADAPTACIÓN | 5/5 → 25.0 | 2/5 → 8.0 | 4/5 → 12.0 | 4/5 → 12.0 | 3/5 → 6.0 | 4/5 → 8.0 | 3/5 → 3.0 | 74.0 | Recomendable, sujeto a dependencias |

### Justificación individual de las siete notas

#### F01 — Editor base: entidades/clases relacionales, atributos y operaciones visuales

Evidencia: E01,E02. Decisión: CONSERVAR. BASE/ADAPTACIÓN.

- R (Relevancia), 4/5; contribución 20: Base del modelador exigido, sin ampliar kinds.
- B (Beneficio incremental), 0/5; contribución 0: No hay mejora incremental por reemplazar lo ya conectado.
- C (Compatibilidad), 5/5; contribución 15: Angular/JointJS son el destino existente.
- I (Facilidad), 5/5; contribución 15: Conservar no exige traducir JSX o IDs.
- Q (Calidad/seguridad/pruebas), 2/5; contribución 4: Persistencia y tsc probados, gestos/template/E2E pendientes.
- M (Mantenibilidad), 4/5; contribución 8: Servicios DI por entidad/relación/cámara separan responsabilidades.
- U (Experiencia esperada), 4/5; contribución 4: Mantiene herramientas y navegación ya conocidas.

#### F02 — UML ampliado: kinds, métodos, realización/dependencia y ownership

Evidencia: E01,E03. Decisión: ADAPTAR. BASE/ADAPTACIÓN.

- R (Relevancia), 2/5; contribución 10: El enunciado no exige cada extensión UML/JPA.
- B (Beneficio incremental), 3/5; contribución 12: Añade métodos y semántica que NB no representa.
- C (Compatibilidad), 2/5; contribución 6: FK y enum NB no equivalen a nodes/edges Java.
- I (Facilidad), 2/5; contribución 6: Exige ampliar datos, editor y traductores.
- Q (Calidad/seguridad/pruebas), 4/5; contribución 8: Pruebas de contrato del donante cubren métodos/relaciones.
- M (Mantenibilidad), 3/5; contribución 6: Reglas separadas útiles, pero semántica adicional aumenta carga.
- U (Experiencia esperada), 3/5; contribución 3: Mejora expresividad para usuarios que necesiten esos tipos.

#### F03 — Validación determinista del dominio, tipos y multiplicidades

Evidencia: E01,E03,E07,E14. Decisión: ADAPTAR. BASE/ADAPTACIÓN.

- R (Relevancia), 4/5; contribución 20: Precondición de cambios UML autorizados y coherentes.
- B (Beneficio incremental), 4/5; contribución 16: Rechaza lotes/tipos inválidos que NB admite.
- C (Compatibilidad), 3/5; contribución 9: Django/DRF comunes, documento y enums distintos.
- I (Facilidad), 3/5; contribución 9: Funciones separadas reutilizables con DTO propio.
- Q (Calidad/seguridad/pruebas), 4/5; contribución 8: Contrato probado, sin certificar todas las entradas.
- M (Mantenibilidad), 4/5; contribución 8: Centralizar reglas evita divergencia entre importación/IA/WS.
- U (Experiencia esperada), 4/5; contribución 4: Errores antes de perder datos y multiplicidades coherentes.

#### F04 — Autenticación JWT, proyectos e invitaciones base

Evidencia: E02,E04. Decisión: CONSERVAR. BASE/ADAPTACIÓN.

- R (Relevancia), 5/5; contribución 25: Sesiones propias y pertenencia sustentan el requisito académico.
- B (Beneficio incremental), 0/5; contribución 0: Cambiar auth no aporta chat ni memoria.
- C (Compatibilidad), 5/5; contribución 15: Ya es la autenticación de Angular/Django destino.
- I (Facilidad), 5/5; contribución 15: Conservar evita dos esquemas de credenciales.
- Q (Calidad/seguridad/pruebas), 3/5; contribución 6: Pruebas acotadas y conexión real; SMTP/OAuth no probados.
- M (Mantenibilidad), 4/5; contribución 8: Módulos propios y contratos actuales aprovechables.
- U (Experiencia esperada), 4/5; contribución 4: Evita rehacer login y dashboard.

#### F05 — Autorización uniforme y revocación REST/WS

Evidencia: E04,E05,E06. Decisión: ADAPTAR. BASE/ADAPTACIÓN.

- R (Relevancia), 5/5; contribución 25: Requisito de autorización y aislamiento de colaboradores.
- B (Beneficio incremental), 5/5; contribución 20: Cerrar caminos indebidos evita escritura no autorizada.
- C (Compatibilidad), 3/5; contribución 9: Roles traducibles pero architect y miembro-ID difieren.
- I (Facilidad), 2/5; contribución 6: Debe abarcar cada entrada, no sólo plan IA.
- Q (Calidad/seguridad/pruebas), 2/5; contribución 4: Controles donantes probados con brechas conocidas S3/legacy.
- M (Mantenibilidad), 4/5; contribución 8: Política común reduce comprobaciones divergentes.
- U (Experiencia esperada), 4/5; contribución 4: Roles fiables evitan sorpresas y expulsión incompleta.

#### F06 — Revisión, reconciliación y guardado autoritativo

Evidencia: E05,E07,E08. Decisión: ADAPTAR. BASE/ADAPTACIÓN.

- R (Relevancia), 5/5; contribución 25: Cambio autorizado debe sincronizarse sin pisar estado nuevo.
- B (Beneficio incremental), 5/5; contribución 20: NB tiene pérdida secuencial reproducida y reconciliación débil.
- C (Compatibilidad), 3/5; contribución 9: Patrón Django/RxJS compatible con adaptador de agregado.
- I (Facilidad), 2/5; contribución 6: Todas las escrituras e IDs temporales deben participar.
- Q (Calidad/seguridad/pruebas), 3/5; contribución 6: Rechazo obsoleto probado; locks PG y ventana F2 limitan garantía.
- M (Mantenibilidad), 4/5; contribución 8: Un contrato autoritativo reduce fuentes divergentes.
- U (Experiencia esperada), 5/5; contribución 5: Estado visible y persistido más predecible.

#### F07 — Conectividad colaborativa: presencia, reconexión y resync

Evidencia: E06,E08,E09. Decisión: ADAPTAR. BASE/ADAPTACIÓN.

- R (Relevancia), 5/5; contribución 25: Sesiones remotas y tablero compartido son obligatorios.
- B (Beneficio incremental), 4/5; contribución 16: Añade recuperación y presencia más consistente que diccionario local.
- C (Compatibilidad), 3/5; contribución 9: Channels compartido, JWT/scope de proyecto diferentes.
- I (Facilidad), 3/5; contribución 9: Hook traducible a RxJS; backend de presencia requiere adaptación.
- Q (Calidad/seguridad/pruebas), 3/5; contribución 6: Utilidades probadas, sin Redis/multiworker real.
- M (Mantenibilidad), 4/5; contribución 8: Lifecycle explícito de canal/TTL facilita soporte.
- U (Experiencia esperada), 5/5; contribución 5: Mejor recuperación y claridad de conexión.

#### F08 — Bloqueo fuerte por elemento con lease

Evidencia: E05,E09. Decisión: INVESTIGAR. BASE/ADAPTACIÓN.

- R (Relevancia), 2/5; contribución 10: No obligatorio si revisión resuelve conflictos de forma explícita.
- B (Beneficio incremental), NE: No se midió necesidad ni ventaja frente a revisión.
- C (Compatibilidad), 3/5; contribución 9: Channels admite diseñarlo en arquitectura destino.
- I (Facilidad), NE: Faltan contrato de dueño/timeout y conflictos.
- Q (Calidad/seguridad/pruebas), NE: No hay pruebas de lease fuerte localizado.
- M (Mantenibilidad), NE: Sin diseño no puede estimarse mantenimiento.
- U (Experiencia esperada), 3/5; contribución 3: Evitar edición simultánea podría ayudar, sin UX probada.

#### F09 — Undo/redo colaborativo seguro

Evidencia: E10. Decisión: INVESTIGAR. BASE/ADAPTACIÓN.

- R (Relevancia), 2/5; contribución 10: Comodidad adicional, no requisito textual.
- B (Beneficio incremental), NE: Ventaja multiusuario no demostrada por undo local.
- C (Compatibilidad), 2/5; contribución 6: Snapshots React no son operaciones inversas de ORM.
- I (Facilidad), NE: Falta alcance local/remoto y política de historial.
- Q (Calidad/seguridad/pruebas), NE: Ningún test acredita inversión colaborativa.
- M (Mantenibilidad), NE: Mantenimiento depende del modelo de operación aún no diseñado.
- U (Experiencia esperada), 4/5; contribución 4: Revertir errores ayudaría si no revierte cambios ajenos.

#### F10 — Lenguaje natural a operaciones estructuradas del modelador

Evidencia: E03,E07,E11. Decisión: ADAPTAR. BASE/ADAPTACIÓN.

- R (Relevancia), 5/5; contribución 25: Interpretar solicitudes de modificación es requisito explícito.
- B (Beneficio incremental), 4/5; contribución 16: Contrato tipado mejora deltas aceptados sin esquema.
- C (Compatibilidad), 3/5; contribución 9: Reutilizable en Django, necesita operaciones ORM NB.
- I (Facilidad), 3/5; contribución 9: Lógica separada pero IDs/tipos/clase asociativa cambian.
- Q (Calidad/seguridad/pruebas), 3/5; contribución 6: Ejecutor probado; comprensión abierta del modelo no probada.
- M (Mantenibilidad), 4/5; contribución 8: Allowlist y operaciones acotadas facilitan extensión.
- U (Experiencia esperada), 4/5; contribución 4: Errores y aclaraciones reducen modificaciones imprevistas.

#### F11 — Plan IA persistido, preview y confirmación autorizada

Evidencia: E07,E11,E12. Decisión: ADAPTAR. BASE/ADAPTACIÓN.

- R (Relevancia), 5/5; contribución 25: Autorización previa de modificaciones exigida.
- B (Beneficio incremental), 5/5; contribución 20: Introduce control que el chat NB no tiene.
- C (Compatibilidad), 3/5; contribución 9: Concepto Django compatible, FKs y revisión no copiables.
- I (Facilidad), 2/5; contribución 6: Nuevo contrato backend/UI y persistencia propia.
- Q (Calidad/seguridad/pruebas), 3/5; contribución 6: Tests de permisos/TTL/rollback, con carrera de base detectada.
- M (Mantenibilidad), 4/5; contribución 8: Separa intención, autorización y aplicación.
- U (Experiencia esperada), 5/5; contribución 5: Usuario ve y decide los cambios antes de persistir.

#### F12 — Dedupe, retry e identidad de solicitud/aplicación

Evidencia: E07,E12. Decisión: ADAPTAR. BASE/ADAPTACIÓN.

- R (Relevancia), 4/5; contribución 20: Apoya integridad de instrucciones y sincronización exigidas.
- B (Beneficio incremental), 4/5; contribución 16: Reduce repetición de creaciones ante respuesta perdida.
- C (Compatibilidad), 3/5; contribución 9: Identidad puede añadirse al contrato NB.
- I (Facilidad), 2/5; contribución 6: Requiere distinguir solicitud, plan, resultado y evento.
- Q (Calidad/seguridad/pruebas), 2/5; contribución 4: Defectos H-D03 e índices sin unicidad impiden garantía alta.
- M (Mantenibilidad), 4/5; contribución 8: Semántica explícita de retry evita excepciones dispersas.
- U (Experiencia esperada), 4/5; contribución 4: Reintentos coherentes sin operaciones repetidas.

#### F13 — Contexto autoritativo del diagrama y selección

Evidencia: E07,E11. Decisión: FUSIONAR. BASE/ADAPTACIÓN.

- R (Relevancia), 5/5; contribución 25: Asesoría y cambios requieren comprender el tablero compartido.
- B (Beneficio incremental), 4/5; contribución 16: Procedencia servidor y multiplicidad mejoran contexto NB.
- C (Compatibilidad), 3/5; contribución 9: Resumen transformable a ORM, no copiar shape React.
- I (Facilidad), 3/5; contribución 9: Servicio de lectura autorizado y DTO son alcance acotado.
- Q (Calidad/seguridad/pruebas), 3/5; contribución 6: Sonda prueba omisión NB y tests cubren resumen/contratos DC.
- M (Mantenibilidad), 4/5; contribución 8: Resumen mínimo aislado reduce acoplamiento visual.
- U (Experiencia esperada), 4/5; contribución 4: Menos ambigüedad sobre elementos y selección.

#### F14 — Voz: conservar push-to-talk y adaptar transcripción final

Evidencia: E13. Decisión: ADAPTAR. BASE/ADAPTACIÓN.

- R (Relevancia), 2/5; contribución 10: No requisito obligatorio del enunciado.
- B (Beneficio incremental), 2/5; contribución 8: Mejora envíos accidentales, no agrega micrófono básico ausente.
- C (Compatibilidad), 4/5; contribución 12: API navegador ya usada en Angular.
- I (Facilidad), 3/5; contribución 9: Estados/finales portables; comportamiento wake requiere revisión.
- Q (Calidad/seguridad/pruebas), 3/5; contribución 6: Funciones puras probadas, audio real pendiente.
- M (Mantenibilidad), 3/5; contribución 6: Servicio Angular existente evita duplicar voz.
- U (Experiencia esperada), 4/5; contribución 4: Menos comandos accidentales y fallback escrito.

#### F15 — Síntesis de voz opcional

Evidencia: E13. Decisión: ADAPTAR. BASE/ADAPTACIÓN.

- R (Relevancia), 1/5; contribución 5: Complementaria, no obligatoria para examen.
- B (Beneficio incremental), 3/5; contribución 12: Añade respuesta hablada no localizada en NB.
- C (Compatibilidad), 4/5; contribución 12: Web Speech se puede encapsular en servicio Angular.
- I (Facilidad), 3/5; contribución 9: Utilidades portables; requiere preferencia y coordinación de escucha.
- Q (Calidad/seguridad/pruebas), 3/5; contribución 6: Pruebas de texto/voz seleccionada, no altavoz.
- M (Mantenibilidad), 3/5; contribución 6: Abstracción pequeña aunque navegador varía.
- U (Experiencia esperada), 4/5; contribución 4: Opción útil de interacción/accesibilidad sin sustituir texto.

#### F16 — Chat grupal: preguntas/respuestas compartidas, actor y destinatario

Evidencia: E04,E06,E15,R2-R7. Decisión: DESARROLLO NUEVO. ESTIMACIÓN: DESARROLLO NUEVO.

- R (Relevancia), 5/5; contribución 25: Preguntas/respuestas visibles y atribuidas son requisitos explícitos.
- B (Beneficio incremental), 5/5; contribución 20: Cubre brecha completa en ambos proyectos.
- C (Compatibilidad), 4/5; contribución 12: User/JWT/proyecto/Channels y Angular ya ofrecen base.
- I (Facilidad), 2/5; contribución 6: Necesita contrato de mensajes, servidor, eventos y UI compartida.
- Q (Calidad/seguridad/pruebas), 2/5; contribución 4: Nota sólo de base reutilizable auth/Channels; mensajes nuevos sin tests.
- M (Mantenibilidad), 3/5; contribución 6: Posible módulo cohesivo, diseño aún no existe.
- U (Experiencia esperada), 5/5; contribución 5: Todos pueden participar y saber a quién responde la IA.

#### F17 — Memoria grupal/individual y continuidad de seguimientos

Evidencia: E15,E16,R8-R11. Decisión: DESARROLLO NUEVO. ESTIMACIÓN: DESARROLLO NUEVO.

- R (Relevancia), 5/5; contribución 25: Contextos de equipo y participante/seguimientos explícitos.
- B (Beneficio incremental), 5/5; contribución 20: Falta capacidad en ambos, no sólo presentación.
- C (Compatibilidad), 4/5; contribución 12: Viable sobre Django/User/proyecto e historial futuro.
- I (Facilidad), 1/5; contribución 3: Política de contexto, límites y resolución por actor sin diseñar.
- Q (Calidad/seguridad/pruebas), NE: NO EVALUABLE: sin recuperador/context builder ni pruebas equivalentes.
- M (Mantenibilidad), 3/5; contribución 6: Separación por actor viable, estrategia de memoria incierta.
- U (Experiencia esperada), 5/5; contribución 5: Continuidad de conversación evitaría repetir acuerdos.

#### F18 — Persistencia y recuperación autorizada del historial IA

Evidencia: E04,E15,R18. Decisión: DESARROLLO NUEVO. ESTIMACIÓN: DESARROLLO NUEVO.

- R (Relevancia), 5/5; contribución 25: Conservar/recuperar historial es requisito explícito.
- B (Beneficio incremental), 5/5; contribución 20: Evita pérdida de diálogo al recargar, inexistente en ambos.
- C (Compatibilidad), 4/5; contribución 12: ORM/DRF/Angular y pertenencia permiten desarrollarlo.
- I (Facilidad), 2/5; contribución 6: Necesita modelos/consulta/paginación/orden y UI, no copia de PlanIA.
- Q (Calidad/seguridad/pruebas), 2/5; contribución 4: Base ORM/auth probada parcialmente; no se atribuyen tests de historial nuevo.
- M (Mantenibilidad), 4/5; contribución 8: Modelo de mensajes separado evita confundir planes y conversación.
- U (Experiencia esperada), 5/5; contribución 5: Recuperar conversaciones aporta continuidad tangible.

#### F19 — Consulta conceptual de sólo lectura separada de mutación

Evidencia: E07,E11,E16,R12. Decisión: FUSIONAR. BASE/ADAPTACIÓN.

- R (Relevancia), 5/5; contribución 25: Dudas conceptuales y asesoría son requisito.
- B (Beneficio incremental), 4/5; contribución 16: Aislar respuesta evita que consulta ejecute cambios.
- C (Compatibilidad), 4/5; contribución 12: Chat Angular y reglas de respuesta compatibles.
- I (Facilidad), 3/5; contribución 9: Requiere contrato answer/proposal y barrera de no escritura.
- Q (Calidad/seguridad/pruebas), 2/5; contribución 4: Sólo transporte fake NB, sin exactitud conceptual real.
- M (Mantenibilidad), 4/5; contribución 8: Separar consulta de comandos reduce estados ambiguos.
- U (Experiencia esperada), 5/5; contribución 5: Permite preguntar sin riesgo de modificar el tablero.

#### F20 — IA moderadora/asesora contextual del equipo y recomendaciones

Evidencia: E15,E16,R13-R14. Decisión: DESARROLLO NUEVO. ESTIMACIÓN: DESARROLLO NUEVO.

- R (Relevancia), 5/5; contribución 25: Rol moderador/asesor y recomendaciones son enunciado explícito.
- B (Beneficio incremental), 5/5; contribución 20: Añade comportamiento grupal que ningún plan prueba.
- C (Compatibilidad), 3/5; contribución 9: Puede usar chat/contexto existentes, comportamiento aún no diseñado.
- I (Facilidad), 1/5; contribución 3: Requiere política, contexto y evaluación de diálogos nuevos.
- Q (Calidad/seguridad/pruebas), NE: NO EVALUABLE: calidad/seguridad de moderación sin corpus ni pruebas.
- M (Mantenibilidad), 3/5; contribución 6: Aislar política es viable, costes de evaluación desconocidos.
- U (Experiencia esperada), 5/5; contribución 5: Potencial alto para acuerdos y asesoría, no resultado comprobado.

#### F21 — XMI actual de NodoBoard: conservar entrada/salida

Evidencia: E14,E17. Decisión: CONSERVAR. BASE/ADAPTACIÓN.

- R (Relevancia), 2/5; contribución 10: Interoperabilidad útil, no requisito textual del chat.
- B (Beneficio incremental), 0/5; contribución 0: Reemplazar lo que procesa la fixture no aporta beneficio demostrado.
- C (Compatibilidad), 5/5; contribución 15: Ya conecta ORM y GeneradorService Angular.
- I (Facilidad), 5/5; contribución 15: Mantener contrato archivo_xml evita conversión inmediata.
- Q (Calidad/seguridad/pruebas), 3/5; contribución 6: Roundtrip de conteos real, semántica/EA y bigint limitados.
- M (Mantenibilidad), 4/5; contribución 8: Servicios import/export separados conservables.
- U (Experiencia esperada), 3/5; contribución 3: Mantiene intercambio conocido sin regresión deliberada.

#### F22 — XMI: perfiles compatibles, límites seguros y preview versionado

Evidencia: E14,E17,E18. Decisión: FUSIONAR. BASE/ADAPTACIÓN.

- R (Relevancia), 2/5; contribución 10: Ampliación útil, no requisito académico textual.
- B (Beneficio incremental), 4/5; contribución 16: Previene importación opaca y añade preview/selección.
- C (Compatibilidad), 2/5; contribución 6: Namespace e IDs/modelo NB incompatibles con parser directo.
- I (Facilidad), 2/5; contribución 6: Debe integrar parseo, DTO ORM, revisión y UI Angular.
- Q (Calidad/seguridad/pruebas), 2/5; contribución 4: Pruebas internas y límites, pero caso real9→0 y preview obsoleto.
- M (Mantenibilidad), 4/5; contribución 8: Reglas de perfil aisladas mejoran mantenimiento.
- U (Experiencia esperada), 4/5; contribución 4: Usuario ve qué se importará y qué se pierde.

#### F23 — Interoperabilidad semántica/visual certificada con EA

Evidencia: E14,E17. Decisión: INVESTIGAR. BASE/ADAPTACIÓN.

- R (Relevancia), 2/5; contribución 10: No exigencia textual de herramienta externa en segundo parcial.
- B (Beneficio incremental), NE: Sin versión/perfil EA objetivo no puede medir mejora.
- C (Compatibilidad), NE: Compatibilidad concreta fuera de perfiles probados no acreditada.
- I (Facilidad), NE: Sin herramienta/alcance no hay estimación razonable.
- Q (Calidad/seguridad/pruebas), NE: No se probó EA real.
- M (Mantenibilidad), NE: Soporte de dialectos depende del perfil acordado.
- U (Experiencia esperada), 4/5; contribución 4: Intercambio fiel ayudaría a usuarios de EA.

#### F24 — Exportación Spring Boot por capas y validación del artefacto

Evidencia: E03,E19. Decisión: MIGRAR. CAPACIDAD DONANTE: MIGRACIÓN CON ADAPTADOR.

- R (Relevancia), 1/5; contribución 5: No requisito del chat académico.
- B (Beneficio incremental), 5/5; contribución 20: Añade capacidad ausente: código y capas CRUD.
- C (Compatibilidad), 2/5; contribución 6: Falta kind/JPA/whole/tipos completos en ORM NB.
- I (Facilidad), 1/5; contribución 3: Adaptador semántico, endpoint/UI y toolchain son amplios.
- Q (Calidad/seguridad/pruebas), 3/5; contribución 6: ZIP/texto probados; javac/Maven/ejecución pendientes.
- M (Mantenibilidad), 3/5; contribución 6: Generador separado útil, pero plantillas/versiones exigen cuidado.
- U (Experiencia esperada), 4/5; contribución 4: Descarga útil si modelo es generable y validado.

#### F25 — Ciclo de proyectos: archivar/restaurar/duplicar y roles extendidos

Evidencia: E02,E04,E20. Decisión: ADAPTAR. BASE/ADAPTACIÓN.

- R (Relevancia), 1/5; contribución 5: No requisito explícito archivar/duplicar.
- B (Beneficio incremental), 3/5; contribución 12: Aporta gestión adicional sin reemplazar dashboard.
- C (Compatibilidad), 3/5; contribución 9: Django común; nombres/diagrama/membresías distintos.
- I (Facilidad), 3/5; contribución 9: Servicios identificados, cambios de modelo/API/UI moderados.
- Q (Calidad/seguridad/pruebas), 2/5; contribución 4: Suite proyectos15 errores SQLite/1 fallo no certifica ciclo entero.
- M (Mantenibilidad), 4/5; contribución 8: Centralizar ciclo y roles facilita evolución.
- U (Experiencia esperada), 4/5; contribución 4: Administrar proyectos resulta más claro.

#### F26 — Errores estructurados, foco y accesibilidad básica

Evidencia: E08,E16,E21. Decisión: FUSIONAR. BASE/ADAPTACIÓN.

- R (Relevancia), 3/5; contribución 15: Apoya uso comprensible y recuperación, no todos sus controles son requisitos.
- B (Beneficio incremental), 3/5; contribución 12: Diagnóstico/foco mejoran errores y conflictos de NB.
- C (Compatibilidad), 4/5; contribución 12: Patrones trasladables a componentes Angular.
- I (Facilidad), 4/5; contribución 12: DTO y UX aprovechables sin cambiar motor/framework.
- Q (Calidad/seguridad/pruebas), 3/5; contribución 6: Pruebas de errores y fuente UI, sin lector/teclado manual.
- M (Mantenibilidad), 4/5; contribución 8: Contrato común reduce ramas de errores.
- U (Experiencia esperada), 5/5; contribución 5: Más claridad de carga, fallo y confirmación.

#### F27 — Contratos, separación de responsabilidades y pruebas de frontera

Evidencia: E01,E08,E11,E22. Decisión: ADAPTAR. BASE/ADAPTACIÓN.

- R (Relevancia), 4/5; contribución 20: Soporta verificar requisitos y evitar regresiones académicas.
- B (Beneficio incremental), 3/5; contribución 12: Hace comprobables límites hoy no cubiertos de NB.
- C (Compatibilidad), 4/5; contribución 12: Django/Angular admiten misma separación sin nuevos frameworks.
- I (Facilidad), 3/5; contribución 9: Reescribir fixtures y revisar versiones requiere alcance transversal.
- Q (Calidad/seguridad/pruebas), 3/5; contribución 6: Pruebas reales pero suites/env parciales y fallos conocidos.
- M (Mantenibilidad), 5/5; contribución 10: Módulos por responsabilidad y contratos únicos reducen deuda.
- U (Experiencia esperada), 3/5; contribución 3: Beneficio indirecto por menos fallos y errores consistentes.

#### F28 — Entrada por imagen de NodoBoard

Evidencia: E07,E23. Decisión: CONSERVAR. BASE/ADAPTACIÓN.

- R (Relevancia), 1/5; contribución 5: Complementaria al requisito de lenguaje natural.
- B (Beneficio incremental), 0/5; contribución 0: No hay beneficio de sustitución donante sin equivalente.
- C (Compatibilidad), 5/5; contribución 15: Integración Angular/backend actual.
- I (Facilidad), 5/5; contribución 15: Conservar superficie no exige copia ni dependencia nueva.
- Q (Calidad/seguridad/pruebas), 1/5; contribución 2: Sin salida real de imagen ni suite propia acreditada.
- M (Mantenibilidad), 3/5; contribución 6: Separar validación futura evita duplicar rutas de ejecución.
- U (Experiencia esperada), 3/5; contribución 3: Mantiene entrada visual disponible por código.

#### F29 — Proveedor alternativo/LLM local opcional

Evidencia: E07,E11,E24,R20. Decisión: INVESTIGAR. BASE/ADAPTACIÓN.

- R (Relevancia), 1/5; contribución 5: Modelo local explícitamente opcional.
- B (Beneficio incremental), NE: Sin modelo/hardware/corpus no se conoce beneficio.
- C (Compatibilidad), 4/5; contribución 12: Interfaz de proveedor puede encajar en Django.
- I (Facilidad), NE: Falta motor, runtime, recursos y operación.
- Q (Calidad/seguridad/pruebas), NE: Sin modelo integrado ni pruebas equivalentes.
- M (Mantenibilidad), NE: Desconocido soporte/operación del motor elegido.
- U (Experiencia esperada), NE: Latencia/calidad/privacidad no medidas.

#### F30 — Incorporación integral de Diana/React/auth/ORM legacy

Evidencia: E02,E06,E15,E25. Decisión: DESCARTAR. BASE/ADAPTACIÓN.

- R (Relevancia), 2/5; contribución 10: Sólo cubre fracciones; no resuelve memoria/chat obligatorio.
- B (Beneficio incremental), 1/5; contribución 4: Duplica editor/chat/auth con poco aporte incremental.
- C (Compatibilidad), 0/5; contribución 0: Reemplazar Angular/introducir React contradice restricción explícita.
- I (Facilidad), 0/5; contribución 0: Traslado literal no es viable dentro de arquitectura autorizada.
- Q (Calidad/seguridad/pruebas), 1/5; contribución 2: Brechas legacy/revisión/revocación y archivos vacíos.
- M (Mantenibilidad), 1/5; contribución 2: Dos autoridades y frameworks aumentan mantenimiento.
- U (Experiencia esperada), 1/5; contribución 1: Fragmenta conversación y navegación.

#### F31 — Completar enlace de invitación firmado sin reemplazar invitaciones

Evidencia: E02,E26. Decisión: ADAPTAR. BASE/ADAPTACIÓN.

- R (Relevancia), 3/5; contribución 15: Facilita acceso al equipo; aceptación interna ya existe.
- B (Beneficio incremental), 3/5; contribución 12: Conecta un recorrido de invitación hoy incompleto.
- C (Compatibilidad), 5/5; contribución 15: Ruta/vista y servicio propios encajan en Angular.
- I (Facilidad), 4/5; contribución 12: Adaptación de contrato/UX pequeña frente a migrar invitaciones.
- Q (Calidad/seguridad/pruebas), 2/5; contribución 4: Fallo de conexión estático suficiente; correo/flujo completo no probado.
- M (Mantenibilidad), 4/5; contribución 8: Reusar firma/aceptación reduce duplicación.
- U (Experiencia esperada), 4/5; contribución 4: Destinatario del correo llega a una acción válida.

#### F32 — Proveedor IA configurable y adaptador único en backend

Evidencia: E07,E11,E24,R19. Decisión: FUSIONAR. BASE/ADAPTACIÓN.

- R (Relevancia), 5/5; contribución 25: Configurar proveedor es requisito explícito R19.
- B (Beneficio incremental), 2/5; contribución 8: Ya hay parámetros; mejora principal separación/testabilidad.
- C (Compatibilidad), 4/5; contribución 12: Django y proveedor actual conservables.
- I (Facilidad), 4/5; contribución 12: Factory adaptable sin auth/React ni cambio de proveedor.
- Q (Calidad/seguridad/pruebas), 3/5; contribución 6: Mocks/ramas config probadas; SDK y servicio real limitados.
- M (Mantenibilidad), 4/5; contribución 8: Un adaptador único reduce duplicación y permite fake.
- U (Experiencia esperada), 3/5; contribución 3: Errores/modelo configurables benefician indirectamente al usuario.

## E. Evaluación de prioridades

La prioridad sigue obligación/bloqueo, no la ordenación de D. Las prioridades de conservación indican preservar y verificar un requisito existente. Las NE mantienen prioridad cuando el requisito o la naturaleza opcional están claros; no se fabricó una puntuación para asignarla.

| ID | Prioridad | Justificación |
|---|---|---|
| F01 | P0 | Preservar requisito base; no es orden de reimplementarlo |
| F02 | P2 | Extensión útil, no brecha obligatoria del chat |
| F03 | P0 | Bloqueo de integridad para las mutaciones requeridas |
| F04 | P0 | Preservar acceso e identidad de cada integrante |
| F05 | P0 | Seguridad e integridad; no implica vulnerabilidad de red completa demostrada |
| F06 | P0 | Bloqueo de integridad del tablero compartido |
| F07 | P0 | Se prioriza continuidad del tablero; presencia visual no es requisito académico independiente |
| F08 | P2 | Opcional y condicionado a política de colaboración |
| F09 | P2 | Útil, sin necesidad de examen acreditada |
| F10 | P0 | Capacidad académica existente parcial a completar |
| F11 | P0 | Confirmación y seguridad del requisito de cambios |
| F12 | P0 | Integridad de acciones autorizadas; no exactly-once demostrado |
| F13 | P0 | Precondición para asesoría/modificaciones sobre datos vigentes |
| F14 | P2 | Mejora opcional sobre entrada existente |
| F15 | P2 | Opcional; no precede requisitos conversacionales |
| F16 | P0 | Requisitos obligatorios R2-R7, incluida consulta por lectores autorizados |
| F17 | P0 | Requisitos R8-R11 siguen siendo P0 aunque no haya puntuación total |
| F18 | P0 | Requisito R18; ausencia no reduce prioridad |
| F19 | P0 | R12 y separación de permiso preguntar/editar |
| F20 | P0 | R13-R14 y propósito moderador, sin degradar por falta de donante |
| F21 | P2 | Capacidad existente opcional a conservar, no desarrollar otra |
| F22 | P1 | Mejora importante; compatibilidad y rechazo de vacío son veto antes de incorporar, no obligación de migrar ahora |
| F23 | P2 | Útil fuera de requisitos conversacionales; falta alcance de herramienta |
| F24 | P2 | Capacidad adicional, no debe desplazar brechas obligatorias |
| F25 | P2 | Opcional sobre proyectos ya existentes |
| F26 | P1 | Mejora importante de uso y recuperación de conflictos |
| F27 | P1 | Mejora transversal importante; gates de seguridad siguen P0 en sus filas |
| F28 | P2 | No descartar capacidad propia; verificación real pendiente |
| F29 | P3 | Opcional; no requisito ni sustitución obligatoria de Gemini |
| F30 | P3 | Redundante e incompatible con restricción arquitectónica |
| F31 | P1 | Mejora importante; no bloquea toda colaboración porque hay aceptación interna |
| F32 | P0 | Conservar configuración obligatoria y verificar integración, no exigir multiempresa |

F05/F06 son P0 por defectos reproducidos de seguridad/integridad, aunque ninguna alternativa aislada alcance 85. F16/F17/F18/F20 son P0 por brechas obligatorias, aunque dos totales sean NE. F24 Spring es P2 pese a aportar una capacidad grande ausente; no pertenece al enunciado del chat. F30 es P3 como alternativa redundante, aun cuando algunas piezas de Diana atiendan problemas P0.

En XMI hay dos niveles distintos: F22 es mejora P1 opcional respecto al examen; **el gate de no integrar un parser que convierte un documento con clases en vacío es indispensable si se decide incorporar esa solución**. Esto no vuelve obligatorio migrar XMI para cumplir el examen ni acredita una pérdida existente en NB. Las comprobaciones indispensables de F05/F06 no pueden quedar compensadas por mejores controles visuales de F26.

## F. Evaluación de esfuerzo

No se estiman horas ni se construye un calendario. Los números consideran backend/frontend, datos/migraciones futuras, traducción Angular/React, contratos, dependencias y pruebas que hoy faltan. Esfuerzo de conservar no equivale a implementar de nuevo. En NE no se inventa un valor medio.

| ID | Esfuerzo /5 | Superficie y motivo | Dependencias/gates propuestos |
|---|---|---|---|
| F01 | 1 | Verificación/regresión focalizada de modelos y servicios ya existentes | F04 |
| F02 | 4 | Modelos/serializers, interfaces, parser y modales; futuras migraciones sólo si se autorizan | F03,F06 |
| F03 | 4 | Validadores NB, modelos/serializers y pruebas por escritor; frontend sólo refleja reglas | F01,F04 |
| F04 | 1 | No nueva autenticación; comprobación de regresión y contratos existentes | Base existente; no requiere solución donante |
| F05 | 4 | Views/serializers/consumers y servicios de miembros; matriz por rol/acción | F04 |
| F06 | 5 | Modelo/revisión futura, servicio común, REST/WS/import/IA y Angular autosave; migración aún no creada | F03,F05 |
| F07 | 4 | Consumer/realtime/socket Angular, expiración y pruebas múltiples pestañas/workers | F05,F06 |
| F08 | NE | NO EVALUABLE: alcance de lease y recuperación no definidos | F05,F06 |
| F09 | NE | NO EVALUABLE: no se definieron inversas/versiones | F06 |
| F10 | 4 | Asistente/modelado y servicios Angular; reescribir fixtures/operaciones sin React Flow | F03,F05,F06,F13,F32 |
| F11 | 5 | Modelo/servicios futuros y Angular estados preview/confirmar/cancelar; no migraciones ahora | F03,F05,F06,F10 |
| F12 | 4 | API/planes, cliente IA/socket y futuros constraints; pruebas de repetición/orden | F06,F11 |
| F13 | 3 | Lectura ORM, vista asistente e interfaz de selección; no memoria conversacional | F03,F05,F06 |
| F14 | 3 | AsistenteIaService/chat y estados de plan; pruebas navegador bajo autorización | F11 |
| F15 | 2 | Servicio de voz y toggle en chat, sin JSX ni nuevo motor | F14 |
| F16 | 5 | Nuevos contratos/servicios/mensajes, frontend y eventos; identidad siempre del servidor | F04,F05,F06,F07 |
| F17 | 5 | Memoria/retrieval/política de contexto y evaluación nuevas, además del historial | F05,F16,F18,F13 |
| F18 | 4 | Modelos y futuras migraciones propias, consultas por proyecto/actor, paginación y recarga Angular | F04,F05,F16 |
| F19 | 3 | Handler/DTO IA y chat, pruebas deterministas de cero escritura | F05,F13,F16,F32 |
| F20 | 5 | Políticas de diálogo/recomendaciones, contexto y pruebas de asesoría; no basta un prompt copiado | F17,F19,F13,F32 |
| F21 | 1 | Regresión focalizada del contrato/fixture, sin sustitución | F03 |
| F22 | 4 | Servicios XML/serializers/views, GeneradorService y preview; pruebas cruzadas de perfiles | F03,F05,F06,F21 |
| F23 | NE | NO EVALUABLE: versión EA, perfil y semántica requerida no definidos | F22 |
| F24 | 5 | DTO canónico a normalize_diagram, generador/endpoint Angular y futura compilación aislada; no backend Spring sustituto | F02,F03,F05,F06 |
| F25 | 4 | Views/servicios/roles/datos de archivo y dashboard Angular; no RunPython del donante | F04,F05,F06 |
| F26 | 3 | Respuestas backend, interfaces, toast/chat y cámara/modal Angular | F05,F06 |
| F27 | 4 | Contratos/fixtures/backend y Angular tests en versión declarada, dependencias verificadas sin fusionar manifests | F03,F05,F06 |
| F28 | 1 | Conservar endpoint/UI e incluir salida en validación común futura | F03,F05,F06 |
| F29 | NE | NO EVALUABLE: motor/modelo/hardware/licencia/operación no definidos | F32 |
| F30 | 5 | Reescritura y doble persistencia de amplia superficie, no acción recomendada | Base existente; no requiere solución donante |
| F31 | 2 | app.routes, página/servicio futuro para token y prueba de enlace; backend vigente como base | F04,F05 |
| F32 | 3 | Settings/interfaz proveedor, vista y pruebas de configuración; no cambio de claves/dependencias ahora | F04 |

Los mayores alcances se explican por cambios de autoridad/persistencia (F06/F11), conversación nueva (F16/F17/F20) o traducción semántica y generación (F24). Un componente React breve no reduce esos alcances: deben reexpresarse comportamientos en Angular. El coste real depende del diseño que se autorice después. F18 necesita esquema nuevo propio; no se debe reutilizar PlanIA como conversación sólo para ahorrar una tabla.

## G. Evaluación de riesgos

El riesgo es una estimación técnica con consecuencias identificadas; no prueba de incidentes reales ni una medida probabilística. Se mantiene separado de Q y del puntaje total. Q refleja evidencia existente; riesgo refleja qué puede salir mal al conservar/integrar el alcance propuesto. No se reducen riesgos por una puntuación favorable.

| ID | Riesgo /5 | Consecuencia y fundamento | Evidencia |
|---|---|---|---|
| F01 | 3 | Guardar/roles presentan fallos atendidos por F05/F06; conservar UI no los valida | E01,E02 |
| F02 | 4 | Pérdida de semántica whole/JPA y conversión de IDs | E01,E03 |
| F03 | 4 | Coerciones incorrectas, pérdida de tipo y validación desigual entre entradas | E01,E03,E07,E14 |
| F04 | 3 | Configuración/refresh y permisos no completamente certificados; F05 separado | E02,E04 |
| F05 | 5 | Escritura fuera de rol y posible entrega posterior al retiro; pruebas E2E pendientes | E04,E05,E06 |
| F06 | 5 | Sobrescritura, borrado y documento visual/ORM divergente | E05,E07,E08 |
| F07 | 4 | Eventos perdidos, canal viejo, presencia fantasma y revocación S3 | E06,E08,E09 |
| F08 | 4 | Bloqueo abandonado o falso sentido de exclusión | E05,E09 |
| F09 | 4 | Restaurar snapshot puede borrar trabajo remoto | E10 |
| F10 | 4 | Salida de proveedor no confiable y semántica traducida incorrectamente | E03,E07,E11 |
| F11 | 5 | Plan obsoleto, rol revocado, aplicar contexto viejo o publicar antes de persistir | E07,E11,E12 |
| F12 | 4 | Duplicación de datos/eventos o falso409 tras aplicación exitosa | E07,E12 |
| F13 | 4 | Interpretar contra contexto viejo o no autorizado; no confundir con memoria de diálogo | E07,E11 |
| F14 | 3 | Permisos de audio, parciales y confirmación errónea; no offline garantizado | E13 |
| F15 | 3 | Feedback acústico, disponibilidad y lectura de mensajes sin preferencia | E13 |
| F16 | 5 | Suplantación de actor, mensajes de otro proyecto o envío sólo local | E04,E06,E15,R2-R7 |
| F17 | 5 | Mezclar participantes, contexto obsoleto, exposición fuera del proyecto y calidad de anáforas | E15,E16,R8-R11 |
| F18 | 4 | Lectura indebida, orden ambiguo o duplicados; diseño de retención pendiente | E04,E15,R18 |
| F19 | 4 | Confundir mensaje con plan y atribuir calidad no medida | E07,E11,E16,R12 |
| F20 | 4 | Consejos erróneos, atribución incorrecta o recomendaciones aplicadas sin confirmar | E15,E16,R13-R14 |
| F21 | 3 | Preservación semántica/layout no completa; errores de tipo atendidos en validación | E14,E17 |
| F22 | 5 | Importar vacío silenciosamente o reemplazar estado posterior al preview | E14,E17,E18 |
| F23 | 4 | Pérdida de semántica/layout encubierta por conteos iguales | E14,E17 |
| F24 | 4 | JPA incorrecto, artefacto no compilable o nombres/rutas inválidas | E03,E19 |
| F25 | 3 | Copiar miembros al duplicar o restaurar sin privacidad/unicidad | E02,E04,E20 |
| F26 | 3 | Exponer raw/detalles, enfocar ID obsoleto o declarar accesibilidad sin prueba | E08,E16,E21 |
| F27 | 4 | Copiar pruebas de JSON donante como si probaran ORM destino o asumir suite verde | E01,E08,E11,E22 |
| F28 | 3 | Resultado multimodal no validado o creación completa que pisa estado | E07,E23 |
| F29 | 4 | Nueva dependencia operativa y calidad incierta; no garantía local por parser | E07,E11,E24,R20 |
| F30 | 5 | Seguridad legacy, dos autenticaciones y pérdida de dominio/estado | E02,E06,E15,E25 |
| F31 | 3 | Token expirado/reutilizado, acceso erróneo o confusión con activar cuenta | E02,E26 |
| F32 | 3 | Mezclar dos APIs SDK o usar fallback no disponible | E07,E11,E24,R19 |

### Gates antes de cualquier incorporación relacionada

| Gate | Evidencia que lo justifica | Alcances condicionados | Criterio de validación futuro, no ejecutado ahora |
|---|---|---|---|
| Permisos uniformes y revocación efectiva | H-N01/H-N02, S3, H-D04 | F05/F07/F10–F20/F22/F24 | Rol/membresía vigentes en cada escritura y en acceso a historial; cortar entrega del retirado, no sólo avisar cliente |
| Una autoridad y revisión esperada | H-N03, R3, H2-D01, WS raw vs validado | F06/F10–F13/F17/F22 | Rechazar base obsoleta en todo escritor y mantener misma base del contexto de interpretación; persistir datos normalizados |
| Rechazo de pérdida XMI inesperada | X3; perfiles/namespace diferentes | F22/F23 | Fixture NB no vacía conserva elementos o falla explícitamente; preview final vinculado a revisión |
| Frontera de consulta/plan/aplicación | Delta mal tipado NB; contrato ready DC | F10/F11/F16/F19/F20 | Consulta sin escritura, allowlist/validación de plan, confirmación y permisos sin confiar en prompt |
| Atribución/contexto/historial definidos | Ausencias E15/E16 | F16/F17/F18/F20 | Actor del servidor, orden/identidad de mensajes, acceso por proyecto y contexto por participante, recuperación consistente |
| Artefacto generado realmente válido | Tests ZIP/texto sin javac | F24 | Compilar y ejecutar casos representativos en toolchain aislada, sin declarar éxito por texto |
| Entorno y contratos destino | Versiones Django/SDK/Redis/driver distintas; suites incompletas | Toda adaptación | Tests en Django5.2/Angular declarados y PG/Redis aislados, dependencias explícitas, sin copiar requirements/migraciones |

Estos gates describen condiciones y dependencias; no son implementación, selección definitiva ni secuencia de migración.

## H. Evaluación especial de XMI

### Qué está confirmado y qué no

**Defecto reproducido de compatibilidad en parser:** F3/X3 y el log T3/cross-xmi-final.log contienen la prueba dirigida CrossXmiTests.test_nb_ea_fixture_classifier_count_survives_diagramcraft_parser. La fixture NB/backend/generador/fixtures/diagramaExamen.xml tiene nueve packagedElement Class/AssociationClass principales; parse_xmi del donante devuelve nodes=[], edges=[], report.errors=[] y warning ea_core_only. La aserción esperada9 falla0!=9. El conteo inicial18 incluía definiciones duplicadas de extensiones: se corrigió sólo el harness y se repitió el caso en fase 3. El número válido es9.

**Respaldo estático suficiente de la causa concreta:** DB/diagramas/xmi.py::_attr consulta atributos sin namespace o XMI20131001; la fixture usa http://schema.omg.org/spec/XMI/2.1. El exportador NB declara ese mismo URI antiguo. No se produjo una nueva exportación NB en esta fase para afirmar que todos sus documentos fallen; la reproducción es sobre la fixture concreta.

**Riesgo potencial:** un resultado vacío aceptado como válido en una importación replace podría eliminar contenido. La vista DC permite reemplazo y su serializer admite documentos vacíos, pero **no se ejecutó reemplazo/guardado de esa fixture**. No se declara borrado de datos confirmado por X3. Tampoco se extiende a todos los perfiles XMI2.1, todas las exportaciones o toda interoperabilidad EA.

| Pregunta de evaluación | Conclusión |
|---|---|
| Funcionalidades afectadas | Lectura del perfil viejo NB por parser DC; futura interoperabilidad cruzada y seguridad de reemplazo. No defecto demostrado del exportador DC ni de la importación actual NB en su fixture |
| Evidencia a favor de conservar NB | XMIImporter/XMIExporter ya conectados a ORM y Angular; roundtrip9entidades/33atributos/10relaciones en fase 1. Preservar F21 evita una regresión conocida de perfil |
| Límites NB | bigint→integer probado, límites de entrada desiguales, paquetes/semántica/layout no certificados. Conservar no significa dar interoperabilidad total por buena |
| Capacidad donante útil | Límites2MB/20000/depth100, lxml acotado sin DTD/red, dry_run/report, mapping y selección; geometría y seis relaciones con tests internos |
| Compatibilidad | FUSIONAR F22 mediante adaptador; no reemplazo automático. F23 certificación EA real sigue INVESTIGAR/NE |
| Prioridad | F21: P2 conservar base; F22: P1 mejora. X3 es gate obligatorio de integridad de la alternativa antes de incorporarla; no una obligación académica de migración |
| Esfuerzo/riesgo | F22 esfuerzo4/riesgo5: namespaces, DTO ORM, referencias, revisión, UI y tests cruzados |
| Verificaciones faltantes | Perfiles/versiones EA objetivo, exportación→parser opuesto, semántica de relaciones/multiplicidad/whole y posiciones, rechazo de vacío inesperado, reemplazo con revisión, vuelta manual en EA |

Alternativa directa A03 se descarta por incompatibilidad concreta, aunque tenga límites de seguridad atractivos. La valoración cuantitativa de sus beneficios no anula el fallo reproducido. No hubo nueva prueba XMI durante fase 4 porque el código/fixture/harness siguen vigentes.

## I. Evaluación especial de WebSocket

### Reconciliación y concurrencia: separar tres comportamientos

| Evidencia | Categoría y alcance | Impacto confirmado | Impacto aún no acreditado |
|---|---|---|---|
| H-N03, fase 1: _guardar_snapshot_db recibe snapshot anterior vacío tras crear entidad | Defecto reproducido en rutina real/BD aislada | La rutina devuelve éxito y elimina la entidad posterior; pérdida secuencial persistida en prueba | Carrera multihilo PostgreSQL o incidente de usuario en producción |
| R3a, fase 3: WhiteboardApiService.reconciliarDatosDiagrama con ORMrelaciones[] y snapshot id44 | Comportamiento reproducido del método Angular extraído | Resultado contiene relación44 que ORM no devolvió | Persistencia posterior de esa relación y pérdida de datos en navegador real |
| R3b, fase 3: entidad intermedia9 sin vínculo y primera asociación2 | Comportamiento reproducido del mismo método | Se asigna clase_asociacion_id9 a la primera candidata sin correspondencia semántica | Que toda asociación-clase real quede mal enlazada o que esto haya ocurrido en un proyecto de usuario |
| H2-D01, fase 2: cambio durante fake proveedor | Defecto reproducido en secuencia simulada del backend DC | Propuesta de contexto0 ligada a revisión1; aplicar esperando1 sobrescribe título y avanza2 | Que todo cliente lo acepte: si mantiene expected_revision0 puede recibir409 |
| WS DC valida serializer y guarda raw en save_diagram_if_user_can_access | Diferencia estática confirmada del flujo de código; riesgo potencial de datos | Existe divergencia de qué objeto se guarda respecto a REST | Caso de documento efectivamente distinto persistido por normalización; sin prueba nueva DB |

F06 adapta expected_revision/lock/409, filtros de generación/revisión y respuesta autoritativa de DC, conservando eventos finos/canvas NB. Se debe mejorar la autoridad actual de NB y eliminar reconciliación semántica por heurística; no importar JSON y mantener ORM como escritor paralelo. Revisión debe abarcar PATCH, snapshot, importación y planes. Los controles del donante son referencias parciales y requieren resolver la ventana H2-D01 y la diferencia raw/validated_data.

Prioridad del problema: **P0**, por H-N03 reproducido y autorización vigente; esfuerzo5/riesgo5 de integración transversal. No se deduce ese nivel de un supuesto ataque de red ni se afirma que R3 haya borrado información. La comparación F06 frente a A02 es sobre adaptar patrones existentes o desarrollar un servicio propio; ambas requieren garantías verificables del agregado.

### Revocación: lectura y escritura diferentes

S3 está documentado y localizado. La prueba RevocationHandlerTests.test_member_removed_handler_does_not_close_and_later_update_is_sent extrae los métodos reales DB/diagramas/consumers.py::DiagramaConsumer.member_removed y diagram_update, con send_json/close simulados. Se notifica member.removed, no se llama close y el siguiente diagram.update se envía. La inspección muestra que diagram_update no revalida membresía antes de entregar; la cadena de grupos/notificaciones sigue en proyectos/realtime y consumer.

**Confirmado en el límite del handler:** falta de cierre y aceptación de una entrega posterior en simulación. **Riesgo potencial de seguridad:** una conexión ya abierta de un miembro retirado, que ignore el aviso del frontend y permanezca en el grupo, podría seguir recibiendo documentos. No se ha probado sesión retirada real+Redis+handshake+grupo ni una explotación de red completa. Una sesión que intente escribir sí pasa por save_diagram_if_user_can_access y puede cerrarse por403/4403; ese control no protege por sí solo a quien sólo escucha.

DF/DiagramCanvas responde al retiro con returnToPrincipalCanvas y hace comprobaciones de acceso; es defensa UX que un cliente puede no seguir. NB tiene además H-N02, con escritura tras retiro/visualizador reproducida en su rutina. No deben confundirse ambos hallazgos ni copiar el consumer DC como solución global.

| Aspecto | Evaluación |
|---|---|
| Usuarios/sesiones en alcance | Canales de miembros previamente autorizados y luego retirados, o con rol cambiado; múltiples pestañas y canales deben considerarse. La cuenta ajena nunca conectada no está probada por S3 |
| Controles existentes aprovechables | Autenticación handshake, membresía, roles por escritura, grupos, avisos y presencia/TTL; NB JWT debe conservarse |
| Alternativas a investigar | Cierre y group_discard dirigidos a todos los canales afectados; revalidación de entrega/expiración según coste; invalidación de permisos y pruebas multiworker |
| Prioridad | F05: P0 por autorización/integridad; F07: P0 por continuidad segura. El problema tiene prioridad aunque la solución donante esté incompleta |
| Riesgo y esfuerzo | F05 riesgo 5/esfuerzo 4; F07 riesgo 4/esfuerzo 4. Son estimaciones de una integración incorrecta, no calificación de explotación probada |
| Verificaciones faltantes | Retiro y cambio de rol con varios sockets, recibir sin escribir, grupos compartidos, reconexión rechazada, ausencia de entregas posteriores y no expulsión de otros miembros |

No se corrigieron los handlers, las heurísticas ni los permisos en esta fase.

## J. Comparación de alternativas

Se comparan soluciones materialmente distintas. Las filas F son las alternativas principales ya evaluadas; A son alternativas de contraste, **no funcionalidades adicionales ni puntos acumulables**. No se ordenan por nota. La prioridad en una alternativa A se refiere al problema común que intenta resolver; no la convierte en recomendación de ejecutar esa solución.

| Problema/necesidad | Alternativas consideradas | Diferencia material, beneficio y decisión preliminar |
|---|---|---|
| Conservar seguridad/integridad del tablero | A01 no cambiar nada; F05/F06 adaptar controles; A02 diseñar revisión propia desde NB | A01 es barata/nativa pero no resuelve defectos probados. F05/F06 aprovechan mecanismos y pruebas con adaptación; A02 mantiene dominio nativo y exige algoritmo/contrato nuevo. No se elige sólo por diferencia de pocos puntos: ambos diseños deben cubrir todo escritor |
| Preguntas/respuestas atribuidas, memoria e historial obligatorios | A04 sólo arrays locales; F30 segundo Diana completo; F16/F17/F18/F20 DESARROLLO NUEVO en chat NB | Los dos primeros no cumplen el conjunto del enunciado. La solución nueva construye lo que falta; no se vende como migración. F17/F20 siguen NE por garantías desconocidas, no dejan de ser obligaciones |
| Consultas frente a cambios IA | F19 separar respuesta de lectura; F10/F11 adaptar operaciones/planes; A05 portar todo backend Diana | F19 conserva intención conceptual NB, F10/F11 incorporan frontera de cambio autorizado. A05 trae modelo JSON/auth sin memoria de equipo y con brechas; se descarta como conjunto. Los límites de lectura y modificación deben ser diferentes |
| Interoperabilidad XMI | F21 conservar perfil NB; A03 sustituir parser directamente; F22 fusionar perfiles/preview/límites; F23 investigar EA real | F21 mantiene capacidad probada acotada, A03 rompe fixture conocida, F22 ofrece mejora con gates y F23 reconoce verificación ausente. Conservar y fusionar son complementarios según alcance, no una orden de sustituir |
| Generación Spring | Mantener alcance XML (F21) sin añadir Spring; F24 migrar capacidad con adaptador; A06 generador propio desde cero | No añadir Spring no incumple chat y evita alcance adicional. F24 reutiliza normalizador/plantillas pero exige semántica/compilación; A06 obliga construir todo. Beneficio potencial no justifica desplazar brechas P0 |
| Proveedor y UI | F32 conservar Gemini/config y aislar adaptador; F29 local/otro proveedor; F30 portar React/sesión/chat | Config actual atiende base R19 sin exigir multimarcas. F29 es opcional y NE hasta conocer motor/hardware. F30 viola arquitectura/no resuelve memoria; no obtiene mérito por mayor código |

### Evaluación separada de alternativas A

| Alternativa | Decisión | Puntuación | Prioridad del problema | Esfuerzo /5 | Riesgo /5 | Confianza |
|---|---|---|---|---|---|---|
| A01 Mantener snapshots/permisos actuales sin endurecimiento | DESCARTAR | 62.0 | P0 | 1 | 5 | ALTA |
| A02 Revisión/persistencia propias diseñadas desde NodoBoard | DESARROLLO NUEVO | 76.0 | P0 | 5 | 5 | MEDIA |
| A03 Sustituir XMI NB por parser DC directamente | DESCARTAR | 36.0 | P1 | 4 | 5 | ALTA |
| A04 Usar sólo historial local como chat grupal recuperable | DESCARTAR | 62.0 | P0 | 1 | 4 | ALTA |
| A05 Portar backend completo Diana/JSON/planes/sesión | DESCARTAR | 54.0 | P0 | 5 | 5 | ALTA |
| A06 Crear un generador Spring propio completo sin reutilizar donante | DESARROLLO NUEVO | 47.0 | P2 | 5 | 4 | MEDIA |

Esfuerzo/riesgo y motivos de cada alternativa:

| Alternativa | Problema/prioridad | Esfuerzo | Riesgo y gate | Evidencia |
|---|---|---|---|---|
| A01 | P0 es prioridad del problema; esta alternativa no lo resuelve | Sin trabajo funcional, sólo preservar estado defectuoso | No resuelve snapshots viejos ni autorización por escritura | E05,E08 |
| A02 | Problema P0, alternativa específica por evaluar frente F06 | Nuevo servicio/contrato de revisión y pruebas completas | Diseño sin garantías probadas, exige mismos gates que adaptar | E01,E05,E08 |
| A03 | P1 del problema/mejora; alternativa vetada por X3 | Copiar no resuelve tipos/roles/UI y perfiles | Vacío aceptado como éxito y reemplazo potencial; no borrado real probado | E14,E17,E18 |
| A04 | P0 de R2-R11/R18; alternativa insuficiente | Sin componente servidor nuevo | Incumplimiento académico si se presenta como conversación compartida | E15 |
| A05 | P0 del problema de control IA, no razón para portar todo | Reescritura auth/datos/API/cliente y garantías | Hereda defectos y deshabilita capacidades propias sin cubrir brechas nuevas | E04,E06,E12,E15,E25 |
| A06 | P2 del exportador opcional; no desplaza obligaciones | Diseño y construcción completa de generador y toolchain | Errores JPA/Java y mantenimiento de todas las plantillas | E01,E19 |

### Desglose aritmético de alternativas A

Mismos pesos, rúbrica y reglas NE que D. Los ceros de C/I de F30 o I de A06 expresan incompatibilidad explícita o reconstrucción sin reutilización del generador; no datos faltantes. Aunque A01/A04 alcancen una nota media por relevancia del problema, compatibilidad y facilidad de no cambiar nada, **se descartan por no resolver la necesidad y por sus gates**, no se presentan como soluciones recomendables.

| ID / alternativa | Base de evaluación | R | B | C | I | Q | M | U | Total /100 | Interpretación |
|---|---|---|---|---|---|---|---|---|---|---|
| A01 Mantener snapshots/permisos actuales sin endurecimiento | BASE/ADAPTACIÓN | 5/5 → 25.0 | 0/5 → 0.0 | 5/5 → 15.0 | 5/5 → 15.0 | 1/5 → 2.0 | 2/5 → 4.0 | 1/5 → 1.0 | 62.0 | Conveniencia condicionada |
| A02 Revisión/persistencia propias diseñadas desde NodoBoard | BASE/ADAPTACIÓN | 5/5 → 25.0 | 5/5 → 20.0 | 5/5 → 15.0 | 1/5 → 3.0 | 1/5 → 2.0 | 3/5 → 6.0 | 5/5 → 5.0 | 76.0 | Recomendable, sujeto a dependencias |
| A03 Sustituir XMI NB por parser DC directamente | BASE/ADAPTACIÓN | 2/5 → 10.0 | 3/5 → 12.0 | 1/5 → 3.0 | 1/5 → 3.0 | 1/5 → 2.0 | 2/5 → 4.0 | 2/5 → 2.0 | 36.0 | Baja conveniencia |
| A04 Usar sólo historial local como chat grupal recuperable | BASE/ADAPTACIÓN | 5/5 → 25.0 | 0/5 → 0.0 | 5/5 → 15.0 | 5/5 → 15.0 | 1/5 → 2.0 | 2/5 → 4.0 | 1/5 → 1.0 | 62.0 | Conveniencia condicionada |
| A05 Portar backend completo Diana/JSON/planes/sesión | BASE/ADAPTACIÓN | 5/5 → 25.0 | 3/5 → 12.0 | 1/5 → 3.0 | 1/5 → 3.0 | 2/5 → 4.0 | 2/5 → 4.0 | 3/5 → 3.0 | 54.0 | Conveniencia condicionada |
| A06 Crear un generador Spring propio completo sin reutilizar donante | BASE/ADAPTACIÓN | 1/5 → 5.0 | 5/5 → 20.0 | 4/5 → 12.0 | 0/5 → 0.0 | 1/5 → 2.0 | 2/5 → 4.0 | 4/5 → 4.0 | 47.0 | Baja conveniencia |

#### A01 — Mantener snapshots/permisos actuales sin endurecimiento

Evidencia: E05,E08. Decisión: DESCARTAR. BASE/ADAPTACIÓN.

- R (Relevancia), 5/5; contribución 25: El problema de seguridad/sincronía es obligatorio.
- B (Beneficio incremental), 0/5; contribución 0: No añade control al defecto existente.
- C (Compatibilidad), 5/5; contribución 15: Nativo porque no cambia arquitectura.
- I (Facilidad), 5/5; contribución 15: No requiere integración nueva.
- Q (Calidad/seguridad/pruebas), 1/5; contribución 2: Defectos reproducidos impiden considerar seguro el límite.
- M (Mantenibilidad), 2/5; contribución 4: Deuda persiste en varios escritores.
- U (Experiencia esperada), 1/5; contribución 1: Experiencia sigue expuesta a pérdida/rechazo incoherente.

#### A02 — Revisión/persistencia propias diseñadas desde NodoBoard

Evidencia: E01,E05,E08. Decisión: DESARROLLO NUEVO. BASE/ADAPTACIÓN.

- R (Relevancia), 5/5; contribución 25: Integridad del tablero es obligatoria.
- B (Beneficio incremental), 5/5; contribución 20: Puede cubrir todos los escritores con contrato propio.
- C (Compatibilidad), 5/5; contribución 15: Encaja íntegramente en agregado ORM destino.
- I (Facilidad), 1/5; contribución 3: Algoritmo/servicio de revisión nuevo de amplio alcance.
- Q (Calidad/seguridad/pruebas), 1/5; contribución 2: Sólo base existente, sin pruebas de algoritmo nuevo.
- M (Mantenibilidad), 3/5; contribución 6: Cohesión posible; diseño aún incierto.
- U (Experiencia esperada), 5/5; contribución 5: Recuperación/control esperados altos, no medidos.

#### A03 — Sustituir XMI NB por parser DC directamente

Evidencia: E14,E17,E18. Decisión: DESCARTAR. BASE/ADAPTACIÓN.

- R (Relevancia), 2/5; contribución 10: No obligatorio para chat.
- B (Beneficio incremental), 3/5; contribución 12: Preview/límites potenciales, anulados por incompatibilidad directa.
- C (Compatibilidad), 1/5; contribución 3: Namespaces/ORM/IDs no equivalen.
- I (Facilidad), 1/5; contribución 3: Traslado aparente oculta adaptación amplia.
- Q (Calidad/seguridad/pruebas), 1/5; contribución 2: Caso cruzado confirmado falla sin error del parser.
- M (Mantenibilidad), 2/5; contribución 4: Dos dialectos sin adaptador elevan soporte.
- U (Experiencia esperada), 2/5; contribución 2: Riesgo de regresión al importar documento conocido.

#### A04 — Usar sólo historial local como chat grupal recuperable

Evidencia: E15. Decisión: DESCARTAR. BASE/ADAPTACIÓN.

- R (Relevancia), 5/5; contribución 25: El requisito de grupo/historial sí es obligatorio.
- B (Beneficio incremental), 0/5; contribución 0: Array local no agrega difusión ni recuperación.
- C (Compatibilidad), 5/5; contribución 15: Es nativo al chat actual.
- I (Facilidad), 5/5; contribución 15: Conservarlo es fácil.
- Q (Calidad/seguridad/pruebas), 1/5; contribución 2: No hay contrato persistido compartido y se pierde al recargar.
- M (Mantenibilidad), 2/5; contribución 4: No soporta contexto de equipo y actor recuperable.
- U (Experiencia esperada), 1/5; contribución 1: Sólo el emisor ve su diálogo, no la experiencia pedida.

#### A05 — Portar backend completo Diana/JSON/planes/sesión

Evidencia: E04,E06,E12,E15,E25. Decisión: DESCARTAR. BASE/ADAPTACIÓN.

- R (Relevancia), 5/5; contribución 25: Pretende resolver cambios autorizados obligatorios.
- B (Beneficio incremental), 3/5; contribución 12: Añade planes pero no chat/memoria del requisito.
- C (Compatibilidad), 1/5; contribución 3: Modelo JSON/sesión no encaja con ORM/JWT existente.
- I (Facilidad), 1/5; contribución 3: Reescritura amplia de contratos y Angular.
- Q (Calidad/seguridad/pruebas), 2/5; contribución 4: Tests del donante con carrera/retry/legacy/revocación.
- M (Mantenibilidad), 2/5; contribución 4: Aumenta deuda y dualidad de representaciones.
- U (Experiencia esperada), 3/5; contribución 3: Plan visible ayuda, pero migración perturba editor y sesiones.

#### A06 — Crear un generador Spring propio completo sin reutilizar donante

Evidencia: E01,E19. Decisión: DESARROLLO NUEVO. BASE/ADAPTACIÓN.

- R (Relevancia), 1/5; contribución 5: No requisito del chat.
- B (Beneficio incremental), 5/5; contribución 20: Capacidad final potencial nueva.
- C (Compatibilidad), 4/5; contribución 12: Puede diseñarse para ORM NB.
- I (Facilidad), 0/5; contribución 0: Hay que construir transformación/plantillas/capas desde cero.
- Q (Calidad/seguridad/pruebas), 1/5; contribución 2: Bases ORM, sin generador propio ni compilación probada.
- M (Mantenibilidad), 2/5; contribución 4: Soportar JPA/build/versiones enteramente nuevo.
- U (Experiencia esperada), 4/5; contribución 4: Descarga útil si llega a validarse.

Los valores F06 y A02 cercanos no acreditan una superioridad estadística. Con esta escala, cambiar un punto en R/B/C/I/Q/M/U altera el total en5/4/3/3/2/2/1 puntos, respectivamente. Diferencias pequeñas son sensibles al diseño; se deben discutir junto a evidencia y riesgos. No se calculó una suma ni un ranking entre F16/F17/F18/F20 porque comparten bases y no todas son evaluables.

## K. Dependencias técnicas

### Dependencias reales del código actual

| Relación comprobada | Archivos/contrato | Naturaleza y consecuencia |
|---|---|---|
| Usuario/miembro → proyecto y acceso al diagrama NB | UserColaborador, ProyectoDetailView/DiagramaCargaInicialView, PizarraConsumer.connect | Obligatoria actual para acceso previsto; fallos de escritura no anulan esa relación, exigen uniformarla |
| JointJS/servicios → snapshot → ORM y remapeos | WhiteboardPage/Canvas/Socket → guardar_snapshot → _guardar_snapshot_db → snapshot_guardado | Obligatoria actual de persistencia del editor; no prueba revisión ni entrega en cierre |
| Fuente JSON DC → serializer/planes/XMI/Spring | Diagrama.nodes/edges → DiagramaSerializer/execute_operations/parse_xmi/normalize_diagram | Obligatoria actual en donante; explica por qué copiar modelos UML legacy no traslada funciones del editor |
| Revisión/permisos → guardado/aplicación DC | DiagramaViewSet.perform_update, save_diagram_if_user_can_access, apply_plan | Obligatoria en esos contratos; import final y ventana antes de PlanIA no heredan todas las garantías automáticamente |
| Proveedor/contrato → interpretación DC | get_ai_provider, validate_provider_response → execute_operations/create_plan | Actual, con gramáticas locales que pueden evitar proveedor; SDK remoto falta. No depende de React para negocio, sí de su DTO |
| Evento autoritativo → estado local DF | publish_diagram_update → useDiagramSocket → collaborationSync/restore | Actual; publicación no demuestra entrega única o resync completo |
| Generación → modelo generable | normalize_diagram y generate_spring_boot_zip | Actual: validar JPA/identidad/ownership más exigente que dibujar |
| Chat local → request sin historial | mensajesChat/aiHistory → instrucción+contexto/resumen | Actual y evidencia negativa de dependencia: arrays NO alimentan memoria grupal ni recuperación backend |

### Dependencias de una solución futura, como restricciones de diseño

Estas relaciones se infieren de la necesidad y de interfaces existentes; no se presentan como llamadas implementadas ni como orden final de trabajo.

| Capacidad dependiente | Dependencia | Tipo | Justificación |
|---|---|---|---|
| F05 permisos | F04 identidad/pertenencia | Obligatoria | Actor y acceso al proyecto se resuelven en servidor, no desde texto/modelo |
| F06 revisión/reconciliación | F03 reglas y F05 autorización | Obligatoria de integridad | El mismo escritor debe validar, autorizar y comparar revisión para todos los caminos |
| F07 presencia/resync | F05 y F06 | Obligatoria para sincronización segura objetivo | Reconectar no puede autorizar por estado antiguo ni restaurar snapshot obsoleto |
| F10/F11 planes | F03/F05/F06/F13/F32 | Obligatoria | Validación, permiso, misma revisión del contexto y proveedor configurable; un plan no concede acceso |
| F12 dedupe | Contrato de F11/F06 | Obligatoria en alcance de aplicación/retry | Misma clave no debe ser nueva aplicación ni promesa de evento único no implementada |
| F16 mensajes grupales/actor | F04/F05/F07 y contrato de mensajes | Obligatoria para el requisito compartido | Autenticar a quien pregunta y distribuir por proyecto. No basta publicar nodos |
| F18 historial | Esquema/identidad/orden de mensajes F16 y F05 | Obligatoria | Guardar/consultar preguntas/respuestas propias del proyecto; no reutilizar tabla de planes |
| F17 memoria | F16/F18 y contexto de diagrama F13 | Obligatoria para R8-R11 objetivo | Recuperación e identidad permiten construir contexto grupal/individual con referencias al tablero |
| F20 moderación | F17/F19/F13/F32 | Obligatoria para alcance contextual propuesto | Requiere diálogo/actor/contexto, consulta segura y política de asesoría; calidad real sigue pendiente |
| F19 consulta | F05/F13/F32; F16 para compartir respuestas | Obligatoria en grupo; F16 no para consulta local aislada | Consulta no debe heredar permiso de editar. La participación de lector necesita contrato propio |
| F14 voz final | Chat/servicio existente; F11 sólo si confirma por voz | Base actual obligatoria; plan opcional para voz | Reconocer texto no exige PlanIA; confirmar cambio por voz sí necesita la misma autorización |
| F15 TTS | Entrada/escucha coordinada y preferencia | Opcional | Puede hablar texto sin reemplazar el proveedor ni ser requisito académico |
| F22 XMI | F21 perfil NB, F03/F05/F06 y resolver X3 | Obligatoria si se incorpora | Preview y reemplazo deben respetar dominio, permisos y revisión; no sustitución automática |
| F24 Spring | F02/F03 y decisiones JPA/ownership, permisos F05 | Obligatoria si se incorpora | El DTO NB actual no contiene todo lo que exige el generador; compilación es gate de validación |
| F08/F09 locks/undo | F05/F06 y política de operación por decidir | Pendiente de diseño | No se exige lease o inversa colaborativa para adoptar revisión; no retrasar obligatoriedad por opcionales |
| F29 local | F32 adaptador y motor/hardware por definir | Opcional y pendiente | No bloquea R19 ni obliga a reemplazar Gemini |
| F31 enlace invitación | F04 firma/aceptación y F05 | Obligatoria para ese recorrido | Falta ruta Angular, no falta toda infraestructura de invitación |
| F27 pruebas/contratos | Entorno correcto y cada alcance modificado futuro | Transversal obligatoria de verificación | Fakes/SQLite actuales no certifican PG/Redis/navegador/Java |

F16 y F18 comparten el diseño del mensaje; no se propone duplicar su modelo ni desarrollarlos como silos. La tabla no define sprints, nuevos nombres de archivos, esquema final, API nueva ni secuencia global. La relación entre memoria y almacenamiento es de uso, no prueba de que ambos ya existan.

## L. Matriz cuantitativa consolidada

Las puntuaciones de desarrollo nuevo son estimaciones y están marcadas como tales; NE no es0. La evidencia va en la primera columna mediante IDs de C. Se mantiene el orden temático, sin columna de ranking.

| Funcionalidad | Estado NodoBoard | Aporte DiagramCraft | Decisión | Puntuación /100 | Prioridad | Esfuerzo /5 | Riesgo /5 | Confianza |
|---|---|---|---|---|---|---|---|---|
| F01 Editor base: entidades/clases relacionales, atributos y operaciones visuales [E01,E02] | Parcial: Angular/JointJS y ORM conectados; tsc y persistencia acotada | Editor React Flow conectado; no sustituir motor | CONSERVAR | 66.0 | P0 | 1 | 3 | ALTA |
| F02 UML ampliado: kinds, métodos, realización/dependencia y ownership [E01,E03] | Sin métodos/kinds diferenciados y sólo cuatro relaciones | Contrato de seis relaciones, métodos y kinds validado | ADAPTAR | 51.0 | P2 | 4 | 4 | MEDIA |
| F03 Validación determinista del dominio, tipos y multiplicidades [E01,E03,E07,E14] | Validación parcial; tipos/deltas débiles y bigint degradado | Serializer/operaciones con reglas y tests | ADAPTAR | 74.0 | P0 | 4 | 4 | ALTA |
| F04 Autenticación JWT, proyectos e invitaciones base [E02,E04] | Flujos propios; tres tests de proyectos y aceptación interna conectada | Sesión/CSRF/allauth y proyectos con otro contrato | CONSERVAR | 73.0 | P0 | 1 | 3 | ALTA |
| F05 Autorización uniforme y revocación REST/WS [E04,E05,E06] | Defectos reproducidos en PATCH y rutina snapshot tras revocación | Revalida escritura; S3 no cierra lectura y legacy vulnerable | ADAPTAR | 76.0 | P0 | 4 | 5 | ALTA |
| F06 Revisión, reconciliación y guardado autoritativo [E05,E07,E08] | Snapshot obsoleto elimina entidades; R3 reintroduce relaciones por heurística | expected_revision/lock/409 y filtros de estado; carrera F2 conocida | ADAPTAR | 79.0 | P0 | 5 | 5 | ALTA |
| F07 Conectividad colaborativa: presencia, reconexión y resync [E06,E08,E09] | Presencia por proceso y sin retry efectivo localizado | Presencia ORM/TTL, heartbeat y hook retry con buffer limitado | ADAPTAR | 78.0 | P0 | 4 | 4 | MEDIA |
| F08 Bloqueo fuerte por elemento con lease [E05,E09] | Avisos visuales y set por conexión; no exclusión fuerte acreditada | No equivalente de lease fuerte verificado | INVESTIGAR | NO EVALUABLE | P2 | NE | 4 | BAJA |
| F09 Undo/redo colaborativo seguro [E10] | Sin equivalente colaborativo sólido verificado | Historial local de 50 snapshots, no inversas concurrentes | INVESTIGAR | NO EVALUABLE | P2 | NE | 4 | BAJA |
| F10 Lenguaje natural a operaciones estructuradas del modelador [E03,E07,E11] | Delta cliente conectado, sin validación runtime estricta | execute_operations y gramáticas/fakes probados | ADAPTAR | 77.0 | P0 | 4 | 4 | MEDIA |
| F11 Plan IA persistido, preview y confirmación autorizada [E07,E11,E12] | Aplicación inmediata al éxito; sin PlanIA equivalente | Plan usuario/diagrama/TTL, confirmación y aplicación atómica | ADAPTAR | 79.0 | P0 | 5 | 5 | MEDIA |
| F12 Dedupe, retry e identidad de solicitud/aplicación [E07,E12] | Busy flag no es idempotencia persistida | request_id/hash y resultado, con retry409 y sin unique compuesto | ADAPTAR | 67.0 | P0 | 4 | 4 | ALTA |
| F13 Contexto autoritativo del diagrama y selección [E07,E11] | Contexto cliente omite multiplicidades; no revisión | build_diagram_summary de documento autorizado y selección | FUSIONAR | 77.0 | P0 | 3 | 4 | ALTA |
| F14 Voz: conservar push-to-talk y adaptar transcripción final [E13] | Entrada implementada por código con provisionales acumulados | isFinal/dedupe/estados probados en utilidades; matiz wake/send | ADAPTAR | 55.0 | P2 | 3 | 3 | MEDIA |
| F15 Síntesis de voz opcional [E13] | Sin speechSynthesis conectado localizado | speakDiana y dianaVoice: selección/segmentación probadas | ADAPTAR | 54.0 | P2 | 2 | 3 | MEDIA |
| F16 Chat grupal: preguntas/respuestas compartidas, actor y destinatario [E04,E06,E15,R2-R7] | mensajesChat local, sin broadcast de conversación | aiHistory local; PlanIA.usuario no es mensaje grupal | DESARROLLO NUEVO | 78.0 (estimación nueva) | P0 | 5 | 5 | MEDIA |
| F17 Memoria grupal/individual y continuidad de seguimientos [E15,E16,R8-R11] | No historia enviada ni memoria por actor | Sin memoria conversacional; resumen sólo de diagrama | DESARROLLO NUEVO | NO EVALUABLE (estimación nueva) | P0 | 5 | 5 | MEDIA |
| F18 Persistencia y recuperación autorizada del historial IA [E04,E15,R18] | Array volátil y limpiarHistorial local | Seis entradas locales; planes guardados no son diálogos | DESARROLLO NUEVO | 80.0 (estimación nueva) | P0 | 4 | 4 | MEDIA |
| F19 Consulta conceptual de sólo lectura separada de mutación [E07,E11,E16,R12] | Prompt permite mensaje sin delta; fake200 verificado | Sin modo answer; contrato de operaciones/clarificación | FUSIONAR | 79.0 | P0 | 3 | 4 | MEDIA |
| F20 IA moderadora/asesora contextual del equipo y recomendaciones [E15,E16,R13-R14] | Intención conceptual; no flujo de moderación de equipo | Planes de modelado; no moderación grupal equivalente | DESARROLLO NUEVO | NO EVALUABLE (estimación nueva) | P0 | 5 | 4 | BAJA |
| F21 XMI actual de NodoBoard: conservar entrada/salida [E14,E17] | Fixture importa/exporta/reimporta9/33/10; límites semánticos | Otro perfil parser; X3 incompatible con fixture NB | CONSERVAR | 57.0 | P2 | 1 | 3 | ALTA |
| F22 XMI: perfiles compatibles, límites seguros y preview versionado [E14,E17,E18] | Importación directa, sin preview equivalente | Límites/mapping/dry_run útiles; X3 y preview sin expected_revision | FUSIONAR | 54.0 | P1 | 4 | 5 | MEDIA |
| F23 Interoperabilidad semántica/visual certificada con EA [E14,E17] | Conteos de fixture, sin EA manual | Perfiles/layout probados parcialmente, sin vuelta EA real | INVESTIGAR | NO EVALUABLE | P2 | NE | 4 | BAJA |
| F24 Exportación Spring Boot por capas y validación del artefacto [E03,E19] | No generador Java conectado; generador sólo XML | ZIP Maven/Java21/Spring3.4/PostgreSQL; repos/service/controller/DTO/mapper | MIGRAR | 50.0 | P2 | 5 | 4 | MEDIA |
| F25 Ciclo de proyectos: archivar/restaurar/duplicar y roles extendidos [E02,E04,E20] | Base proyectos e invitaciones propia | Acciones/servicios específicos, con tests PG pendientes | ADAPTAR | 51.0 | P2 | 4 | 3 | MEDIA |
| F26 Errores estructurados, foco y accesibilidad básica [E08,E16,E21] | Toasts/roles/labels, errores heterogéneos | Códigos/element_id, Escape/aria-live y enfoque | FUSIONAR | 70.0 | P1 | 3 | 3 | MEDIA |
| F27 Contratos, separación de responsabilidades y pruebas de frontera [E01,E08,E11,E22] | Servicios propios; tests IA vacíos y entorno NB no fiel | Módulos/fakes/tests útiles, Canvas concentrado y deuda | ADAPTAR | 72.0 | P1 | 4 | 4 | MEDIA |
| F28 Entrada por imagen de NodoBoard [E07,E23] | Endpoint/compresión/normalización conectados, proveedor no probado | Sin equivalente de boceto a diagrama localizado | CONSERVAR | 46.0 | P2 | 1 | 3 | MEDIA |
| F29 Proveedor alternativo/LLM local opcional [E07,E11,E24,R20] | Parámetros Gemini; sin adaptador local/multiproveedor conectado | Factory Gemini y gramática; no LLM local real | INVESTIGAR | NO EVALUABLE | P3 | NE | 4 | BAJA |
| F30 Incorporación integral de Diana/React/auth/ORM legacy [E02,E06,E15,E25] | Un asistente Angular y dominio propio activos | UI/estado/sesión/legacy completos pero no chat grupal persistente | DESCARTAR | 19.0 | P3 | 5 | 5 | ALTA |
| F31 Completar enlace de invitación firmado sin reemplazar invitaciones [E02,E26] | Backend genera /invitacion/token; Angular no tiene ruta | Flujo distinto de invitaciones en API, no parche directo | ADAPTAR | 70.0 | P1 | 2 | 3 | ALTA |
| F32 Proveedor IA configurable y adaptador único en backend [E07,E11,E24,R19] | GEMINI_API_KEY/MODEL y SDK declarado | get_ai_provider separado, SDK ausente en requirements | FUSIONAR | 74.0 | P0 | 3 | 3 | ALTA |

No se declara adecuada toda capacidad CONSERVAR sólo por esa decisión: se conserva su integración/base, con límites y problemas separados. F01/F04/F21/F28 no duplican la nota de mejoras F03/F05/F06/F22. Ninguna nota representa puntos del examen ni porcentaje de funcionalidad implementada.

## M. Limitaciones de evaluación

- No se midieron exactitud conceptual, asesoría, seguimiento, moderación, latencia, coste ni disponibilidad de Gemini. No hubo llamadas externas IA ni audio real. Fakes acreditan transporte/validación y fallos específicos, no inteligencia.
- Los resultados backend heredados no son un entorno idéntico al destino: NB declara Django5.2 y se ejercitó parcialmente con6.1/URLconf reducido. DB suite85 obtuvo69 éxitos/1 fallo/15 errores SQLite por jsonb_array_length, sin certificar PostgreSQL ni ocultar problemas.
- NB tsc pasó; build y Karma quedaron impedidos por permisos/navegador. DF 28 tests Node, lint y build pasaron, sin componente E2E ni audio real. Mayor bundle/cantidad de archivos no otorgan puntos de calidad.
- XMI9/33/10 es conteo sobre una fixture; X3 prueba otro parser con ese perfil. No vuelta manual EA ni garantía de preservación completa. Spring ZIP/texto no es javac/Maven exitoso.
- S3 y H-N02 se reprodujeron en límites distintos: handlers o rutina real aislada; no vulnerabilidad de red completa probada. No se verificó Redis/multiworker ni revocación en dispositivos reales.
- El inventario SHA cubre archivos rastreados/no ignorados; no cada archivo ignorado instalado ni infraestructura. No se leyeron credenciales ni se conectaron bases reales para comparar datos/migraciones aplicadas.
- Esfuerzo/riesgo son estimaciones ordinales; notas de compatibilidad/mantenimiento/UX son juicios trazables, no tiempos, probabilidades ni estudio de usuarios. Las partes nuevas sin diseño reducen confianza.
- La clasificación de ausencia se refiere a flujos activos/modelos/contratos inspeccionados. No se prueba inexistencia abstracta de cualquier capacidad de un LLM o de una biblioteca externa.
- NE de F08/F09/F23/F29 responde a alcance/beneficio/garantías insuficientes; NE de F17/F20 responde a diseño/calidad de capacidad nueva. La obligación académica no se sustituye por una nota inventada.
- No se consultaron fuentes externas para afirmar soporte, vulnerabilidades o precios de versiones. Sólo se evalúa evidencia local suministrada y vigente.
- Requisitos R1–R19 se toman del maestro, no de una rúbrica del docente no adjuntada aparte. No se añadieron como obligatorios Spring, seis relaciones, voz, TTS, privacidad de chat oculto, múltiples proveedores o LLM local.

## N. Pruebas y verificaciones

### Evidencia reutilizada y resultados

Se releyeron maestro/informes y se comprobó su vigencia. No se ejecutaron nuevas pruebas funcionales: los hashes están iguales y las dudas principales ya tienen evidencia o deben permanecer NE. Se hicieron verificaciones de identidad/integridad, inspección estática focalizada y comprobación aritmética del informe.

| Origen | Resultado reutilizado | Límite conservado |
|---|---|---|
| Fase1 AST/pip/check |123 fuentes Python sin errores sintácticos; pip check0 y DB check0 | No import/runtime completo ni requirements completos; genai/psycopg2 faltantes en venv disponible |
| Fase1 DB |85 tests,69 pasan/1 fallo/15 errores; diagramas59yconfig6pasan | Fallo test antiguo sin expected_revision;15 errores jsonb_array_length en SQLite, no fallo PG probado |
| Fase1 NB |3tests propios+5probes8pasan; XMLfixture1caso conteos9/33/10 | Sondas de permisos/snapshot/bigint; URLconf parcial y versiones distintas |
| Fase1 probes DC |retry con revisión inicial→409 después de200; ClaseUML legacy movida a diagrama ajeno | Defectos en contratos específicos, no globales ni permiso de destino del canvas |
| Fase1 frontend |DF28Node/lint/build pasan; NBtsc pasa | NBbuild/Karma no completan por entorno; no navegador/voz/EA/Java |
| Fase2 NB |7 probes con fake pasan |Incluye delta string aceptado200, contexto incompleto y transporte conceptual. OK reproduce defecto donde corresponde |
| Fase2 DC |1 probe fake reproduce ventana revisión0→1→planbase1→apply2 |Secuencia simulada, cliente manteniendo0 puede rechazar |
| Fase3 X3 |Caso dirigido falla0!=9, errors[]/ea_core_only |Defecto parser, no reemplazo real; expectativa inicial18 corregida en temporal |
| Fase3 R3 |2 escenarios Node reproducidos,3 assert.equal |Método original transpilado en memoria; no HTTP/Angular/browser/guardado |
| Fase3 S3 |1test de handlers OK: no close y update posterior |Simulación de envío, sin red, base de datos ni Redis; OK no significa seguro |

Los registros originales continúan en estos directorios temporales, cuya permanencia depende de limpieza del sistema:

~~~text
T1=C:\Users\juan\AppData\Local\Temp\nodoboard-audit-52aff2032c65410ea64d503eabc879af
T2=C:\Users\juan\AppData\Local\Temp\nodoboard-phase2-f46ef03b467846458ffc3c28469ac040
T3=C:\Users\juan\AppData\Local\Temp\nodoboard-phase3-e613595407db4fe5b274031a09d001d7
T4=C:\Users\juan\AppData\Local\Temp\nodoboard-phase4-f855ab0c351b42189accaacb657ef42f
PY=D:\swProyecto\backend\.venv\Scripts\python.exe
~~~

Logs leídos de T3: cross-xmi-final.log, angular-reconcile.log y primeras líneas relevantes pure-backend.log; no se reejecutaron probes. F1§7 y F2§K conservan comandos/resultados completos; F3§N conserva pruebas puras y sus condiciones. Se preservan los fallos documentados; no se usa el logger “Gemini llamado” de una prueba fake como prueba de llamada real.

### Comandos y controles de esta fase

| Comando o script | Resultado / propósito |
|---|---|
| Get-Content -LiteralPath <attachment fase 4> -Raw -Encoding UTF8 | Instrucción completa; sólo informefase 4 como escritura persistente autorizada |
| Get-Item/Test-Path de raíces e informe destino | Tres rutas existentes; informe ausente antes de escribir |
| git -c safe.directory=<raíz> --no-optional-locks -C <raíz> status --porcelain=v1 --untracked-files=all | Registro inicial/final sin config ni reversión de cambios |
| Mismo prefijo git con rev-parse --show-toplevel/HEAD, branch --show-current, remote get-url origin, ls-files --cached --others --exclude-standard | Identidad/ramas/commits/inventarios verificados |
| rg --files -g AGENTS.md; rg -n sobre clases/handlers/planes/historial/voz/configuración; Get-Content por rangos; Get-Item de archivos React vacíos | Inspección focalizada y confirmación de evidencia existente; no nueva auditoría funcional completa |
| Get-Content UTF8 de maestro y fases1–3 | Lectura completa. Salidas largas truncadas se complementaron por tramos; no se dedujo ausencia de líneas no visibles |
| PY -B T4/snapshot.py T4 | Línea base1888 archivos, comparación1885/1886/1887 sin cambios, hash de cuatro documentos e initial-git.json |
| PY -B T4/evaluation.py T4 | Construye evaluación/alternativas fuera de repos;32 funcionalidades y6 alternativas, sin importar apps ni ejecutar negocio. Una segunda ejecución completó el catálogo de alternativas, no repitió tests |
| PY -B T4/render_report.py T4 | Verifica rango de notas, pesos, contribuciones, totales, IDs/decisiones/prioridades, nuevas brechas y estructura A–O; genera staged-report.md en T4 |
| PY -B T4/qa_report.py T4 | Contraste independiente con Fraction de las 38 filas de cálculo renderizadas (32 funciones y 6 alternativas), secciones y referencias de rutas |
| PY -B T4/publish_report.py T4 | Recomprueba hashes/Git, crea sólo AUDITORIA_FASE_4.md con modo exclusivo, añade verificación de integridad y comprueba archivo cerrado |

Se creó T4 nuevo con GUID, fuera de repositorios. Allí están snapshot.py, baseline.json, initial-git.json, validity.json, evaluation.py/.json, alternatives.json, report-template.md, render_report.py, staged-report.md, arithmetic-check.json, qa_report.py/qa-check.json, refine_template.py y publish_report.py/final-verification.json. Ningún script temporal necesita red, credentials, ORM, subprocess de aplicación ni bases de datos; sólo los de inventario/publicación consultan Git en modo lectura. Se utilizó Python explícito con -B para no generar bytecode. No se instalaron paquetes.

La validación aritmética comprueba cada contribución con Decimal y suma de pesos100; un segundo control independiente con Fraction compara las 38 filas de celdas realmente renderizadas. Verifica también que una nota NE implique totalNE, sin normalización; no valida por sí misma la certeza de los juicios, cuyas razones y fuentes están en D/C. No se realizan tests de aplicación exclusivamente para justificar números.

### Pruebas omitidas

| Prueba | Motivo |
|---|---|
| Suites Django, makemigrations/migrate, endpoints sobre bases existentes | Prohibición de migraciones/escrituras; evidencia previa suficiente para evaluación y ninguna fuente cambió. No tocar credenciales/config para forzar ejecución |
| Redis/PG/multiworker/dos navegadores | No entorno completo acreditado aislado; no se inicia infraestructura ni se usa desarrollo. Mantener alcance parcial y gates |
| Build/lint/tsc/Karma repetidos | Sin cambio de fuentes y sin pregunta nueva que lo requiera; evitar caches/output en repos y repetición innecesaria |
| Proveedor externo, audio real, SMTP/OAuth | Prohibido enviar datos/llamar IA y sin necesidad para cálculo; no activar servicios por una puntuación |
| EA manual, compilación Java/Maven, ejecución Spring | Sin toolchain/entorno aislado acreditado sin instalaciones/red; no convertir ZIP o conteos en éxito integrado |
| NUEVOS tests de memoria/moderación/historial | Funcionalidades ausentes: requerirían implementación no autorizada. Puntuar viabilidad o marcarNE, sin inventar tests |
| Nuevas reproducciones destructivas XMI o de pérdida/revocación | Evidencia existente basta para el límite documentado; no provocar pérdida o ataques reales para ampliar una afirmación |
| Auditoría externa de vulnerabilidades o versiones | Fuera del alcance local, sin red/instalaciones; no se certifica ausencia de vulnerabilidades |

No hubo llamadas reales a Gemini/OpenAI/otros proveedores, envío de diagramas/código a servicios externos mediante pruebas, instalaciones, migraciones, cambios de configuración, commits/pushes, despliegues o acciones AWS.

## O. Recomendaciones preliminares

### Funcionalidades que NodoBoard debe conservar

F01 editor/Angular/JointJS y dominio ORM; F04 JWT, usuarios, proyectos, dashboard e invitaciones internas; F21 XMI que procesa la fixture actual; F28 entrada por imagen con proveedor real pendiente. Mantener un único chat Angular y la configuración Gemini de F32. No conservar sus defectos: permisos/revisión/validación se evalúan por separado. La facilidad de conservar puede elevar una nota, pero no es evidencia de cumplimiento completo.

### Capacidades de DiagramCraft que convendría adaptar

F03 validación tipada y multiplicidades, F05 controles uniformes sin heredar S3/legacy, F06 revisión/estado autoritativo sin carrera F2, F07 presencia/reintento/resync, F10 operaciones, F11 planes/confirmación y F12 identidad de retry con garantías corregidas. F14/F15 voz final/TTS son opcionales y no justifican reemplazar chat. F25 lifecycle y F27 contratos/tests ofrecen mejoras condicionadas. F24 generación Spring es una capacidad migrable mediante adaptador y validación real del artefacto, no una obligación académica ni un cambio de backend.

### Funcionalidades que requieren fusión

F13 contexto de documento del dominio NB con procedencia/selección autorizada; F19 intención conceptual NB con contrato estricto que no permita mutación; F22 perfiles NB y límites/preview del donante después de resolver X3; F26 errores/foco/accesibilidad Angular; F32 configuración actual con adaptador único. F31 debe completar el recorrido propio de invitación, no sustituir el sistema completo por el donante.

### Funcionalidades que deberían descartarse como alternativa de incorporación

F30: segundo Diana íntegro, React/React Flow/Zustand embebidos para reemplazar Angular, nueva sesión/allauth sólo para planes, CRUD UML legacy paralelo y archivos vacíos presentados como capacidades. A01/A04 no resuelven integridad ni conversación aunque sean fáciles; A03 sustitución XMI directa falla sobre un perfil conocido; A05 backend completo no ofrece memoria de equipo y traslada incompatibilidades. DESCARTAR no autoriza borrar archivos o dependencias existentes.

### Requisitos obligatorios que necesitan DESARROLLO NUEVO

F16 preguntas/respuestas grupales, actor real y destinatario individualizado; F17 contexto grupal/individual, seguimiento y distinción por participante; F18 conservación/recuperación de diálogo; F20 política/flujo de moderación y asesoría contextual de equipo. Reutilizan identidad, pertenencia, chat, Django/Channels/Angular, pero **no existe una implementación donante de esas capacidades**. F17/F20 siguen NE en total, con prioridad P0. F19 aprovecha un modo conceptual parcial; su exactitud requiere evaluación posterior, sin confundirla con el flujo nuevo de moderación.

### Riesgos que requieren validación antes de implementar

Autorización y revocación de lectura/escritura, revisión única de todos los escritores, no rebase silencioso de plan tras proveedor, persistencia de validated_data, deduplicación por nivel, perfil XMI y rechazo de vacío, acceso/orden/contexto por actor en conversación, compilación Java y entorno destino real. R3/S3/X3 conservan los límites de evidencia de H/I; no son incidentes de producción declarados.

Las alternativas técnicamente más congruentes son conservar la base NB, adaptar límites donantes probados y construir lo ausente en el mismo asistente. No se decide un ranking definitivo, un calendario, esquema de tablas, nuevas rutas ni plan final de migración. Se han registrado dependencias y prioridades preliminares para permitir esa decisión en otra ejecución autorizada.

**FASE 4 DE TRABAJO FINALIZADA. Detenerse tras entregar el informe; no implementar, corregir, migrar ni continuar sin autorización expresa.**

### Verificación final

El bloque siguiente se obtiene durante la creación exclusiva del entregable, contrastando los 1888 archivos de línea base, ramas/commits y Git antes y después. Se conserva el estado preexistente y los informes anteriores; no se limpia ni revierte Git.


~~~text
D:\Informatica\8vo Semestre\sw1-2-2026\pizarra-colaborativa
Rama: feat/integrar-diagramcraft; HEAD: df5430d221ddfbdc23e0a7882e535dc402ceafc4
 M frontend/package-lock.json
?? AUDITORIA_FASE_1.md
?? AUDITORIA_FASE_2.md
?? AUDITORIA_FASE_3.md
?? AUDITORIA_FASE_4.md
?? AUDITORIA_MAESTRA.md
?? auditoria-diagramcraft-nodoboard.code-workspace
?? debug.log
D:\swProyecto\backend
Rama: main; HEAD: 125dc3b72fed6a829299d5733f31277d0c789a1c
(limpio)
D:\swProyecto\frontend
Rama: main; HEAD: e200fc82b2fa6cb3b79e62b5411a6942ccd0cc7a
(limpio)
~~~

SHA-256 de 1888 archivos existentes: 0 diferencias. Ramas, commits, origins y cambios Git previos conservados: True. Único archivo nuevo autorizado: True.

Maestro y fases 1, 2 y 3 incluidos en el inventario y preservados byte por byte; frontend/package-lock.json conserva su modificación previa. No se revirtió ningún cambio ni se ejecutaron nuevas pruebas funcionales. Se comprobaron 32 funcionalidades, 6 alternativas y las 38 filas aritméticas renderizadas; cobertura de R1–R20 y estructura A–O verificadas.

Alcance de integridad: archivos rastreados y no ignorados inventariados; no se afirma hash de todos los ignorados del entorno. Temporales y generación del informe permanecen en T4. Esta comprobación no sustituye las limitaciones funcionales documentadas.
