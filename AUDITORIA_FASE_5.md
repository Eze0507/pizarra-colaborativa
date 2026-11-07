# Auditoría — Fase 5 de trabajo: consolidación final y plan de implementación de NodoBoard

Referencia de auditorías: 30 de octubre de 2026. Cierre con contexto actualizado del cliente: 31 de octubre de 2026, America/La_Paz. **Entrega exclusivamente documental. Toda tarea, modelo, ruta o componente futuro se propone para una implementación posterior autorizada; no está creado ni implementado por este informe.**

## A. Resumen ejecutivo

**Conservar NodoBoard Angular + Django, su editor JointJS, identidad JWT y dominio ORM. Ampliar un único asistente Angular mediante servicios Django autoritativos; adaptar capacidades concretas de DiagramCraft y desarrollar el sistema de conversación que ninguno implementa.** No incorporar Diana íntegra, React, Zustand, autenticación de sesión paralela o CRUD UML heredado.

El recuento se obtuvo directamente de AUDITORIA_FASE_4.md, no de mensajes anteriores ni de su JSON temporal: 32 funcionalidades, 6 alternativas materiales de contraste, 26 funcionalidades con total y 6 NO EVALUABLES (F08, F09, F17, F20, F23, F29). DESARROLLO NUEVO: F16, F17, F18, F20. Las puntuaciones, prioridades, esfuerzo, riesgo y confianza se mantienen sin cambios. Las diferencias entre archivos de informes son las adiciones autorizadas de fases previas; los inventarios anteriores permanecen idénticos. No hubo nueva evidencia funcional para recalificar.

El núcleo obligatorio documentado en el maestro requiere nuevos mensajes compartidos atribuidos (F16), memoria grupal/individual (F17), historial recuperable (F18) y moderación/asesoría contextual (F20). F17 y F20 conservan total NO EVALUABLE y prioridad P0: se incorporan tareas de definición y verificación antes de aceptar su resultado. Las incertidumbres opcionales F08/F09/F23/F29 no bloquean el núcleo.

La secuencia recomendada protege primero identidad, permisos, escritura única/revisión y recuperación; después incorpora mensajes/historial, contexto/asesoría de sólo lectura, y finalmente planes confirmables e idempotencia. Cada entrega lleva pruebas. La generación Spring, UML ampliado, XMI avanzado, voz/TTS, lifecycle, locks/undo y modelo local no deben desplazar las brechas académicas documentadas.

**Procedencia académica:** no se localizó en los repositorios una transcripción, audio o enunciado original independiente del docente. El maestro§11 formaliza el enunciado y sus requisitos; se identifican como INTERPRETACIÓN DEL DOCUMENTO MAESTRO, sin atribuirlos textualmente al docente. La procedencia primaria sigue NO VERIFICADA. Las garantías de autorización/revisión/dedupe/secretos se distinguen como recomendaciones técnicas y condiciones del proyecto. El modelo local permanece OPCIONAL por maestro y orden expresa de esta fase; no se promete calificación.

El plan ofrece 12 tareas backend, 10 frontend y 31 escenarios propuestos, de los cuales los cuatro últimos amplían las pruebas técnicas/opcionales solicitadas. Son unidades de planificación, no conteo de nuevas funcionalidades ni trabajo ejecutado. La implementación y cualquier modificación de datos, ramas, dependencias o despliegue requieren autorización posterior.

## B. Consolidación de las cuatro auditorías

### Alcance y correspondencia

Las ejecuciones1/2/3/4 trataron auditoría integral, asistentes, comparación backend+frontend y evaluación cuantitativa. Esta ejecución5 consolida maestro§11 (cobertura académica), §12 (ranking), §13 (selección) y §14 (plan/informe final), reutilizando §7–10 (matriz/pesos/prioridades/esfuerzo/riesgo). No crea otra fase ni repite suites de aplicación.

Se consultaron íntegramente AUDITORIA_MAESTRA.md y las fases1–4. El contenido ya leído en las ejecuciones previas se mantuvo vigente por hash, y se leyó el texto completo de los cinco archivos para extracción/consolidación. Se aplicó como guía la skill diagramcraft-ai-uml-platform ya leída; el contrato escrito de una skill no demuestra implementación. No se delegó trabajo ni se utilizaron servicios externos.

### Identidad y estado

| Alias | Ruta real | Origin | Rama inicial | Commit inicial |
|---|---|---|---|---|
| NB | D:\Informatica\8vo Semestre\sw1-2-2026\pizarra-colaborativa | https://github.com/Eze0507/pizarra-colaborativa.git | feat/integrar-diagramcraft | df5430d221ddfbdc23e0a7882e535dc402ceafc4 |
| DB | D:\swProyecto\backend | https://github.com/juanse8202/swbackend.git | main | 125dc3b72fed6a829299d5733f31277d0c789a1c |
| DF | D:\swProyecto\frontend | https://github.com/juanse8202/swfrontend.git | main | e200fc82b2fa6cb3b79e62b5411a6942ccd0cc7a |

Rutas/raíz Git/origin se verificaron; toda referencia relativa en tareas backend/frontend parte de NB salvo indicación DB/DF. AUDITORIA_FASE_5.md no existía. Estado inicial NB:

~~~text
 M frontend/package-lock.json
?? AUDITORIA_FASE_1.md
?? AUDITORIA_FASE_2.md
?? AUDITORIA_FASE_3.md
?? AUDITORIA_FASE_4.md
?? AUDITORIA_MAESTRA.md
?? auditoria-diagramcraft-nodoboard.code-workspace
?? debug.log
~~~

DB/DF limpios. Git se leyó con -c safe.directory por proceso y --no-optional-locks, sin config persistente. No se encontraron AGENTS.md mediante búsqueda en las tres raíces con archivos ocultos incluidos/exclusión de dependencias. No se crearon ramas/PR/commits ni se revirtió el lockfile.

| Documento consultado | Bytes/líneas | SHA-256 |
|---|---|---|
| AUDITORIA_MAESTRA.md | 29803/887 | e31d7c76755987a6542d033720f65276d3dbe1db5ff8026eb8405498d9deca41 |
| AUDITORIA_FASE_1.md | 43325/322 | 9f696d650923ca4b27da9c0d4a4b4215f9b8bda85783f702f6c631326f6d180c |
| AUDITORIA_FASE_2.md | 73304/407 | 0c229547359d479c290ba3c51bac714c854feec788e1152de6b4e97839405d0a |
| AUDITORIA_FASE_3.md | 98399/614 | 3d6c99f155e4120c8675a6af1f79160f4a0f9a2ca7e83826e62acc38be511325 |
| AUDITORIA_FASE_4.md | 131889/1181 | 5841c0a1ffbc38b529b4a75302d6b0ce80b5380627cbdf05e26857f8ff145a95 |

### Recuento verificable de fase 4

Se extrajeron las filas F de C/D/E/F/G/L y las filas A de J; se contrastaron IDs, notas/contribuciones, decisiones, prioridades, esfuerzo y riesgo. La suma usa los pesos25/20/15/15/10/10/5 y la fórmula g/5×peso, sin cambiar notas ni normalizar NE.

| Recuento | Valor real | Contraste |
|---|---|---|
| Funcionalidades únicas | 32 | C y L; IDs únicos idénticos a D/E/F/G |
| Alternativas de contraste | 6 | J; no se suman al inventario funcional |
| Con total numérico | 26 | D y L; suma ponderada exacta contrastada |
| NO EVALUABLES | 6 | F08, F09, F17, F20, F23, F29 |
| DESARROLLO NUEVO | 4 | F16, F17, F18, F20 |
| Decisión CONSERVAR | 4 | Misma clasificación en C/L |
| Decisión ADAPTAR | 13 | Misma clasificación en C/L |
| Decisión INVESTIGAR | 4 | Misma clasificación en C/L |
| Decisión FUSIONAR | 5 | Misma clasificación en C/L |
| Decisión DESARROLLO NUEVO | 4 | Misma clasificación en C/L |
| Decisión MIGRAR | 1 | Misma clasificación en C/L |
| Decisión DESCARTAR | 1 | Misma clasificación en C/L |
| Prioridad P0 | 16 | Misma clasificación en E/L |
| Prioridad P2 | 10 | Misma clasificación en E/L |
| Prioridad P1 | 4 | Misma clasificación en E/L |
| Prioridad P3 | 2 | Misma clasificación en E/L |

No se encontraron inconsistencias entre esos recuentos y el resumen de fase4. El primer parser temporal comparó la celda exactamente con NO EVALUABLE y falló al encontrar el sufijo “(estimación nueva)”; se corrigió sólo el parser a detectar el prefijo. No fue inconsistencia del informe ni cambio de puntuación.

### Evidencia consolidada y límites

| Fase | Evidencia vigente que condiciona la decisión | Límite preservado |
|---|---|---|
| 1 | Editor/proyectos/ORM/JWT/XML conectados NB; tres tests propios+cinco probes8pasan; XMLfixture9/33/10; tsc pasa. H-N01/H-N02/H-N03: PATCH visualizador, rutina snapshot sin revalidación y eliminación por snapshot anterior | URLconf parcial y Django6.1 en vez de5.2; sin handshake ofensivo ni PG real; conservar no valida fallos |
| 1 | DB 85 tests:69 éxitos,1 fallo,15 errores; diagramas59 y config 6 pasan; DC retry409 tras éxito y movimiento legacy a diagrama ajeno; DF 28 Node/lint/build pasan | SQLjsonb_array_length no funciona en SQLite; test antiguo sin expected_revision; no E2E/navegador/proveedor |
| 2 | Mantener un asistente NB; adaptar operaciones/planes/frontera. Siete probes NB con fake: acepta delta string, omite historia/actor/multiplicidad; un probe DC reproduce rebase revisión durante proveedor | Fake no acredita inteligencia. PlanIA no es historial conversacional; ambas apps carecen de memoria grupal/individual |
| 3 | NB ORM+snapshot frente a documento JSON DC; X3 parser9→0 sin errors; R3 dos heurísticas Angular; S3 handler sin close y update posterior; invitación/enlace sin ruta; cinco archivos React vacíos | X3 no ejecutó reemplazo/borrado; R3 no guardó navegador; S3 no explotación de red. XMI/Java/audio reales pendientes |
| 4 | Notas y decisiones por 32 funciones/6 alternativas; cuatro DESARROLLO NUEVO, seis NE. Q de F16/F18 sólo bases reutilizables; F17/F20 sin garantía puntuable | Conveniencia no equivale a cumplimiento ni a prioridad; riesgos no se compensan con puntos |

Identificadores H-N01/02/03/05/06, H-D02/03/04/05, H2-D01 y X3/R3/S3/I3 conservan el significado de los informes originales. Las referencias E01–E26 de fase4 se mantienen en matrices de este informe y remiten a sus rutas/funciones/pruebas; no se inventa una nueva ejecución.

Contradicciones resueltas sin editar originales: archivos React vacíos no son módulos activos; pruebas internas XMI no certifican el perfil NB; configuración de proveedor no exige múltiples marcas; contexto de diagrama no equivale a memoria; OK en sonda de defecto no indica control seguro. Procedencia primaria del docente no disponible impide confrontar audio con formalización: eso es una limitación, no una contradicción demostrada.

## C. Ranking definitivo

Ranking de **las alternativas numéricamente evaluadas**, con decisiones y cifras intactas de fase4. Los seis NE permanecen individualmente en D, no como cero ni al final de una falsa clasificación numérica. Los obligatorios F17/F20 se intercalan como gates de desarrollo en M después de historia/contexto y antes de cerrar asesoría; no desaparecen por carecer de puesto numérico.

El orden respeta bases/dependencias y seguridad antes que score. F04/F01 se conservan, no se reimplementan. Los controles mínimos de pruebas/errores acompañan todos los puestos aunque la ampliación transversal F27/F26 aparezca después. F21/F28 se mantienen operativos desde el baseline; su puesto se refiere a atención adicional, nunca a retirar funcionalidades. F30 se excluye desde el comienzo: su posición no implica programar su migración al final.

| Ranking | Funcionalidad | Decisión | Puntuación /100 | Prioridad | Esfuerzo /5 | Riesgo /5 | Confianza | Justificación |
|---|---|---|---|---|---|---|---|---|
| 1 | F04 Autenticación JWT, proyectos e invitaciones base | CONSERVAR | 73.0 | P0 | 1 | 3 | ALTA | Identidad y pertenencia son base ya existente de todos los accesos; conservar antes de ampliar. Evidencia: E02,E04 |
| 2 | F01 Editor base: entidades/clases relacionales, atributos y operaciones visuales | CONSERVAR | 66.0 | P0 | 1 | 3 | ALTA | Preservar modelo y editor actuales es prerrequisito de validar/cambiar el agregado; no rehacerlo. Evidencia: E01,E02 |
| 3 | F05 Autorización uniforme y revocación REST/WS | ADAPTAR | 76.0 | P0 | 4 | 5 | ALTA | Permisos/revocación son gate crítico de seguridad antes de nuevos escritores o mensajes. Evidencia: E04,E05,E06 |
| 4 | F03 Validación determinista del dominio, tipos y multiplicidades | ADAPTAR | 74.0 | P0 | 4 | 4 | ALTA | Reglas deterministas antes de versionar/aplicar lotes; menor nota no reduce su carácter de prerrequisito. Evidencia: E01,E03,E07,E14 |
| 5 | F06 Revisión, reconciliación y guardado autoritativo | ADAPTAR | 79.0 | P0 | 5 | 5 | ALTA | Revisión y autoridad comunes después de permisos/reglas; corrige pérdida secuencial y condiciona colaboración. Evidencia: E05,E07,E08 |
| 6 | F07 Conectividad colaborativa: presencia, reconexión y resync | ADAPTAR | 78.0 | P0 | 4 | 4 | MEDIA | Resync y presencia seguros sobre revisión; habilita sesiones compartidas y mensajes posteriores. Evidencia: E06,E08,E09 |
| 7 | F32 Proveedor IA configurable y adaptador único en backend | FUSIONAR | 74.0 | P0 | 3 | 3 | ALTA | Mantener configuración y aislar proveedor antes de orquestar conversación; no exige multimarcas. Evidencia: E07,E11,E24,R19 |
| 8 | F13 Contexto autoritativo del diagrama y selección | FUSIONAR | 77.0 | P0 | 3 | 4 | ALTA | Contexto autorizado coherente con revisión antes de asesoría/órdenes; no es memoria conversacional. Evidencia: E07,E11 |
| 9 | F16 Chat grupal: preguntas/respuestas compartidas, actor y destinatario | DESARROLLO NUEVO | 78.0 | P0 | 5 | 5 | MEDIA | Nueva conversación grupal atribuida sobre identidad/permisos/resync; requisito no ofrecido por Diana. Evidencia: E04,E06,E15,R2-R7 |
| 10 | F18 Persistencia y recuperación autorizada del historial IA | DESARROLLO NUEVO | 80.0 | P0 | 4 | 4 | MEDIA | Historial requiere identidad/contrato de mensajes F16; aunque puntúe80 no puede precederlo. Evidencia: E04,E15,R18 |
| 11 | F19 Consulta conceptual de sólo lectura separada de mutación | FUSIONAR | 79.0 | P0 | 3 | 4 | MEDIA | Consulta sin escritura y respuesta dirigida sobre chat/contexto; F17/F20 se resuelven en gates separados. Evidencia: E07,E11,E16,R12 |
| 12 | F10 Lenguaje natural a operaciones estructuradas del modelador | ADAPTAR | 77.0 | P0 | 4 | 4 | MEDIA | Operaciones estructuradas tras contexto/proveedor/reglas; no activar ejecución sólo por transporte200. Evidencia: E03,E07,E11 |
| 13 | F11 Plan IA persistido, preview y confirmación autorizada | ADAPTAR | 79.0 | P0 | 5 | 5 | MEDIA | Plan y confirmación dependen del ejecutor y misma base de revisión; F2 impide copiar rebase del donante. Evidencia: E07,E11,E12 |
| 14 | F12 Dedupe, retry e identidad de solicitud/aplicación | ADAPTAR | 67.0 | P0 | 4 | 4 | ALTA | Idempotencia de aplicación una vez definido el plan; sus67puntos/P0 preceden mejoras opcionales mejor puntuadas. Evidencia: E07,E12 |
| 15 | F27 Contratos, separación de responsabilidades y pruebas de frontera | ADAPTAR | 72.0 | P1 | 4 | 4 | MEDIA | Ampliación transversal de contratos/tests; controles mínimos ya acompañan cada gate anterior. Evidencia: E01,E08,E11,E22 |
| 16 | F26 Errores estructurados, foco y accesibilidad básica | FUSIONAR | 70.0 | P1 | 3 | 3 | MEDIA | UX de errores/accesibilidad complementa contratos; avisos básicos y confirmación ya son parte del núcleo. Evidencia: E08,E16,E21 |
| 17 | F31 Completar enlace de invitación firmado sin reemplazar invitaciones | ADAPTAR | 70.0 | P1 | 2 | 3 | ALTA | Completar enlace propio; aceptación interna evita que esta mejora bloquee todo el chat. Evidencia: E02,E26 |
| 18 | F21 XMI actual de NodoBoard: conservar entrada/salida | CONSERVAR | 57.0 | P2 | 1 | 3 | ALTA | Conservar XMI existente es dependencia de fusionar perfiles; posición no autoriza retirar su función actual. Evidencia: E14,E17 |
| 19 | F22 XMI: perfiles compatibles, límites seguros y preview versionado | FUSIONAR | 54.0 | P1 | 4 | 5 | MEDIA | Preview/límites requieren F21 y resolver X3; P1 no salta ese prerrequisito P2 de conservación. Evidencia: E14,E17,E18 |
| 20 | F25 Ciclo de proyectos: archivar/restaurar/duplicar y roles extendidos | ADAPTAR | 51.0 | P2 | 4 | 3 | MEDIA | Lifecycle adicional después del núcleo seguro; no requisito textual de conversación. Evidencia: E02,E04,E20 |
| 21 | F14 Voz: conservar push-to-talk y adaptar transcripción final | ADAPTAR | 55.0 | P2 | 3 | 3 | MEDIA | Mejorar transcripción manteniendo push-to-talk; confirmación por voz depende del plan existente. Evidencia: E13 |
| 22 | F15 Síntesis de voz opcional | ADAPTAR | 54.0 | P2 | 2 | 3 | MEDIA | TTS opcional tras coordinar escucha/voz; no desplaza texto ni memoria obligatoria. Evidencia: E13 |
| 23 | F02 UML ampliado: kinds, métodos, realización/dependencia y ownership | ADAPTAR | 51.0 | P2 | 4 | 4 | MEDIA | UML avanzado requiere reglas/revisión y diseño de tipos; fuera del mínimo conversacional. Evidencia: E01,E03 |
| 24 | F24 Exportación Spring Boot por capas y validación del artefacto | MIGRAR | 50.0 | P2 | 5 | 4 | MEDIA | Exportador Spring depende de semántica F02/F03 y compilación; no sustituye Django. Evidencia: E03,E19 |
| 25 | F28 Entrada por imagen de NodoBoard | CONSERVAR | 46.0 | P2 | 1 | 3 | MEDIA | Preservar imagen sin ampliar su alcance; salida real pendiente y su escritura debe usar el límite común. Evidencia: E07,E23 |
| 26 | F30 Incorporación integral de Diana/React/auth/ORM legacy | DESCARTAR | 19.0 | P3 | 5 | 5 | ALTA | Descartar traslado integral/duplicación desde el inicio; última posición es decisión de exclusión, no tarea final. Evidencia: E02,E06,E15,E25 |

F18 (80) no puede preceder el contrato de mensajesF16 (78); F03 (74) y F05 (76) habilitan F06 (79); F12 (67)/P0 precede ampliaciones P1 mejor puntuadas; F21 (57)/conservar es base de F22 (54)/fusionar. F17/F20 siguen P0 sin total. No se recalcula una suma global de beneficios compartidos, ni se usa el score como nota del examen.

## D. Tratamiento de funcionalidades NO EVALUABLES

El conjunto se obtuvo por lectura de las celdas de total en fase4L y se contrastó con D; su tamaño real es 6. Cada caso distingue necesidad, evidencia faltante y efecto bloqueante. La decisión de construir la capacidad obligatoria no constituye evaluación positiva del algoritmo aún no existente.

### F08 — Bloqueo fuerte por elemento con lease

| Campo | Conclusión |
|---|---|
| Necesidad/obligatoriedad | Exclusión fuerte por elemento/lease; opcional. |
| Motivo NO EVALUABLE | No hay contrato de dueño/timeout ni prueba de lease fuerte; beneficio frente a revisión no medido. |
| Evidencia disponible | Avisos/set por conexión NB; donante no demuestra lease fuerte. Referencias E05,E09 |
| Evidencia faltante | Política de bloqueo, alcance, caducidad y recuperación multiworker. |
| Impacto académico | No bloquea requisitos de chat si revisión rechaza conflictos. |
| Qué bloquea y qué no | No bloquear núcleo; bloquea sólo prometer bloqueo fuerte. |
| Verificación propuesta | V08: decidir necesidad y probar expiración, dueño, pestañas, liberación y caídas en aislamiento. |
| Dependencias | B01,B02,B03; política UX futura. |
| Decisión provisional | INVESTIGAR; no sustituir revisión por avisos visuales. |
| Cifras fase4 conservadas | Total NO EVALUABLE; P2; esfuerzo NE/5; riesgo 4/5; confianza BAJA |

### F09 — Undo/redo colaborativo seguro

| Campo | Conclusión |
|---|---|
| Necesidad/obligatoriedad | Undo/redo seguro con colaboradores; opcional. |
| Motivo NO EVALUABLE | Historial local50 snapshots no prueba inversas válidas ante edición remota. |
| Evidencia disponible | diagramStore.undo/redo/restore y Canvas autosave; no garantía multiusuario. Referencias E10 |
| Evidencia faltante | Alcance local/remoto, operación inversa y política de conflicto. |
| Impacto académico | No exigencia textual en maestro; preservar edición normal. |
| Qué bloquea y qué no | Sólo bloquea incorporar undo como seguro; no chat. |
| Verificación propuesta | V09: dos actores, edición posterior ajena y undo; debe preservar trabajo remoto o rechazar conflicto explícito. |
| Dependencias | B02/B03 y modelo de operaciones B08 si se define inversa. |
| Decisión provisional | INVESTIGAR; no migrar snapshots React a ORM como undo colaborativo. |
| Cifras fase4 conservadas | Total NO EVALUABLE; P2; esfuerzo NE/5; riesgo 4/5; confianza BAJA |

### F17 — Memoria grupal/individual y continuidad de seguimientos

| Campo | Conclusión |
|---|---|
| Necesidad/obligatoriedad | Contexto grupal/individual, seguimiento y distinción por actor; obligatorio según maestro. |
| Motivo NO EVALUABLE | Q NE: no recuperador/context builder equivalente ni pruebas de memoria por actor. |
| Evidencia disponible | Historial local, resumen de diagrama y autenticación; ausencia de historia en request probada. Referencias E15,E16,R8-R11 |
| Evidencia faltante | Política de recuperación/límites, fuentes, causalidad de consultas simultáneas y evaluación semántica. |
| Impacto académico | AC10–AC13 no pueden cerrarse sin demostrar continuidad. |
| Qué bloquea y qué no | Bloquea aceptación de memoria/segundo parcial documentado; no impide permisos/chat/historial previos. |
| Verificación propuesta | V17 en B06: corpus con tres actores, acuerdos grupales y hechos por actor; reconstruir contexto recuperable y probar recarga/seguimientos largos. |
| Dependencias | B04 historial, B01 acceso, B02 revisión, B05 proveedor; U02/U04. |
| Decisión provisional | DESARROLLO NUEVO/P0; conservar NE hasta evidencia, gate antes de moderación completa. |
| Cifras fase4 conservadas | Total NO EVALUABLE; P0; esfuerzo 5/5; riesgo 5/5; confianza MEDIA |

### F20 — IA moderadora/asesora contextual del equipo y recomendaciones

| Campo | Conclusión |
|---|---|
| Necesidad/obligatoriedad | Moderación/asesoría contextual del equipo y recomendaciones; obligatorio formalizado. |
| Motivo NO EVALUABLE | Q NE: no política/corpus ni resultados de moderación equivalente. |
| Evidencia disponible | Intención conceptual NB y operaciones DC; no flujo asesor de equipo verificado. Referencias E15,E16,R13-R14 |
| Evidencia faltante | Definición de moderar, rúbrica humana, contexto/actor y respuestas reales autorizadas o corpus registrado válido. |
| Impacto académico | AC15/AC16 y propósito moderador siguen sin cumplir. |
| Qué bloquea y qué no | Bloquea declarar asesoría/aceptación completa; no bloquea transporte y seguridad. |
| Verificación propuesta | V20 en B07: acordar rúbrica y corpus, evaluar atribución, consejo UML justificado, incertidumbre y cero mutación; fake sólo valida flujo. |
| Dependencias | V17/B06, B04/B05, U02/U04 y consulta de sólo lectura. |
| Decisión provisional | DESARROLLO NUEVO/P0; política mínima propuesta, exactitud aún NE y sin puntos inventados. |
| Cifras fase4 conservadas | Total NO EVALUABLE; P0; esfuerzo 5/5; riesgo 4/5; confianza BAJA |

### F23 — Interoperabilidad semántica/visual certificada con EA

| Campo | Conclusión |
|---|---|
| Necesidad/obligatoriedad | Interoperabilidad semántica/visual con EA; opcional para enunciado disponible. |
| Motivo NO EVALUABLE | Sin versión/perfil de herramienta objetivo ni vuelta manual EA. |
| Evidencia disponible | NB conteos9/33/10, pruebas internas DC y X3 concreto. Referencias E14,E17 |
| Evidencia faltante | EA objetivo, perfil, semántica/layout requeridos y aceptación de pérdidas. |
| Impacto académico | No bloquea conversación; no prometer certificación EA. |
| Qué bloquea y qué no | Bloquea certificación/integración opcional de perfiles no acreditados. |
| Verificación propuesta | V23: acordar perfiles, fixtures cruzadas y vuelta manual EA; clases/relaciones/multiplicidades/whole/layout. |
| Dependencias | B09/U07 y gate X3; herramienta aislada disponible futura. |
| Decisión provisional | INVESTIGAR; conservar XMI NB y no sustituirlo automáticamente. |
| Cifras fase4 conservadas | Total NO EVALUABLE; P2; esfuerzo NE/5; riesgo 4/5; confianza BAJA |

### F29 — Proveedor alternativo/LLM local opcional

| Campo | Conclusión |
|---|---|
| Necesidad/obligatoriedad | Otro proveedor/LLM local; extensión opcional. |
| Motivo NO EVALUABLE | Motor/hardware/modelo/operación y beneficios no definidos; parser local no es LLM. |
| Evidencia disponible | Gemini configurable y factory del donante; sin adaptador local. Referencias E07,E11,E24,R20 |
| Evidencia faltante | Motor/modelo autorizado, recursos, corpus/calidad y operación; no instalar ahora. |
| Impacto académico | No bloquea AC22 ni el núcleo; AC23 permanece OPCIONAL. |
| Qué bloquea y qué no | Sólo bloquea decidir integración local; no todo el plan. |
| Verificación propuesta | V29: comparar en corpus con política de datos autorizada y recursos conocidos; no alterar proveedor actual por defecto. |
| Dependencias | B05 interfaz única y validación de salida B07/B08. |
| Decisión provisional | INVESTIGAR/P3; ninguna puntuación y ninguna obligación local nueva. |
| Cifras fase4 conservadas | Total NO EVALUABLE; P3; esfuerzo NE/5; riesgo 4/5; confianza BAJA |

V17 y V20 son tareas explícitas de verificación/diseño vinculadas a B06/B07, con entregables de corpus/rúbrica/contexto y pruebas semánticas. V08/V09/V23/V29 son investigaciones opcionales, sin instalación ni implementación autorizada ahora. Un riesgo de explotación aún no probado no se usa para completar Q con un número. Tras nueva evidencia se actualizaría una evaluación posterior autorizada, no las notas de fase4 en este informe.

## E. Matriz de requisitos académicos

### Procedencia y obligatoriedad reales de las fuentes disponibles

La búsqueda local de archivos con nombre de parcial/docente/transcripción, audio(.mp3/.wav), PDF/DOCX y menciones en Markdown/TXT fuera de auditorías no localizó una fuente académica primaria independiente en las tres raíces. No se amplió a cuentas externas, internet ni archivos privados. El maestro§11 contiene un enunciado formalizado y una atribución secundaria sobre el modelo local. La instrucción actual también ordena mantenerlo opcional.

Por tanto:

- **EXPLÍCITO DEL DOCENTE:** no hay requisito que pueda atribuirse textualmente con una fuente primaria verificada en esta ejecución. Esto no significa que el docente no lo pidiera.
- **INTERPRETACIÓN DEL DOCUMENTO MAESTRO:** procedencia documental verificable para las capacidades formalizadas. Se tratan como alcance obligatorio documentado por el usuario/maestro, manteniendo NO VERIFICADA la atribución primaria.
- **RECOMENDACIÓN TÉCNICA:** revisión, dedupe, colas, permisos uniformes, secreto backend, UX y otras garantías necesarias/elegidas por diseño; no se presentan como citas del docente.
- Si aparece una fuente posterior, V00 exige contrastarla y registrar diferencias antes de declarar cobertura académica definitiva. Sin esa fuente no se promete calificación ni se rebaja silenciosamente el alcance formalizado.

Los 23 elementos siguientes desagregan los 20 R del maestro: por ejemplo, sesiones/dispositivos/tablero y sincronización se separan; no son 23 nuevas funcionalidades puntuadas. “Obligatorio documentado” significa según maestro, no “EXPLÍCITO DEL DOCENTE”. Ningún requisito se declara cumplido por estar en el plan.

| ID/descripción | Procedencia | Obligatoriedad | NB actual | Aporte DC | Evidencia | Cumplimiento actual | Función/tareas | Prioridad | Dependencias | Criterio de aceptación futuro |
|---|---|---|---|---|---|---|---|---|---|---|
| AC01 Sesión independiente por integrante | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/párrafo y R1 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | JWT/token propio; parcial | Sesión propia; parcial | F4 C/R1; E04/E09 | PARCIALMENTE CUMPLIDO | F04,F05,F07; B00,B01,B03 / U00,U01; PX01,PX02 | P0 | Identidad/pertenencia vigentes | Tres sesiones distintas conservan actor y permisos correctos sin compartir tokens. |
| AC02 Dispositivos/ubicaciones distintas | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R1 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | Canales/URLs conectados; E2E pendiente | Hook/Channels, E2E pendiente | E04/E09 | PARCIALMENTE CUMPLIDO | F04,F07; B00,B03 / U00,U01; PX01,PX20 | P0 | Infra aislada, URL/transporte de prueba | Tres clientes en sesiones separadas se reconectan al mismo proyecto; no se presume prueba geográfica real. |
| AC03 Un mismo tablero compartido | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/párrafo inicial | Obligatorio documentado; atribución textual al docente NO VERIFICADA | Eventos/snapshot/ORM; defectos de revisión | JSON/revisión; no reemplazo de dominio | E01/E05/E08 | PARCIALMENTE CUMPLIDO | F01,F06,F07; B02,B03 / U00,U01; PX02,PX03,PX23 | P0 | B01/B02 | Estado normalizado y revisión iguales tras cambios/reconexión; preservar editor NB. |
| AC04 Sincroniza cambios autorizados | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R16-R17 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | Parcial y permisos/snapshot defectuosos | Publicación autoritativa y revisión parciales | E05/E08/E12 | PARCIALMENTE CUMPLIDO | F05,F06,F07,F12; B01,B02,B03,B08 / U01,U03; PX15,PX16,PX17,PX23 | P0 | Writer común y permisos | Sólo cambio confirmado/permitido persiste y todos convergen a su revisión; ningún evento antes de commit. |
| AC05 Todo integrante del proyecto puede consultar IA | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R3 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | Entrada autenticada local; sin canal grupal completo | EDIT_ROLES excluye reader en interpretación | E07/E11/E15 | PARCIALMENTE CUMPLIDO | F16,F19; B01,B04,B07 / U02,U04; PX04,PX12,PX17 | P0 | Preguntar separado de editar | Propietario/editor/visualizador activos pueden consultar; visualizador no modifica. |
| AC06 Pregunta visible para todos los miembros | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R2,R4 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | Sólo mensajesChat local | Sólo aiHistory local | E15 | NO CUMPLIDO | F16; B03,B04,B07 / U02; PX04,PX05 | P0 | Identidad/mensaje persistido | Los tres ven el mismo message_id/actor/texto en orden, sin duplicado tras replay. |
| AC07 Respuesta visible para todo el proyecto | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R5 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | Respuesta local | Respuesta/plan local; WS de documento no es chat | E15/E16 | NO CUMPLIDO | F16,F18; B03,B04,B07 / U02; PX06,PX18 | P0 | Pregunta/reply_to y acceso | Una respuesta canónica vinculada a pregunta aparece en todos y en historial. |
| AC08 Identifica quién pregunta | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R6 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | Autenticación sin actor al proveedor | PlanIA.usuario no es atribución de diálogo | E04/E07/E15 | PARCIALMENTE CUMPLIDO | F16; B01,B04,B06,B07 / U02; PX07,PX25,PX27 | P0 | request.user, nunca actor libre | Actor del mensaje y del contexto deriva de sesión; falsificar actor_id no lo cambia. |
| AC09 Dirige respuesta al participante correcto | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R7 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | Sin flujo atribuido conectado | Sin flujo conversacional atribuido | E15/E16 | NO CUMPLIDO | F16,F20; B04,B06,B07 / U02,U04; PX08,PX19 | P0 | reply_to/recipient autorizados | Respuesta identifica al autor de la pregunta incluso con dos peticiones simultáneas. |
| AC10 Contexto conversacional grupal | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R8 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | Sólo contexto del diagrama | Resumen del documento, no diálogo | E15/E16 | NO CUMPLIDO | F17; B04,B06,B07 / U02,U04; PX09,PX19,PX21 | P0 | V17 y registro persistido | Seguimiento usa acuerdos anteriores de ese proyecto con referencias de origen y sin mezclar otro. |
| AC11 Contexto individual por participante | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R9 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | No memoria por actor | No memoria por actor | E15/E16 | NO CUMPLIDO | F17; B04,B06,B07 / U02,U04; PX10,PX11 | P0 | V17, actor servidor | Recupera hechos del actor correcto dentro de conversación compartida, también tras recarga. |
| AC12 Comprende preguntas de seguimiento | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R10 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | No historia enviada; semántica no probada | Igual limitación | E16; V17 | NO VERIFICADO | F17,F20; B06,B07 / U02,U04; PX09,PX10,PX11 | P0 | Historial + evaluación de contenido | Corpus de seguimientos pasa rúbrica acordada; un fake no acredita comprensión real. |
| AC13 Diferencia intervenciones de distintos participantes | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R11 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | Sin hilo/actor contextual | Historial local no equivale a turnos por actor | E15/E16 | NO CUMPLIDO | F16,F17; B04,B06,B07 / U02,U04; PX07,PX10,PX19 | P0 | Actor y causalidad por request | No asigna a B un dato/acuerdo personal de A; turno y respuesta conservan destinatario. |
| AC14 Responde dudas conceptuales sin cambiar diagrama | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R12; cero mutación es control técnico | Obligatorio documentado; atribución textual al docente NO VERIFICADA | Prompt + transporte fake sin delta, calidad no probada | Sin answer explícito | E07/E11/E16 | PARCIALMENTE CUMPLIDO | F19; B07 / U02,U04; PX12,PX26 | P0 | Consulta separada de aplicar | Consulta produce answer y ningún cambio de revisión/ORM; contenido pasa rúbrica, no sólo HTTP200. |
| AC15 Asesora en diseño UML y modera al equipo | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/propósito y R13 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | Intención conceptual; sin moderación de equipo | Planes no son asesoría contextual | E16; V20 | NO VERIFICADO | F20; B06,B07 / U04; PX09,PX12,PX26 | P0 | V17/V20, contexto y política | Distingue hechos/acuerdos de sugerencias, pide aclaración y fundamenta consejo en el modelo/contexto. |
| AC16 Recomienda mejoras del diagrama | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R14 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | Calidad/flujo de consejo no acreditados | Delta/plan no prueba recomendación razonada | E16; V20 | NO VERIFICADO | F13,F20; B06,B07 / U04; PX12,PX26 | P0 | Contexto de revisión y rúbrica | Presenta recomendación referida a elementos reales y no la aplica automáticamente. |
| AC17 Solicita modificaciones mediante lenguaje natural | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R15 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | Deltas cliente conectados y débiles | Gramática/operaciones fake/local probadas | E07/E11 | PARCIALMENTE CUMPLIDO | F03,F10,F13; B02,B05,B08 / U03; PX13,PX26 | P0 | Reglas/contexto autorizado | Instrucción válida obtiene propuesta tipada; salida malformada/ambigua se rechaza o aclara sin mutar. |
| AC18 Confirma operaciones cuando corresponde | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R16; exigir toda mutación IA es política técnica propuesta | Obligatorio documentado; atribución textual al docente NO VERIFICADA | Aplicación inmediata tras éxito | Plan confirmado backend, con carrera conocida | E12 | NO CUMPLIDO | F11; B08 / U03; PX14,PX15,PX23 | P0 | Misma revisión del contexto y rol vigente | Cancelar no escribe; confirmar plan propio vigente persiste una vez; obsoleto requiere nueva interpretación. |
| AC19 Modifica respetando permisos | RECOMENDACIÓN TÉCNICA; desarrolla autorización de maestro §11/R16 | Condición de seguridad del proyecto; no cita textual académica | PATCH/snapshot indebidos reproducidos | Revalida writes, brechas S3/legacy | E05/E06/E12 | PARCIALMENTE CUMPLIDO | F05,F11; B01,B02,B08 / U01,U03,U05; PX17,PX22,PX25 | P0 | Política por acción, no sólo UI | Retirado/lector no escriben por ningún transporte ni FK; consulta de miembro activo permanece permitida. |
| AC20 Todos ven modificaciones autorizadas | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R17 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | Sync parcial, sin revisión | Documento/revisión y filtros; E2E pendiente | E05/E08/E09 | PARCIALMENTE CUMPLIDO | F06,F07,F12; B02,B03,B08 / U01,U03; PX03,PX16,PX20 | P0 | AC04 y replay | Los tres convergen, eco no aplica dos veces y respuesta/evento atrasado no pisa revisión nueva. |
| AC21 Recupera historial conversacional | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R18 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | Sólo array volátil | Planes no recuperan conversación | E15 | NO CUMPLIDO | F18; B04 / U02; PX18,PX20,PX21 | P0 | Persistencia/orden/acceso | Recargar y paginar conserva preguntas/respuestas/actor/reply_to en orden autorizado. |
| AC22 Configura proveedor IA de forma segura | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R19; seguridad de claves es recomendación técnica | Configuración obligatoria documentada; proveedor concreto/multimarcas no impuestos | Key/modelo configurables, SDK declarado | Factory, SDK no declarado/disponible | E24/E22 | PARCIALMENTE CUMPLIDO | F32; B00,B05 / U00,U04; PX24,PX27 | P0 | Configuración backend y fake | Key sólo backend; modelo/config inválida da error controlado; sin secreto en bundle/eventos/logs. |
| AC23 Modelo local como mejora opcional | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/Modelo local y orden expresa de fase5 | OPCIONAL | Sin adaptador LLM local | Parser determinista no es LLM | E24; V29 | OPCIONAL | F29; V29/B05 / U04 (sólo futuro); V29 | P3 | Modelo/hardware/corpus aún no definidos | No bloquea núcleo ni exige sustituir Gemini; sólo integrar tras decisión y pruebas propias. |

Para AC18 se propone técnicamente confirmar toda mutación IA, más estricto que “cuando corresponde”, sin atribuir esa política al docente. AC19 es garantía técnica de autorización. AC22 separa configuración documentada de la gestión segura de claves. Contexto individual ocurre dentro del grupo compartido; no se añadió un requisito de chat privado invisible a los demás.

## F. Selección definitiva de alternativas

La selección se fija para la evidencia actual; no se cambian decisiones de fase4, y las opciones INVESTIGAR permanecen sin elegir algoritmo. “Definitiva” cierra esta auditoría, no elimina gates pendientes ni autoriza código. MIGRAR en F24 significa capacidad con adaptador, no copia de app, modelos o migraciones.

| Funcionalidad | Decisión final de auditoría | Fundamento/limitaciones | Origen aprovechable | Destino propuesto / verificación |
|---|---|---|---|---|
| F01 Editor base: entidades/clases relacionales, atributos y operaciones visuales | CONSERVAR | Preservar requisito base; no es orden de reimplementarlo Riesgo: Guardar/roles presentan fallos atendidos por F05/F06; conservar UI no los valida | Editor React Flow conectado; no sustituir motor; evidencia E01,E02 | B00 / U00 |
| F02 UML ampliado: kinds, métodos, realización/dependencia y ownership | ADAPTAR | Extensión útil, no brecha obligatoria del chat Riesgo: Pérdida de semántica whole/JPA y conversión de IDs | Contrato de seis relaciones, métodos y kinds validado; evidencia E01,E03 | B10 / U08 |
| F03 Validación determinista del dominio, tipos y multiplicidades | ADAPTAR | Bloqueo de integridad para las mutaciones requeridas Riesgo: Coerciones incorrectas, pérdida de tipo y validación desigual entre entradas | Serializer/operaciones con reglas y tests; evidencia E01,E03,E07,E14 | B02 / U01,U03 |
| F04 Autenticación JWT, proyectos e invitaciones base | CONSERVAR | Preservar acceso e identidad de cada integrante Riesgo: Configuración/refresh y permisos no completamente certificados; F05 separado | Sesión/CSRF/allauth y proyectos con otro contrato; evidencia E02,E04 | B00,B01 / U00,U05 |
| F05 Autorización uniforme y revocación REST/WS | ADAPTAR | Seguridad e integridad; no implica vulnerabilidad de red completa demostrada Riesgo: Escritura fuera de rol y posible entrega posterior al retiro; pruebas E2E pendientes | Revalida escritura; S3 no cierra lectura y legacy vulnerable; evidencia E04,E05,E06 | B01,B03 / U01,U05 |
| F06 Revisión, reconciliación y guardado autoritativo | ADAPTAR | Bloqueo de integridad del tablero compartido Riesgo: Sobrescritura, borrado y documento visual/ORM divergente | expected_revision/lock/409 y filtros de estado; carrera F2 conocida; evidencia E05,E07,E08 | B02,B03 / U01 |
| F07 Conectividad colaborativa: presencia, reconexión y resync | ADAPTAR | Se prioriza continuidad del tablero; presencia visual no es requisito académico independiente Riesgo: Eventos perdidos, canal viejo, presencia fantasma y revocación S3 | Presencia ORM/TTL, heartbeat y hook retry con buffer limitado; evidencia E06,E08,E09 | B03 / U01 |
| F08 Bloqueo fuerte por elemento con lease | INVESTIGAR | Opcional y condicionado a política de colaboración Riesgo: Bloqueo abandonado o falso sentido de exclusión | No equivalente de lease fuerte verificado; evidencia E05,E09 | V08 / U09 |
| F09 Undo/redo colaborativo seguro | INVESTIGAR | Útil, sin necesidad de examen acreditada Riesgo: Restaurar snapshot puede borrar trabajo remoto | Historial local de 50 snapshots, no inversas concurrentes; evidencia E10 | V09 / U09 |
| F10 Lenguaje natural a operaciones estructuradas del modelador | ADAPTAR | Capacidad académica existente parcial a completar Riesgo: Salida de proveedor no confiable y semántica traducida incorrectamente | execute_operations y gramáticas/fakes probados; evidencia E03,E07,E11 | B08 / U03 |
| F11 Plan IA persistido, preview y confirmación autorizada | ADAPTAR | Confirmación y seguridad del requisito de cambios Riesgo: Plan obsoleto, rol revocado, aplicar contexto viejo o publicar antes de persistir | Plan usuario/diagrama/TTL, confirmación y aplicación atómica; evidencia E07,E11,E12 | B08 / U03 |
| F12 Dedupe, retry e identidad de solicitud/aplicación | ADAPTAR | Integridad de acciones autorizadas; no exactly-once demostrado Riesgo: Duplicación de datos/eventos o falso409 tras aplicación exitosa | request_id/hash y resultado, con retry409 y sin unique compuesto; evidencia E07,E12 | B03,B04,B08 / U01,U02,U03 |
| F13 Contexto autoritativo del diagrama y selección | FUSIONAR | Precondición para asesoría/modificaciones sobre datos vigentes Riesgo: Interpretar contra contexto viejo o no autorizado; no confundir con memoria de diálogo | build_diagram_summary de documento autorizado y selección; evidencia E07,E11 | B02,B06 / U04 |
| F14 Voz: conservar push-to-talk y adaptar transcripción final | ADAPTAR | Mejora opcional sobre entrada existente Riesgo: Permisos de audio, parciales y confirmación errónea; no offline garantizado | isFinal/dedupe/estados probados en utilidades; matiz wake/send; evidencia E13 | Reutiliza B07/B08 / U06 |
| F15 Síntesis de voz opcional | ADAPTAR | Opcional; no precede requisitos conversacionales Riesgo: Feedback acústico, disponibilidad y lectura de mensajes sin preferencia | speakDiana y dianaVoice: selección/segmentación probadas; evidencia E13 | Reutiliza B07 / U06 |
| F16 Chat grupal: preguntas/respuestas compartidas, actor y destinatario | DESARROLLO NUEVO | Requisitos obligatorios R2-R7, incluida consulta por lectores autorizados Riesgo: Suplantación de actor, mensajes de otro proyecto o envío sólo local | aiHistory local; PlanIA.usuario no es mensaje grupal; evidencia E04,E06,E15,R2-R7 | B04,B07 / U02 |
| F17 Memoria grupal/individual y continuidad de seguimientos | DESARROLLO NUEVO | Requisitos R8-R11 siguen siendo P0 aunque no haya puntuación total Riesgo: Mezclar participantes, contexto obsoleto, exposición fuera del proyecto y calidad de anáforas | Sin memoria conversacional; resumen sólo de diagrama; evidencia E15,E16,R8-R11 | B06,V17 / U04 |
| F18 Persistencia y recuperación autorizada del historial IA | DESARROLLO NUEVO | Requisito R18; ausencia no reduce prioridad Riesgo: Lectura indebida, orden ambiguo o duplicados; diseño de retención pendiente | Seis entradas locales; planes guardados no son diálogos; evidencia E04,E15,R18 | B04 / U02 |
| F19 Consulta conceptual de sólo lectura separada de mutación | FUSIONAR | R12 y separación de permiso preguntar/editar Riesgo: Confundir mensaje con plan y atribuir calidad no medida | Sin modo answer; contrato de operaciones/clarificación; evidencia E07,E11,E16,R12 | B07 / U04 |
| F20 IA moderadora/asesora contextual del equipo y recomendaciones | DESARROLLO NUEVO | R13-R14 y propósito moderador, sin degradar por falta de donante Riesgo: Consejos erróneos, atribución incorrecta o recomendaciones aplicadas sin confirmar | Planes de modelado; no moderación grupal equivalente; evidencia E15,E16,R13-R14 | B06,B07,V20 / U04 |
| F21 XMI actual de NodoBoard: conservar entrada/salida | CONSERVAR | Capacidad existente opcional a conservar, no desarrollar otra Riesgo: Preservación semántica/layout no completa; errores de tipo atendidos en validación | Otro perfil parser; X3 incompatible con fixture NB; evidencia E14,E17 | B00,B02; B09 sólo ampliación / U00; U07 sólo ampliación |
| F22 XMI: perfiles compatibles, límites seguros y preview versionado | FUSIONAR | Mejora importante; compatibilidad y rechazo de vacío son veto antes de incorporar, no obligación de migrar ahora Riesgo: Importar vacío silenciosamente o reemplazar estado posterior al preview | Límites/mapping/dry_run útiles; X3 y preview sin expected_revision; evidencia E14,E17,E18 | B09 / U07 |
| F23 Interoperabilidad semántica/visual certificada con EA | INVESTIGAR | Útil fuera de requisitos conversacionales; falta alcance de herramienta Riesgo: Pérdida de semántica/layout encubierta por conteos iguales | Perfiles/layout probados parcialmente, sin vuelta EA real; evidencia E14,E17 | V23,B09 / U07 |
| F24 Exportación Spring Boot por capas y validación del artefacto | MIGRAR | Capacidad adicional, no debe desplazar brechas obligatorias Riesgo: JPA incorrecto, artefacto no compilable o nombres/rutas inválidas | ZIP Maven/Java21/Spring3.4/PostgreSQL; repos/service/controller/DTO/mapper; evidencia E03,E19 | B10 / U08 |
| F25 Ciclo de proyectos: archivar/restaurar/duplicar y roles extendidos | ADAPTAR | Opcional sobre proyectos ya existentes Riesgo: Copiar miembros al duplicar o restaurar sin privacidad/unicidad | Acciones/servicios específicos, con tests PG pendientes; evidencia E02,E04,E20 | B11 / U09 |
| F26 Errores estructurados, foco y accesibilidad básica | FUSIONAR | Mejora importante de uso y recuperación de conflictos Riesgo: Exponer raw/detalles, enfocar ID obsoleto o declarar accesibilidad sin prueba | Códigos/element_id, Escape/aria-live y enfoque; evidencia E08,E16,E21 | B07,B08 / U00,U03,U04 |
| F27 Contratos, separación de responsabilidades y pruebas de frontera | ADAPTAR | Mejora transversal importante; gates de seguridad siguen P0 en sus filas Riesgo: Copiar pruebas de JSON donante como si probaran ORM destino o asumir suite verde | Módulos/fakes/tests útiles, Canvas concentrado y deuda; evidencia E01,E08,E11,E22 | B00 + pruebas de cada tarea / U00 + pruebas de cada tarea |
| F28 Entrada por imagen de NodoBoard | CONSERVAR | No descartar capacidad propia; verificación real pendiente Riesgo: Resultado multimodal no validado o creación completa que pisa estado | Sin equivalente de boceto a diagrama localizado; evidencia E07,E23 | B00,B02 / U00 |
| F29 Proveedor alternativo/LLM local opcional | INVESTIGAR | Opcional; no requisito ni sustitución obligatoria de Gemini Riesgo: Nueva dependencia operativa y calidad incierta; no garantía local por parser | Factory Gemini y gramática; no LLM local real; evidencia E07,E11,E24,R20 | V29,B05 / U04 sólo si se aprueba |
| F30 Incorporación integral de Diana/React/auth/ORM legacy | DESCARTAR | Redundante e incompatible con restricción arquitectónica Riesgo: Seguridad legacy, dos autenticaciones y pérdida de dominio/estado | UI/estado/sesión/legacy completos pero no chat grupal persistente; evidencia E02,E06,E15,E25 | Exclusión documental, sin implementación / Sin segundo asistente/framework |
| F31 Completar enlace de invitación firmado sin reemplazar invitaciones | ADAPTAR | Mejora importante; no bloquea toda colaboración porque hay aceptación interna Riesgo: Token expirado/reutilizado, acceso erróneo o confusión con activar cuenta | Flujo distinto de invitaciones en API, no parche directo; evidencia E02,E26 | B01; B11 si precisa ajuste / U05 |
| F32 Proveedor IA configurable y adaptador único en backend | FUSIONAR | Conservar configuración obligatoria y verificar integración, no exigir multiempresa Riesgo: Mezclar dos APIs SDK o usar fallback no disponible | get_ai_provider separado, SDK ausente en requirements; evidencia E07,E11,E24,R19 | B05 / U00,U04 |

Alternativas materiales de fase4J, conservando sus notas:

| ID/alternativa | Decisión fase4 | Puntuación /100 | Prioridad del problema | Esfuerzo /5 | Riesgo /5 | Confianza |
|---|---|---|---|---|---|---|
| A01 Mantener snapshots/permisos actuales sin endurecimiento | DESCARTAR | 62.0 | P0 | 1 | 5 | ALTA |
| A02 Revisión/persistencia propias diseñadas desde NodoBoard | DESARROLLO NUEVO | 76.0 | P0 | 5 | 5 | MEDIA |
| A03 Sustituir XMI NB por parser DC directamente | DESCARTAR | 36.0 | P1 | 4 | 5 | ALTA |
| A04 Usar sólo historial local como chat grupal recuperable | DESCARTAR | 62.0 | P0 | 1 | 4 | ALTA |
| A05 Portar backend completo Diana/JSON/planes/sesión | DESCARTAR | 54.0 | P0 | 5 | 5 | ALTA |
| A06 Crear un generador Spring propio completo sin reutilizar donante | DESARROLLO NUEVO | 47.0 | P2 | 5 | 4 | MEDIA |

Se selecciona F05/F06 frente a A01 sin endurecimiento; A02 (revisión propia sin aprovechar límites/pruebas donantes) es viable pero no ofrece evidencia suficiente para preferir reconstrucción completa sobre adaptación al ORM. El servicio objetivo será propio de NB en ambos casos: la diferencia es aprovechar patrones/fixtures de revisión probados, no copiar JSON del donante.

A04 arrays locales no cubre chat/historial; F16/F17/F18/F20 DESARROLLO NUEVO es la solución, con NE preservados. A05 backend Diana completo aporta planes pero cambia auth/dominio y tampoco resuelve conversación; elegir F10/F11/F12 adaptados. A03 parserDCdirecto falla fixture conocida; conservarF21 y fusionarF22 tras gates. A06 generador entero desde cero no se prefiere a F24 con adaptador, y ambas opciones son posponibles respecto al chat.

No trasladar JSX/hooks/Zustand/React Flow, authStore/AppRouter/ProjectsPage/ActiveUsers/VoiceCommand vacíos, allauth sólo por IA, ni APIs/tabla UML legacy como segunda autoridad. No borrar ninguna de esas piezas del donante ni dependencias durante esta ejecución.

## G. Decisión final sobre la IA

Conservar la superficie/entradas del asistente NB (texto, push-to-talk, imagen) y el proveedor configurado; reemplazar en una implementación futura la aceptación/aplicación insegura de deltas por servicios autorizados, operaciones tipadas, planes y escritor común. No conservar defectos ni añadir un segundo personaje/chat.

| Decisión | Diseño propuesto y procedencia |
|---|---|
| Identificar participante | B04 deriva autor de request.user/scope.user y destinatario del mensaje-pregunta; nunca se permite actor arbitrario. Requisito documentado+control técnico |
| Compartir preguntas/respuestas | B04 persiste mensajes por conversación/proyecto, B03 publica tras commit, U02 renderiza el mismo ID por HTTP/WS/replay |
| Historial | B04 consulta paginada/ordenada por secuencia de conversación, con permisos vigentes; PlanIA no se usa como diálogo |
| Contexto grupal | B06 reúne intercambios previos completados, acuerdos/resumen con fuentes y diagrama autorizado/revisión; política/tokenbudget explícitos |
| Contexto individual | Mismo registro compartido, vista filtrada por actor real y referencias a su pregunta/turno; no hilo privado ni mezcla con otro proyecto |
| Seguimientos/concurrencia | Cola durable ordenada por solicitud dentro de proyecto; contexto usa intercambios anteriores completados + solicitud actual, excluye preguntas futuras. Diferentes proyectos pueden procesarse independientemente |
| Moderación/asesoría | Política nueva: asesorar/pedir aclaración, resumir acuerdos y señalar sugerencias como tales, fundamentar en contexto, no tomar decisiones ni aplicar cambios sin autorización. V20 verifica esta definición con rúbrica |
| Consultas conceptuales | Salida answer separada de proposal/error; no llama al escritor. Actor lector activo puede consultar sin permiso de modificar |
| Solicitudes de cambio | B08 transforma a allowlist del dominio NB, simula/valida lote, crea plan inmutable ligado a proyecto/autor/contexto/revisión; confirmar llama B02 |
| Autorización y confirmación | Toda mutación IA requiere confirmación explícita como política técnica propuesta; pertenencia/rol revisados en aplicación, cancelación y expiración con estados definidos |
| Dedupe | message_id/request_id para mensajes; key+fingerprint por intento/plan para aplicación; event_id/revisión/cursor en cliente. Dos instrucciones iguales deliberadas pueden usar keys distintas |
| Proveedor | B05 adaptador único sobre Gemini ya configurado, fake en pruebas y parámetros backend; no requisito nuevo de múltiples marcas/local |
| Capacidades DC aprovechables | ai_operations/DiagramaSerializer como referencia determinista, create_plan/apply_plan sin sus bugs, build_diagram_summary/factory, collaborationSync, errores y utilidades de voz opcionales |
| Componentes redundantes | Diana completa, nuevo chat, segunda auth/persistencia y componente monolítico Canvas React. Ninguno aporta memoria grupal por sí mismo |

No se afirma superioridad semántica del proveedor. La cola por proyecto y memoria con fuentes son elecciones técnicas para determinismo/recuperación, no requisitos docentes literales. El alcance mínimo no necesita Celery ni un LLM local: un trabajador backend propuesto con claim/lease durable es una opción a cerrar en B07. No se arranca ni instala ahora.

## H. Arquitectura objetivo

Leyenda: [E] existente a conservar; [A] existente que se adapta; [N] componente nuevo propuesto. Todos los nodosN y extensionesA son documentación. PostgreSQL conserva la autoridad; Redis/Channels transporta eventos y presencia, no es la única copia del historial. JointJS conserva edición visual; ninguna salida IA escribe directamente sin writer.

~~~mermaid
flowchart LR
  subgraph Angular["NodoBoard Angular"]
    Auth["E: Auth/JWT y dashboard"]
    Editor["A: editor JointJS + servicios"]
    Chat["A: único ChatAsistenteIa"]
    Store["A: estado RxJS, revisión y cursor"]
    Preview["N: estado/preview de plan en chat"]
  end
  subgraph Django["NodoBoard Django"]
    Gate["A: identidad, membresía y permisos"]
    Msg["N: conversaciones/mensajes/historial"]
    Context["N: contexto grupal e individual"]
    IA["N/A: orquestador + adaptador proveedor"]
    Plans["N: validador/planes/confirmación"]
    Writer["A: escritor ORM único + revisión"]
    Events["A: Channels, publicación y resync"]
    Export["A: XML existente; mejoras opcionales"]
  end
  PG[("E/A: PostgreSQL ORM + nuevos registros")]
  Redis[("E/A: Redis y canales")]
  Provider["E/A: proveedor configurado; fake en pruebas"]
  Auth --> Gate
  Chat --> Gate
  Editor --> Gate
  Preview --> Gate
  Gate --> Msg
  Gate --> Plans
  Msg --> Context
  Context --> IA
  IA --> Provider
  IA --> Msg
  IA --> Plans
  Plans --> Writer
  Gate --> Writer
  Writer --> PG
  Msg --> PG
  Context --> PG
  Export --> Writer
  Writer --> Events
  Msg --> Events
  Events --> Redis
  Redis --> Store
  Store --> Editor
  Store --> Chat
  Store --> Preview
~~~

Writer actualiza ORM y proyección visual en una transacción sobre el agregado Proyecto. El snapshot visual sólo conserva geometría/presentación de elementos autorizados existentes; no resucita relaciones ni asigna clase asociativa por orden. Se justifica una revisión de Proyecto para cubrir todos sus escritores actuales (REST, WS, importación, imagen/IA) sin crear un Diagrama JSON paralelo.

Conversación y mensaje son nuevos datos hoy ausentes; una conversación por proyecto basta para el mínimo. Mensaje tiene identidad/orden/actor/relación de respuesta. SolicitudIA permite recuperación del trabajo del proveedor y un único resultado visible. PlanModelado guarda intención autorizable separada del diálogo. ResumenContexto sólo si se necesita memoria acotada a largo plazo, con fuentes; los detalles/migraciones se diseñarán al implementar, no se copian de DC.

No mantener transacciones/locks abiertos durante llamada al proveedor. Se captura contexto/revisión, se solicita fuera del lock, se valida contra esa base y se rechaza propuesta obsoleta en vez de refrescarla silenciosamente. on_commit no garantiza entrega de red: el historial durable y consulta de cabeza/cursor/resync recuperan eventos perdidos; no se promete exactly-once.

## I. Plan técnico backend

Todos los archivos sin marca de propuesta son existentes según los inventarios/referencias anteriores. “Potencial/PROPUESTO” identifica un archivo o modelo no creado. No se proponen migraciones concretas numeradas ni se ejecuta su generación: sólo se justifica qué datos nuevos necesitan esquema cuando se autorice.

### B00 — Acreditar entorno destino y baseline de regresión

| Campo | Plan futuro |
|---|---|
| Objetivo | Acreditar entorno destino y baseline de regresión |
| Requisitos/funciones | AC01–AC04,AC22; RT03 |
| Archivos existentes NB | backend/core/settings.py,asgi.py,urls.py; backend/requirements.txt; modelado/tests.py; informes/fixtures actuales. |
| Archivos nuevos potenciales, NO CREADOS | Ningún archivo nuevo de producto necesario; fixtures/runners de prueba futuros aislados, nombres por acordar. |
| Modelos afectados/propuestos | No cambio; documentar esquema aplicado sólo en entorno futuro autorizado. |
| Servicios/reglas | Configuración JWT/Channels/DB/proveedor y contrato actual. |
| HTTP: existente/extensión/propuesta | Conservar /api/usuario/* y carga de diagrama; inventariar payloads reales. |
| Eventos WebSocket | Conservar ruta /ws/pizarra/{proyecto_id}/; fijar fixture de protocolo. |
| Dependencias | Autorización de implementación y entorno de prueba propio; estado sucio actual preservado. |
| Comportamiento esperado | Baseline Angular/Django5.2/PG/Redis y fixture XML documentado; errores existentes distinguidos. |
| Validaciones | Versiones/SDK/driver presentes, URLconf real, sin reutilizar DB desarrollo. |
| Seguridad/permisos | No copiar .env, claves ni abrir servicios reales; settings de prueba explícitos. |
| Pruebas futuras | PX01,PX02,PX03,PX27; regresión F1/F2/F3 en entorno fiel. |
| Criterio de aceptación | Checklist de entorno y contratos pasa o bloqueo localizado documentado antes de activar escrituras nuevas. |
| Riesgo | Confundir errores SQLite/SDK con estado real o perder package-lock preexistente. |
| Prioridad de tarea | P0 |

### B01 — Unificar permisos por acción y revocar lectura/escritura

| Campo | Plan futuro |
|---|---|
| Objetivo | Unificar permisos por acción y revocar lectura/escritura |
| Requisitos/funciones | AC05,AC08,AC19; RT01 |
| Archivos existentes NB | backend/usuario/models.py::UserColaborador; modelado/views.py,serializers.py,consumers.py,middleware.py,realtime.py. |
| Archivos nuevos potenciales, NO CREADOS | Potencial backend/modelado/permissions.py y servicio de revocación; PROPUESTOS, no existentes. |
| Modelos afectados/propuestos | UserColaborador/Proyecto; presencia por canal propuesta B03, sin duplicar User. |
| Servicios/reglas | Resolver miembro activo/rol; negar cambio de FK a otro proyecto; invalidar canales al retirar/cambiar rol. |
| HTTP: existente/extensión/propuesta | PATCH/PUT/DELETE proyecto, colaboradores, invitaciones; todos los contratos nuevos de chat/historial/plan. |
| Eventos WebSocket | Handshake y cada comando; nuevo aviso access.revoked propuesto con cierre y retiro de grupos. |
| Dependencias | B00; política mantener propietario/editor/visualizador, preguntar separado de editar. |
| Comportamiento esperado | Miembro activo puede consultar; sólo roles autorizados modifican; retirado no escucha ni envía. |
| Validaciones | Comprobar proyecto tanto original como destino de referencia; estado actual al ejecutar, no sólo al conectar. |
| Seguridad/permisos | Actor siempre request.user/scope.user; no confiar en actor_id cliente, UI o permiso almacenado antiguo. |
| Pruebas futuras | PX07,PX17,PX22,PX25,PX27. |
| Criterio de aceptación | Tres roles y retirado cubiertos por REST/WS; cero entregas después del límite de revocación definido y confirmado. |
| Riesgo | Cerrar sólo cliente honesto, omitir otra pestaña o publicar payload ya en cola antes del corte. |
| Prioridad de tarea | P0 |

### B02 — Servicio único de escritura UML y revisión del agregado

| Campo | Plan futuro |
|---|---|
| Objetivo | Servicio único de escritura UML y revisión del agregado |
| Requisitos/funciones | AC03,AC04,AC17–AC20; RT02 |
| Archivos existentes NB | backend/modelado/models.py,serializers.py,views.py,consumers.py::_guardar_snapshot_db; generador/views.py y servicios XML; asistente/views.py. |
| Archivos nuevos potenciales, NO CREADOS | Potencial backend/modelado/services/documento.py y validadores.py; PROPUESTOS; nombre final pendiente. |
| Modelos afectados/propuestos | Proyecto con revisión monotónica propuesta; Entidad/Atributo/Relacion conservados y referencias/IDs estables cuando corresponda. |
| Servicios/reglas | Leer documento canónico, validar/autorizar lote, bloquear Proyecto y comparar revisión; actualizar ORM+snapshot en misma transacción. |
| HTTP: existente/extensión/propuesta | EXTENDER PATCH/carga de proyecto y importación; futuros apply-plan deben delegar; no nueva autoridad JSON donante. |
| Eventos WebSocket | EXTENDER guardar_snapshot y snapshot_guardado: expected_revision, documento/remapeos/revisión autoritativos. |
| Dependencias | B01; F03/F06; justificar campo revisión y migración propia futura, sin copiar archivos del donante. |
| Comportamiento esperado | Todo escritor rechaza base vieja sin cambios; normalizar antes de persistir; snapshot visual no resucita semántica ausente en ORM. |
| Validaciones | IDs/duplicados/extremos/cardinalidad/tipos, pertenencia, borrados en cascada explícitos; atributo bigint/long conserva tipo. |
| Seguridad/permisos | Validación determinista servidor; no ejecutar código IA; permisos dentro del lock y transacción. |
| Pruebas futuras | PX03,PX13,PX15,PX17,PX23,PX26; fixtures R3 y H-N03. |
| Criterio de aceptación | Revisión incrementa una vez por cambio aceptado, rollback deja cero cambios/eventos; GET y ack representan misma verdad. |
| Riesgo | Algún escritor omite revisión; destruir IDs/atributos o remapear respuesta atrasada sobre otro diagrama. |
| Prioridad de tarea | P0 |

### B03 — Publicación tras commit, presencia y recuperación de estado

| Campo | Plan futuro |
|---|---|
| Objetivo | Publicación tras commit, presencia y recuperación de estado |
| Requisitos/funciones | AC01–AC04,AC20; RT01/RT02 |
| Archivos existentes NB | backend/modelado/consumers.py,routing.py,realtime.py; core/asgi.py; usuario/modelado avisos de membresía. |
| Archivos nuevos potenciales, NO CREADOS | Potencial backend/modelado/services/presencia.py y contrato de eventos; PROPUESTOS. |
| Modelos afectados/propuestos | Presencia por canal con usuario/proyecto/actividad/caducidad propuesta; revisión de B02. Mensajes durables en B04. |
| Servicios/reglas | Registro/limpieza de canales, heartbeat, on_commit publicación, resync por documento/revisión y replay de mensajes. |
| HTTP: existente/extensión/propuesta | EXTENDER GET diagrama con revisión; lectura de cabeza/cursor del chat B04. |
| Eventos WebSocket | Eventos diagram.updated/presence.updated/access.revoked PROPUESTOS; conservar/adaptar wrapper existente hasta transición coordinada. |
| Dependencias | B01,B02; Redis/Channels aislados, decisión de worker/proceso y clocks. |
| Comportamiento esperado | Reconectar autoriza de nuevo, recupera estado persistido y descarta respuestas antiguas; presencia no depende de un solo proceso. |
| Validaciones | Payloads con project_id/revision/event_id; tamaño/frecuencia/canal; TTL y múltiples pestañas. |
| Seguridad/permisos | No enviar a canal retirado; heartbeat no renueva permisos; no confiar en CORS HTTP para WS. |
| Pruebas futuras | PX03,PX16,PX18,PX20,PX22,PX23,PX25. |
| Criterio de aceptación | Commit precede evento; si publicación falla, cursor/resync recupera datos y cliente no duplica aplicación; no prometer exactly-once. |
| Riesgo | Gaps después de on_commit, presencia fantasma, reintento con token vencido y revocación sólo al escribir. |
| Prioridad de tarea | P0 |

### B04 — Conversaciones/mensajes e historial recuperable

| Campo | Plan futuro |
|---|---|
| Objetivo | Conversaciones/mensajes e historial recuperable |
| Requisitos/funciones | AC05–AC11,AC13,AC21; F16/F18 |
| Archivos existentes NB | backend/asistente/models.py placeholder,views.py,urls.py; usuario/modelado para pertenencia. |
| Archivos nuevos potenciales, NO CREADOS | Potenciales backend/asistente/serializers.py,services/conversaciones.py y tests; PROPUESTOS. |
| Modelos afectados/propuestos | ConversacionProyecto (una por proyecto mínimo); MensajeConversacion con ID servidor, secuencia por conversación, autor/rol, texto, reply_to, destinatario, fecha y request key. |
| Servicios/reglas | Crear pregunta canónica y recuperar historial paginado; referencia al User existente y proyecto, no nuevo usuario. |
| HTTP: existente/extensión/propuesta | PROPUESTOS: crear mensaje y GET historial por proyecto/cursor; nombres/rutas finales pendientes K. |
| Eventos WebSocket | chat.message.created propuesto tras commit para pregunta/respuesta; mismo ID que HTTP/historial. |
| Dependencias | B01/B03; acordar esquema de mensaje antes de implementar U02; F16 y F18 comparten modelo. |
| Comportamiento esperado | Preguntas y respuestas visibles al equipo; recarga recupera actor/orden; una pregunta por clave de intento. |
| Validaciones | Longitud/límites, reply_to del mismo proyecto, clave por actor/proyecto y fingerprint; key repetida con contenido distinto rechazada. |
| Seguridad/permisos | Autor de pregunta desde sesión; destinatario de respuesta desde pregunta; acceso al historial sólo miembros vigentes. |
| Pruebas futuras | PX04–PX08,PX18–PX21,PX25,PX27. |
| Criterio de aceptación | Tres clientes muestran mismos IDs; paginación/replay sin pérdidas/duplicados; retirado no consulta historial. |
| Riesgo | Orden por timestamps ambiguo, doble inserción concurrente, historial de otro proyecto; justificar migraciones nuevas por datos antes inexistentes. |
| Prioridad de tarea | P0 |

### B05 — Adaptador único de proveedor y configuración segura

| Campo | Plan futuro |
|---|---|
| Objetivo | Adaptador único de proveedor y configuración segura |
| Requisitos/funciones | AC22; F32 |
| Archivos existentes NB | backend/core/settings.py; asistente/views.py/requirements.txt; referencia DB/diagramas/ai_interpreter.py. |
| Archivos nuevos potenciales, NO CREADOS | Potencial backend/asistente/proveedores.py con interfaz y fake de prueba; PROPUESTO. |
| Modelos afectados/propuestos | No requiere tabla de claves ni selector de marcas para alcance mínimo; sólo parámetros backend. |
| Servicios/reglas | Adaptar interfaz del proveedor existente, límites/timeout y errores; conservar SDK NB verificado. |
| HTTP: existente/extensión/propuesta | No endpoint público de claves; llamadas sólo desde servicios backend propuestos B07/B08. |
| Eventos WebSocket | Sólo error técnico sanitizado al destinatario/proyecto según contrato, nunca secreto/raw. |
| Dependencias | B00/B01; resolver compatibilidad generate_content vs interactions antes de reutilizar. |
| Comportamiento esperado | Mismo proveedor configurado, sustituible por fake, sin segundo cliente IA de producto ni requisito local. |
| Validaciones | Clave/modelo/config presentes y válidos, timeout, tamaño respuesta y esquema del resultado. |
| Seguridad/permisos | Secretos sólo backend; logging mínimo por IDs técnicos; no enviar secretos del proyecto al contexto. |
| Pruebas futuras | PX24,PX26,PX27. |
| Criterio de aceptación | Pruebas con fake y config ausente/errónea generan estados controlados sin filtrar claves; ningún SDK faltante queda oculto. |
| Riesgo | Dependencia genai ausente en donante y APIs incompatibles; no instalar ni cambiar proveedor en esta fase. |
| Prioridad de tarea | P0 |

### B06 — Memoria/contexto grupal e individual con fuentes

| Campo | Plan futuro |
|---|---|
| Objetivo | Memoria/contexto grupal e individual con fuentes |
| Requisitos/funciones | AC08–AC13,AC15–AC16; V17 |
| Archivos existentes NB | backend/asistente/models.py,views.py; modelado/models.py para lectura autorizada y B02. |
| Archivos nuevos potenciales, NO CREADOS | Potenciales backend/asistente/contexto.py y corpus versionado de aceptación; PROPUESTOS. |
| Modelos afectados/propuestos | B04 mensajes; ResumenContexto propuesto con alcance grupo/actor, fuentes/corte/hash y versión; no copiar PlanIA como diálogo. |
| Servicios/reglas | Seleccionar intercambios previos del proyecto y actor actual, snapshot de diagrama/revisión, referencias y resumen acotado. |
| HTTP: existente/extensión/propuesta | Interno a consulta/interpretación; no permitir al cliente elegir identidad ajena ni aportar historia como autoridad. |
| Eventos WebSocket | No requiere evento de memoria privada; compartir mensajes sigue B04; UI puede recibir metadata no sensible de contexto. |
| Dependencias | B02,B04,B05; V17 acuerda causalidad/retención/límites antes de desarrollar recuperación. |
| Comportamiento esperado | Memoria reconstruible tras recarga; contexto individual es filtro del actor dentro del grupo, no otro chat privado inventado. |
| Validaciones | Fuentes del mismo proyecto, presupuesto de contexto, selección/dedupe de mensajes, no instrucciones de sistema desde texto usuario. |
| Seguridad/permisos | Aislamiento por proyecto y permisos al leer; historial no autorizado nunca entra al proveedor. |
| Pruebas futuras | PX09–PX11,PX19,PX21,PX25,PX27. |
| Criterio de aceptación | Corpus de tres actores y seguimiento largo con hechos grupales/por actor correctamente recuperados; evidencia de IDs/corte/contexto. |
| Riesgo | Truncar hecho necesario, mezclar actor/otro proyecto o confundir instantánea del diagrama con memoria; Q sigueNE hasta evaluar. |
| Prioridad de tarea | P0 |

### B07 — Orquestación de consultas y moderación sin escritura

| Campo | Plan futuro |
|---|---|
| Objetivo | Orquestación de consultas y moderación sin escritura |
| Requisitos/funciones | AC05–AC16,AC21–AC22; V20/F19/F20 |
| Archivos existentes NB | backend/asistente/views.py,urls.py,models.py y servicios B04/B05/B06 futuros; chat actual como cliente. |
| Archivos nuevos potenciales, NO CREADOS | Potenciales backend/asistente/orquestacion.py,politica_asesoria.py y trabajador/management command; PROPUESTOS, sin imponer Celery. |
| Modelos afectados/propuestos | SolicitudIA propuesta: pregunta, estado, key, contexto/revisión base, resultado/errores y lease del trabajador; mensaje respuesta único por solicitud. |
| Servicios/reglas | Cola durable por proyecto en orden de solicitudes; proveedor fuera de transacción larga; respuesta ligada a pregunta y actor; política asesor/moderador. |
| HTTP: existente/extensión/propuesta | Crear pregunta devuelve aceptación/estado; GET historial/estado recupera respuesta; contrato answer/proposal/error propuesto. |
| Eventos WebSocket | chat.message.created y chat.request.status propuestos; publicar sólo mensajes persistidos. |
| Dependencias | B04,B05,B06, B03; V20 acuerda rúbrica. Estado de transporte puede validarse con fake sin acreditar inteligencia. |
| Comportamiento esperado | Consulta conceptual no toca ORM/revisión; explica/sugiere/pide aclaración, nombra destinatario, no aplica cambios implícitos. |
| Validaciones | Respuesta estructurada; distinguir answer/proposal/error; lease/retry no generan varias respuestas canónicas. |
| Seguridad/permisos | Permiso consultar separado de editar; texto no confiable, límites, no raw del proveedor ni ejecución de instrucciones como código. |
| Pruebas futuras | PX04–PX12,PX18–PX21,PX24–PX27. |
| Criterio de aceptación | Equipo ve una respuesta atribuida por pregunta; fallos recuperables; evaluación humana de corpus para semántica antes de cerrar AC12/15/16. |
| Riesgo | Cola bloqueada, dos workers duplican resultado, consejos no evaluados; lease/timeout/recovery y pruebas PG requeridos. |
| Prioridad de tarea | P0 |

### B08 — Operaciones tipadas, planes confirmables e idempotencia

| Campo | Plan futuro |
|---|---|
| Objetivo | Operaciones tipadas, planes confirmables e idempotencia |
| Requisitos/funciones | AC17–AC20; F10/F11/F12 |
| Archivos existentes NB | backend/asistente/views.py,models.py,urls.py; modelado writerB02; referencia DB/diagramas/ai_operations.py,ai_plans.py. |
| Archivos nuevos potenciales, NO CREADOS | Potenciales backend/asistente/operaciones.py,planes.py y serializers propios; PROPUESTOS. |
| Modelos afectados/propuestos | PlanModelado propuesto: dueño/proyecto, operaciones inmutables, revisión/contexto base, hash/TTL/estado/key/resultado. No copiar FK/migraciones del donante. |
| Servicios/reglas | Interpretar desde contexto autorizado, simular/validar, persistir plan; confirmar dentro del mismo writer B02 con lock y permisos vigentes. |
| HTTP: existente/extensión/propuesta | PROPUESTOS interpretar/confirmar/cancelar plan; cliente confirma ID/hash/revisión, nunca envía lote ejecutable como autoridad. |
| Eventos WebSocket | Documento autoritativo tras commitB03 y estado del plan; historial registra propuesta/resultado sin duplicar aplicación. |
| Dependencias | B01,B02,B03,B05,B06; contratos U03; sólo dominio NB actual en mínimo. |
| Comportamiento esperado | No refrescar silenciosamente revision_base tras proveedor; consulta obsoleta exige revalidación/reinterpretación; confirmar/cancelar no equivalen. |
| Validaciones | Allowlist/campos/IDs/tipos/endpoints, lotes completos/rollback, roles/TTL/hash, misma revisión que contexto y expected_revision. |
| Seguridad/permisos | Actor desde sesión; plan propio y proyecto autorizado; propietario/editor sólo según política, visualizador no aplica; revalidar en cada confirmación. |
| Pruebas futuras | PX13–PX18,PX22,PX23,PX26; regresiones H-D03/H2-D01. |
| Criterio de aceptación | Primera confirmación válida aplica una vez; retry exacto devuelve resultado de ese intento o estado definitivo sin reaplicar; otra instrucción idéntica puede tener key nueva. |
| Riesgo | Repetir eventos, rebase equivocado, stale autosave posterior; dedupe de datos/publicación/cliente se prueba por separado. |
| Prioridad de tarea | P0 |

### B09 — XMI compatible: perfiles, límites y preview ligado a revisión

| Campo | Plan futuro |
|---|---|
| Objetivo | XMI compatible: perfiles, límites y preview ligado a revisión |
| Requisitos/funciones | RT05; F21/F22/F23, opcional |
| Archivos existentes NB | backend/generador/services/xmi_importer.py,xmi_exporter.py; serializers.py,views.py; modelado writerB02. |
| Archivos nuevos potenciales, NO CREADOS | Potencial adaptador/perfiles XML en generador/services; PROPUESTO; no sustituir parser sin fixture. |
| Modelos afectados/propuestos | Conservar ORM; preview DTO temporal y revisión base, sin modelo de diagrama donante. |
| Servicios/reglas | Fusionar límites/preview de DC con perfil NB; importar por B02 con revisión y respuesta autoritativa. |
| HTTP: existente/extensión/propuesta | EXTENDER importar-xml con preview/confirmación compatible o ruta versionada por decidir; exportar-xml actual conservado. |
| Eventos WebSocket | Publicar cambio finalB03; preview no publica cambio de documento. |
| Dependencias | B02/B03, V23, X3 resuelto antes de portar parser; U07. |
| Comportamiento esperado | Fixture conocida no se convierte en éxito vacío; conteos/semántica se explican antes de reemplazar. |
| Validaciones | Namespaces/perfiles, límites uniformes de archivo/texto, sin DTD/red, referencias/whole/tipos y rechazo vacío inesperado. |
| Seguridad/permisos | Mismos permisos import propietario/editor y lectura export actual salvo política expresamente revisada después. |
| Pruebas futuras | PX28; regresión9/33/10 y bigint/long, preview sin mutar, conflicto desde preview. |
| Criterio de aceptación | Importación válida conserva semántica declarada o rechaza explícito; no pierde documento nuevo por preview antiguo. |
| Riesgo | X3 sólo demuestra parser concreto; no borrar datos para probarlo. No obligatorio para chat. |
| Prioridad de tarea | P1 |

### B10 — UML avanzado y exportación Spring con compilación real

| Campo | Plan futuro |
|---|---|
| Objetivo | UML avanzado y exportación Spring con compilación real |
| Requisitos/funciones | RT06; F02/F24, opcional |
| Archivos existentes NB | backend/modelado/models.py/serializers y generador/views.py; referencia DB/diagramas/spring_generator.py. |
| Archivos nuevos potenciales, NO CREADOS | Potenciales adaptador UML/JPA y exportador Spring en generador/services; PROPUESTOS. |
| Modelos afectados/propuestos | Justificar kinds/métodos/whole/JPA que hoy faltan antes de esquema; conservar IDs/ORM NB. |
| Servicios/reglas | DTO canónico a normalize_diagram/generate_spring_boot_zip adaptados; exportación, no backend sustituto. |
| HTTP: existente/extensión/propuesta | PROPUESTO endpoint ZIP; método/nombre final por decidir; paquete_base NB como entrada validada. |
| Eventos WebSocket | No evento de mutación si sólo exporta; error de elemento estructurado para U08. |
| Dependencias | B02; B05 no es requisito de exportación; F02/F03 y semántica/JPA acordada; U08. |
| Comportamiento esperado | Generar capas sólo para documento generable; class/interface/entity con tratamiento explícito. |
| Validaciones | Nombres/rutas/ZIP, identidad JPA, relaciones/whole y tipos; compilación no inferida de texto. |
| Seguridad/permisos | Permiso exportación explícito NB; sin credenciales reales en ZIP/config. |
| Pruebas futuras | PX29; compilar y ejecutar en toolchain aislado futuro con dependencias autorizadas. |
| Criterio de aceptación | ZIP seguro y proyecto representativo compila/arranca/pruebas CRUD pasan; si no, no certificar generador. |
| Riesgo | JPA incorrecto y dependencia/versiones; no copiar Maven/Spring como reemplazo de Django. |
| Prioridad de tarea | P2 |

### B11 — Lifecycle de proyectos y compatibilidad de invitaciones

| Campo | Plan futuro |
|---|---|
| Objetivo | Lifecycle de proyectos y compatibilidad de invitaciones |
| Requisitos/funciones | RT08; F25/F31, opcional fuera de accesos básicos |
| Archivos existentes NB | backend/modelado/views.py,serializers.py,usuario/models.py; referencia proyectos/views.py/services.py del donante. |
| Archivos nuevos potenciales, NO CREADOS | Potencial servicio de proyectos propio; PROPUESTO; enlace firmado puede completarse sólo en Angular si backend suficiente. |
| Modelos afectados/propuestos | Justificar archivo/restore/copia/roles nuevos por separado; no archivar por nombre histórico del donante. |
| Servicios/reglas | Duplicación privada, restauración sin heredar miembros, invariantes de propietario; firma de invitación existente. |
| HTTP: existente/extensión/propuesta | EXTENDER acciones sólo si se aprueban; no reemplazar rutas actuales por API donante. |
| Eventos WebSocket | Avisos de ciclo/membresía pasan B01/B03. |
| Dependencias | B01/B02 y U05/U09; no obligatorio introducir architect. |
| Comportamiento esperado | Proyecto restaurado/copiado respeta privacidad/nombres; enlace y aceptación interna siguen funcionando. |
| Validaciones | Unicidad/estado/propietario, copia sin permisos heredados y tokens expirados. |
| Seguridad/permisos | No permitir destino ajeno ni rol owner por invitación libre. |
| Pruebas futuras | PX31 y regresión de permisos/proyectos. |
| Criterio de aceptación | Flujos opcionales no cambian acceso/propiedad de proyectos existentes ni bloquean chat. |
| Riesgo | Copiar RunPython o trasladar estados entre modelos no equivalentes. |
| Prioridad de tarea | P2 |

B01 debe cerrar tanto PATCH metadata/JSON indebido como guardar_snapshot y nuevas entradas; no basta incorporar un decorator sólo al endpointIA. B02 debe utilizar datos validados, no reproducir la divergencia WSraw/validated_data del donante. Las decisiones de modelos nuevos se justifican por memoria/historial/planes hoy ausentes, no por semejanza de nombres.

B04/B06/B07 comparten un registro de conversación, no tres almacenes de mensajes. El contexto almacena referencias/corte/hash y eventualmente resumen, no otra autoridad de historial. B05 puede verificarse con fake sin instalar otro SDK. B08 no amplía a métodos/kinds no soportados por NB para cumplir una orden básica de creación de clase relacional; la ampliación F02/B10 es opcional.

## J. Plan técnico frontend

Rutas de whiteboard relativas a frontend/src/app/features/whiteboard; servicios en services, chat en components/chat-asistente-ia y página en pages/whiteboard. Todos los servicios/interfaces/componentes “potenciales” son propuestas. Se adapta el chat existente con Angular/DI/RxJS; no se copian JSX/hooks ni se introduce Zustand.

### U00 — Preservar Angular, sesión y editor; baseline de integración

| Campo | Plan futuro |
|---|---|
| Objetivo | Preservar Angular, sesión y editor; baseline de integración |
| Requisitos/funciones | AC01–AC04,AC22; RT03 |
| Componentes existentes/propuestos | app.routes.ts/app.config.ts; layouts y features/auth; WhiteboardPage, canvas, menús, dashboard/shared. |
| Servicios | AuthService, TokenStorage/JWT interceptor, ProjectsService y servicios JointJS existentes. |
| Interfaces/DTOs propuestos | Conservar DTOs actuales; distinguir transporte/error y revisión que extenderá U01. |
| Contrato HTTP | EXISTENTES /api/usuario/*, /api/modelado/proyectos/*, GET diagrama y XML/imagen. |
| Eventos WS | EXISTENTE /ws/pizarra/{id}/; no añadir React/hook como segundo cliente. |
| Estado | Token/usuario actuales, proyecto activo, viewport/selección; no nuevas credenciales. |
| Comportamiento esperado | Primer parcial y entradas actuales conservados; mocks de backend realistas y contrato centralizado. |
| Dependencias | B00; acceso/pertenencia acordadosB01. |
| Errores/recuperación | 401/token expirado debe resolver sesión explícitamente; no sólo presencia de string; 403 no reintenta como conflicto. |
| Pruebas futuras | PX01,PX02,PX03,PX27; tests Angular en versión declarada. |
| Criterio de aceptación | Login/dashboard/editor mantienen rutas, gestos, atributos, XML e imagen conectados; sin React/Zustand ni segundo chat. |
| Riesgo | Cambiar ruta/API por copiar donante, perder lockfile o duplicar subscripciones. |
| Prioridad de tarea | P0 |

### U01 — Estado autoritativo, autosave y reconexión

| Campo | Plan futuro |
|---|---|
| Objetivo | Estado autoritativo, autosave y reconexión |
| Requisitos/funciones | AC03–AC04,AC20; F06/F07 |
| Componentes existentes/propuestos | WhiteboardPage y componentes del editor; herramientas de estado/conexión existentes. |
| Servicios | WhiteboardApiService.reconciliarDatosDiagrama, WhiteboardSocketService, Canvas/Entity/Relationship/Camera. |
| Interfaces/DTOs propuestos | Documento/revisión/remapeos y eventos identificados; interfaces EXTENDIDAS, nombres finales por acordar. |
| Contrato HTTP | GET diagrama con revisión, PATCH escritor extendido y lecturas de recuperación. |
| Eventos WS | guardar_snapshot/snapshot_guardado EXTENDIDOS; diagram.updated/resync propuestos, transición coordinada K. |
| Estado | Una revisión aplicada; guardado pendiente con generación/proyecto; estado reconectando/sin conexión/conflicto. |
| Comportamiento esperado | Invalidar autosave viejo, aplicar ack/documento normalizado y remapeos una vez; recuperar al reconectar. |
| Dependencias | B01/B02/B03; no inferir semántica de primera asociación ni resucitar relación ausente en ORM. |
| Errores/recuperación | 409 conserva cambio local como intento rechazado, ofrece recargar/reinterpretar; nada de rebase silencioso. Desconectado no simula éxito. |
| Pruebas futuras | PX03,PX16,PX18,PX20,PX22,PX23 y R3a/R3b. |
| Criterio de aceptación | Tras tres clientes y reconexión todos comparten revisión/estado; eco y respuesta atrasada no pisan selección/estado nuevo. |
| Riesgo | Aplicar evento doble, error de remapeo o reenviar snapshot perdido sobre revisión nueva. |
| Prioridad de tarea | P0 |

### U02 — Un solo chat compartido con identidad e historial

| Campo | Plan futuro |
|---|---|
| Objetivo | Un solo chat compartido con identidad e historial |
| Requisitos/funciones | AC05–AC11,AC13,AC21; F16/F18 |
| Componentes existentes/propuestos | ChatAsistenteIaComponent existente y WhiteboardPage; UI de participantes/mensajes adaptada, sin duplicar panel. |
| Servicios | AsistenteIaService + potencial servicio ConversacionService Angular PROPUESTO, conectado al mismo chat. |
| Interfaces/DTOs propuestos | MensajeDTO, SolicitudDTO y cursor/estado propuestos; actor,reply_to,destinatario,ID servidor y key de intento. |
| Contrato HTTP | PROPUESTOS enviar pregunta/GET historial/estado; no enviar historia/actor como autoridad. |
| Eventos WS | chat.message.created/chat.request.status propuestos y replay al reconectar. |
| Estado | Mapa por message_id + orden servidor, pending por client_request_id; páginas/cursor y requests en curso por proyecto. |
| Comportamiento esperado | Mostrar nombre real de quien pregunta y a quién responde IA; todos ven la misma conversación, recargable. |
| Dependencias | B03/B04; respuestasB07; mínimo transporte/historia puede probarse antes con fixtures/fake. |
| Errores/recuperación | 202 es pendiente, no respuesta; timeout/502 muestra estado canónico y permite retry misma key; salir proyecto cancela subscripción local. |
| Pruebas futuras | PX04–PX08,PX18–PX21,PX25. |
| Criterio de aceptación | HTTP/WS/replay de un mensaje no generan filas duplicadas; tres sesiones ven IDs/actor/reply iguales; cambio de proyecto limpia contexto local. |
| Riesgo | Mostrar siempre Tú/Asistente sin identidad, asignar respuesta al último emisor o mezclar proyecto anterior. |
| Prioridad de tarea | P0 |

### U03 — Preview, confirmar/cancelar planes y errores localizables

| Campo | Plan futuro |
|---|---|
| Objetivo | Preview, confirmar/cancelar planes y errores localizables |
| Requisitos/funciones | AC17–AC20; F10/F11/F12/F26 |
| Componentes existentes/propuestos | Chat actual, WhiteboardPage y modales/controles Angular reutilizables. |
| Servicios | AsistenteIaService, WhiteboardSocketService/U01 y ToastNotificationService/camera. |
| Interfaces/DTOs propuestos | PlanDTO/resultado/errores, base_revision/plan_id/TTL/request_id propuestos; tipos validados en runtime. |
| Contrato HTTP | PROPUESTOS interpretar/aplicar/cancelar; cliente no envía operations como fuente de ejecución. |
| Eventos WS | Estado de plan y documento autoritativo tras commit; dedupe ID/revisión en U01. |
| Estado | Estados interpretando, aclaración, pendiente, confirmando, aplicado, cancelado, expirado, conflicto/error. |
| Comportamiento esperado | Enseñar resumen de cambios, confirmación explícita y resultado persistido; invalidar autosaves antes de aplicar. |
| Dependencias | B08, U01/U02; política todo cambio IA requiere confirmar como control técnico mínimo. |
| Errores/recuperación | 400 muestra campo/elemento;403 bloquea aplicar;409 exige nuevo plan;410/expirado invalida preview; retry conserva misma key. |
| Pruebas futuras | PX13–PX18,PX22,PX23,PX26. |
| Criterio de aceptación | Cancelar/consulta no cambia diagrama; confirmar muestra éxito sólo tras respuesta canónica; perdido el response recupera resultado sin duplicar. |
| Riesgo | Confirmar plan distinto al visto, doble click con otra key o autosave viejo después de aplicar. |
| Prioridad de tarea | P0 |

### U04 — Presentar asesoría/contexto sin confundir con cambios

| Campo | Plan futuro |
|---|---|
| Objetivo | Presentar asesoría/contexto sin confundir con cambios |
| Requisitos/funciones | AC09–AC16,AC22; F17/F19/F20 |
| Componentes existentes/propuestos | Chat actual y controles de selección/contexto del editor; mensajes/indicadores Angular existentes. |
| Servicios | AsistenteIaService/ConversacionService propuesto, selección de Canvas; no almacenar memoria sólo en navegador. |
| Interfaces/DTOs propuestos | Answer/proposal/error y metadata de revisión/fuentes/estado propuestos; no clave ni prompt sistema. |
| Contrato HTTP | Consulta/mensaje propuestos con texto/selección; respuesta dirigida y plan separado si lo hay. |
| Eventos WS | Eventos de mensaje/estado, sin ejecutar delta por recibir texto de asesoría. |
| Estado | Conversación compartida con actor y reply_to; indicador de respuesta basada en revisión anterior cuando corresponda. |
| Comportamiento esperado | Explicar consejo/solicitar aclaración; cambio de diseño sólo entra a U03. Memoria grupal/individual se reconstruye en backend. |
| Dependencias | B06/B07 y gatesV17/V20; U02/U01. |
| Errores/recuperación | No presentar respuesta de fake/HTTP200 como calidad validada; fallos/timeout muestran estado sin perder pregunta. |
| Pruebas futuras | PX08–PX12,PX19,PX24,PX26. |
| Criterio de aceptación | Consejo y propuesta se distinguen visualmente; identidad/seguimientos sobreviven recarga y no provocan escritura automática. |
| Riesgo | Dar por entendido un seguimiento sin fuentes o tratar consejo como instrucción aprobada. |
| Prioridad de tarea | P0 |

### U05 — Acceso de colaboradores y enlace firmado existente

| Campo | Plan futuro |
|---|---|
| Objetivo | Acceso de colaboradores y enlace firmado existente |
| Requisitos/funciones | AC05,AC19; RT01/RT08 |
| Componentes existentes/propuestos | ModalColaboradores, Header/dashboard notificaciones, app.routes.ts; futura página para /invitacion/:token si se aprueba. |
| Servicios | WhiteboardApiService, InvitacionesService, AuthService; potencial método de aceptar token en servicio existente. |
| Interfaces/DTOs propuestos | Roles NB actuales, membresía/canal retirado y respuesta de firma; no confundir colaborador_id con usuario_id. |
| Contrato HTTP | EXISTENTES invitar/colaboradores/invitaciones y aceptar-invitacion; ampliar ruta UI, no inventar backend ya disponible. |
| Eventos WS | access.revoked propuesto; cerrar pizarra/chat y no seguir reproduciendo buffers. |
| Estado | Permisos derivados de servidor; membresía inválida elimina acceso/estado; pendientes dashboard conservados. |
| Comportamiento esperado | Lectores pueden preguntar sin editar; retirada se explica; enlace firmado conduce a aceptación segura. |
| Dependencias | B01/B03; enlaceF31 puede ir después del núcleo porque aceptación interna existe. |
| Errores/recuperación | 403/retirado cierra subscripción y UI; token expirado/incorrecto informa sin aceptar; 401 no consume token erróneamente. |
| Pruebas futuras | PX17,PX22,PX25,PX31. |
| Criterio de aceptación | No simular autorización por controles ocultos; aceptación por dashboard no regresa; completar enlace no altera /activar/:token. |
| Riesgo | Revocar sólo una pestaña/diálogo; mostrar datos tras cierre o aceptar token de otro contexto. |
| Prioridad de tarea | P0 |

### U06 — Voz final y TTS opcionales en el chat existente

| Campo | Plan futuro |
|---|---|
| Objetivo | Voz final y TTS opcionales en el chat existente |
| Requisitos/funciones | RT07; F14/F15 |
| Componentes existentes/propuestos | ChatAsistenteIaComponent, botones/espacio y preferencias opcionales. |
| Servicios | AsistenteIaService reconocimiento y potencial servicio TTS Angular; adaptar utilidades aiFlow/dianaVoice, no JSX. |
| Interfaces/DTOs propuestos | Transcript final y estado de captura/confirmación; misma key de solicitud que texto. |
| Contrato HTTP | Misma entrada de mensajes/plan, sin endpoint IA paralelo para voz. |
| Eventos WS | Mismos mensajes/planes del chat; voz no aplica cambios por sí sola. |
| Estado | Capturando/final/esperando/confirmación; pausar escucha al sintetizar y respetar preferencia. |
| Comportamiento esperado | Texto siempre disponible; no enviar provisionales ni convertir ruido en confirmación. |
| Dependencias | U02/U03 para confirmar; B07/B08 existentes. No obligatorio para examen. |
| Errores/recuperación | Permiso micrófono denegado/voz no disponible da fallback; no bucle TTS/reconocimiento. |
| Pruebas futuras | PX30; utilidades y navegador autorizado sin atribuir offline. |
| Criterio de aceptación | Una transcripción final genera como máximo un intento; TTS optativo no lee sin preferencia ni duplica chat. |
| Riesgo | Matiz wake/send del donante, disponibilidad de navegador y feedback acústico. |
| Prioridad de tarea | P2 |

### U07 — Preview/importación XMI y conservación del perfil NB

| Campo | Plan futuro |
|---|---|
| Objetivo | Preview/importación XMI y conservación del perfil NB |
| Requisitos/funciones | RT05; F21/F22/F23 |
| Componentes existentes/propuestos | Sidebar/WhiteboardPage y GeneradorService; diálogo preview Angular propuesto. |
| Servicios | GeneradorService y U01; no importar componentes React. |
| Interfaces/DTOs propuestos | Preview/report/selección, xmi_ids y expected_revision, DTOs PROPUESTOS. |
| Contrato HTTP | EXISTENTES importar-xml/exportar-xml; EXTENSIÓN de preview/final por acordarB09. |
| Eventos WS | Preview sin cambios; final respuesta/diagrama por U01. |
| Estado | Archivo/selección/revisión base, warnings y confirmación; abortar preview al cambiar proyecto. |
| Comportamiento esperado | No sustituir automáticamente XMI NB; advertir pérdida no soportada y rechazar éxito vacío inesperado. |
| Dependencias | B09/V23, U01; resolverX3 antes de incorporar parser. |
| Errores/recuperación | Parseo/límites/roles/conflicto de revisión visibles; no cerrar error como importación exitosa. |
| Pruebas futuras | PX28; fixture conocida y recarga/replay. |
| Criterio de aceptación | Usuario confirma exactamente preview compatible con misma revisión; final inválido no altera documento. |
| Riesgo | Preview viejo reemplaza estado nuevo; counts no prueban semántica/layout. |
| Prioridad de tarea | P1 |

### U08 — UML avanzado y exportación Spring opcionales

| Campo | Plan futuro |
|---|---|
| Objetivo | UML avanzado y exportación Spring opcionales |
| Requisitos/funciones | RT06; F02/F24 |
| Componentes existentes/propuestos | EditorInline/menús/modales/WhiteboardPage/sidebar Angular. |
| Servicios | Entity/Relationship/Parser/GeneradorService; adaptador Angular para kinds/errores de generador. |
| Interfaces/DTOs propuestos | Kinds/métodos/ownership/JPA sólo tras diseño y persistenciaB10; ZIP/error DTO. |
| Contrato HTTP | PROPUESTO exportador ZIP; editor/guardado EXTENDIDOS si se amplía UML. |
| Eventos WS | Sólo documento validado/revisado U01; exportar no cambia diagrama. |
| Estado | Tipos explícitos y errores enfocados por ID NB; descarga ZIP y warnings. |
| Comportamiento esperado | No inferir JPA por arrastre o etiqueta; mostrar posibilidad de generar sólo si contrato lo permite. |
| Dependencias | B10/U01 y semántica acordada; no React Flow, no nuevo framework. |
| Errores/recuperación | Modelo no generable explica elementos; descarga fallida no simula compilación. |
| Pruebas futuras | PX29 y pruebas de editor/tipos/endpoints tras aprobación. |
| Criterio de aceptación | Tipos y relaciones guardan sin pérdida; error localiza elemento; compilación demostrada fuera del cliente antes de anunciar capacidad. |
| Riesgo | Ofrecer controles que ORM no persiste, invertir whole/part o llamar compilado al ZIP. |
| Prioridad de tarea | P2 |

### U09 — Mejoras de gestión y decisiones opcionales separadas

| Campo | Plan futuro |
|---|---|
| Objetivo | Mejoras de gestión y decisiones opcionales separadas |
| Requisitos/funciones | RT08; F25/F08/F09 |
| Componentes existentes/propuestos | Dashboard/ProjectsListPage/modales y controles actuales; diálogos Angular nuevos sólo si se justifican. |
| Servicios | ProjectsService/WhiteboardApiService; Undo/locks únicamente después deV08/V09. |
| Interfaces/DTOs propuestos | Acciones de proyecto y permisos extendidos; inversas/lease aún no diseñados. |
| Contrato HTTP | EXISTENTES proyectos; PROPUESTAS acciones lifecycle sólo trasB11. |
| Eventos WS | Avisos de lifecycle; no tratar lock visual existente como exclusión fuerte. |
| Estado | Archivo/duplicado/restauración y selección; undo/lease no habilitados hasta evidencia. |
| Comportamiento esperado | Mejoras no bloquean requisito conversacional ni cambian privacidad de copias. |
| Dependencias | B11 para lifecycle; V08/V09 para considerar locks/undo. |
| Errores/recuperación | Conflictos/nombres/roles deben informarse sin clonar miembros accidentalmente. |
| Pruebas futuras | PX31 y pruebas específicas futuras V08/V09. |
| Criterio de aceptación | Proyecto copiado/restaurado respeta política; opcionales sin evidencia permanecen deshabilitados/pendientes. |
| Riesgo | Introducir snapshots de undo que borren trabajo remoto o bloqueos sin expiración. |
| Prioridad de tarea | P2 |

Los estados de UI deben distinguir pregunta aceptada, respuesta pendiente, propuesta que no se aplicó, confirmación en curso y resultado persistido. Un HTTP202 no es una respuesta del modelo; un HTTP200 de lectura no autoriza mutación; un evento de propuesta no ejecuta delta. El editor mantiene viewport/selección cuando sea seguro y nunca reaplica una revisión anterior por una respuesta tardía.

La memoria recuperable reside en backend. El estado local sólo indexa mensajes/revisión/cursores de ese proyecto. Salir, perder acceso o cambiar proyecto elimina sus subscripciones/buffers activos; no se mezclan respuestas de una pizarra anterior. El nombre Tú puede ser complemento para sesión propia, pero el mensaje compartido siempre conserva nombre/ID del participante.

## K. Contratos de integración

Los nombres de operaciones y tipos nuevos de evento son **PROPUESTOS** para discutir en el gate de contratos. No son endpoints registrados actualmente. Se especifican responsabilidades/métodos/campos semánticos suficientes para implementar; URI exacta, nombres JSON y versión final se acuerdan antes de cambiar cliente/servidor. No crear aquí rutas o OpenAPI.

| ID / estado | Responsabilidad / método o evento | Entrada semántica | Salida semántica | Autenticación/permisos | Validaciones/errores | Estado Angular / compatibilidad |
|---|---|---|---|---|---|---|
| K00 CONTRATO EXISTENTE | JWT /api/usuario/{login,logout,token/refresh,...}/; proyectos/invitaciones y GET diagrama actuales | Credenciales/token o acción actual | Usuario/tokens/datos según serializers vigentes | JWT/miembro, con corrección B01 | Rechazo credenciales/token/pertenencia; no introducir cookies de sesión donante | Conservar AuthService/interceptor/rutas; refresh efectivo se verifica, no se infiere por existir endpoint |
| K01 CONTRATO A EXTENDER | GET /api/modelado/proyectos/{id}/diagrama/ | Proyecto autorizado | Documento ORM+proyección visual y revisión autoritativa; remapeos cuando apliquen | Miembro activo/propietario | Proyecto inaccesible no devuelve contenido; normalización sin R3 | WhiteboardApiService aplica datos canónicos; campos adicionales compatibles en lectura |
| K02 CONTRATO A EXTENDER | guardar_snapshot WS y escrituras REST del agregado | Proyecto, expected_revision y documento/lote NB permitido; key de intento donde corresponda | Resultado aplicado/no cambio, revisión y documento/remapeos validados; conflicto estructurado | JWT handshake + autorización vigente por operación | Tipos/IDs/cardinalidades/extremos/rol;400malformado,403sinpermiso,409basevieja; rollback sin evento | Invalida autosave viejo. PATCH metadata no es bypass para datos_diagrama; las escrituras documentales deben pasar por writer común |
| K03 CONTRATO NUEVO PROPUESTO | POST enviar_mensaje para consulta/solicitud del chat | Proyecto,texto,client_request_id,reply_to/selección opcionales validados | Pregunta canónica,message_id/actor/secuencia y request/status aceptado; respuesta posterior | Miembro activo de cualquier rol para consulta; no acepta identidad libre | Tamaño/contexto mismo proyecto, key+fingerprint; key repetida distinto contenido409; sin raw/proveedor | Optimismo reconciliado por key/ID;202indica pendiente. No rompe entrada texto actual: la reemplaza coordinadamente dentro del mismo chat |
| K04 CONTRATO NUEVO PROPUESTO | GET listar_historial/estado | Proyecto,cursor/límite y solicitud autorizada | Página de mensajes/orden/reply_to/actor, cursor/cabeza y estados persistidos | Miembro vigente; no resultados de otro proyecto | Cursor/límite válidos, autorización cada lectura;401/403segúnpolítica | U02 dedupe por ID y recupera tras reload/reconnect; PlanIA no es la fuente |
| K05 CONTRATO NUEVO PROPUESTO | POST interpretar_plan | Proyecto,instrucción/selección y revisión esperada,key; autor derivado servidor | Aclaración o plan persistido inmutable,resumen,base_revision/hash/TTL; ninguna mutación | Acceso+permiso de solicitar modificación según rol; consulta de lector porK03/answer | Allowlist/salida/proyecto/revisión; rechazar propuesta de contexto obsoleto, no refrescar base después del proveedor | U03 preview/confirmar/cancelar; no enviar lote del cliente como autoridad |
| K06 CONTRATO NUEVO PROPUESTO | POST aplicar_plan | plan_id,confirmación,expected_revision,key del intento; no operations editables | Resultado persistido/revisión aplicada/documento canónico o estado ya aplicado; identidad del evento | Acceso vigente y dueño del plan; para aplicación nueva, rol de escritura vigente | TTL/hash/estado/base; conflictos409, expiración código a acordar; exact retry devuelve resultado existente sin reaplicar | U03 usa la misma key ante respuesta perdida; si resultado aplicado viejo, U01 no restaura sobre revisión nueva: recarga estado actual |
| K07 CONTRATO NUEVO PROPUESTO | POST cancelar_plan | plan_id y key/estado esperado | Cancelado si pendiente; ya aplicado informa resultado; nunca revierte aplicación | Autor y miembro autorizado | Transición atómica; confirmar vs cancelar concurrentes sólo una gana; error de estado no se disfraza éxito | CancelarUI y abortarHTTP no sustituyen cancelar servidor; no aplicación posterior de plan cancelado |
| K08 CONTRATO A EXTENDER/NUEVO PROPUESTO | WS diagram.updated/presence.updated/access.revoked, adaptando wrapper actual | Heartbeat/acciones del cliente sólo permitidas por protocolo; no actor libre | event_id,proyecto,tipo,revision/estado/presencia y documento cuando corresponda | JWT+miembro en handshake/operación/entrega según política; corte al revocar | Tipo/tamaño/rol/canal; evento de documento sólo tras commit, sin payload a no miembro | Mismo socket Angular por proyecto o multiplexado diseñado; filtro revisión/generación/evento; retry con backoff y resync |
| K09 CONTRATO NUEVO PROPUESTO | WS chat.message.created/chat.request.status | Servidor publica mensaje/estado durable | Mismo message_id/sequence/reply_to/actor/status queK03/K04 | Sólo miembros vigentes del proyecto | Publicación tras commit; error sanitizado; evento no concede permisos ni escribe documento | Upsert porID, cursor/detección de gaps y recuperación porGET; duplicación de red tolerada, no promesa exactamente una entrega |
| K10 CONTRATO A EXTENDER OPCIONAL | XML importar-xml/exportar-xml existentes; preview/final futuro | archivo_xml/contenido_xml actual; preview/selección/revisión propuestos | Reporte/preview sin escritura; final documento/revisión/metricas compatible | Política NB actual revisada, sin adoptar architect automáticamente | Perfil/límites/referencias; X3 veto, preview obsoleto 409 | GeneradorService preservado; diálogo Angular nuevo sólo conB09 |
| K11 CONTRATO NUEVO PROPUESTO OPCIONAL | Exportar ZIP Spring | Proyecto/opciones limitadas aprobadas | ZIP y warnings o errores de elementos | Permiso explícito propio NB, no inferido de DC | Modelo generable, nombres/rutas/ownership/tipos; no garantía de compilación por descarga | U08 descarga/enfoque error; no modifica diagrama ni sustituye backend |

### Reglas transversales del protocolo propuesto

1. Backend deriva autor; proveedor recibe identidad de participante mínima autorizada, no credenciales. reply_to/destinatario se fijan desde la pregunta. El contexto individual se filtra por actor dentro del proyecto compartido.
2. Toda escritura documental usa el mismo writer y revisión. Interpretar conserva exactamente revisión/contexto usados. Si el documento cambia durante proveedor, se rechaza propuesta o se marca obsoleta y requiere nueva interpretación; no rebase silencioso.
3. Una aplicación nueva autoriza rol y revisión bajo lock. Un retry exacto ya aplicado primero verifica acceso/propiedad y fingerprint, devuelve el resultado de ese intento sin volver a comparar la revisión inicial como si fuera una aplicación nueva. Resultado antiguo no pisa el documento actual. Miembro retirado no obtiene resultado/historial por cache.
4. Unicidad durable se define para intentos de mensajes y aplicación en su ámbito actor/proyecto/plan; índice no basta. Misma key/diferente contenido es conflicto; nueva key permite otra instrucción legítima igual. No confundir una única mutación con una única publicación de red o una sola llamada física al proveedor tras timeout.
5. Fallo de publicación después de commit se recupera mediante historial/cursor/cabeza/resync. No hay garantía exactly-once. La estrategia de sondeo/resync periódico y su frecuencia se acuerda y prueba; reconexión sola no recupera un evento perdido en una conexión aparentemente viva.
6. El worker propuesto reclama solicitud con lease/estado en transacción corta y llama proveedor fuera del lock. Una respuesta canónica por solicitud y reanudación tras fallo son obligatorias; implementación del worker/arranque se decide antes de B07, sin imponer dependencia nueva.
7. Lecturas pueden ampliar DTO con campos. Escritura vieja sin expected_revision no se acepta silenciosamente: transición coordinada backend/Angular, error claro/recarga para clientes anteriores y compatibilidad de lectura. No dejar una ruta antigua que pueda pisar el agregado.
8. Los formatos/nombres de error/expiry/cursor/versión quedan por concretar en contratos antes de código. Las responsabilidades, permisos, precondiciones y garantías anteriores son el acuerdo de diseño propuesto, no contratos implementados.

## L. Problemas técnicos y riesgos

| Hallazgo | Evidencia y categoría conservada | Resolución futura seleccionada | Dependencia/validación; no corrección ahora |
|---|---|---|---|
| H-N01/H-N02 autorización NB | PATCH de visualizador persistió metadata/snapshot; rutina snapshot de visualizador/retirado borró entidades en BD aislada | B01 política por acción, B02 writer común y cierre de bypass JSON | PX17/PX22/PX25 cubren REST/WS/rol/revocación; no se declara handshake ofensivo probado |
| H-N03 snapshot anterior | Pérdida secuencial persistida reproducida en rutina real | B02 revisión obligatoria/atomicidad, U01 conflicto/resync | PX23 prueba dos bases y rollback; PG/multiworker futuros, no inferir carrera real actual |
| R3 reconciliación | Método Angular extraído reintroduce relación44 de snapshot y asigna intermedia9 a primera asociación2 | U01 elimina inferencia semántica; backend devuelve autoridad y snapshot sólo geometría válida | Reproducir método/carga real en tests antes de cambiar; no afirmar persistencia perdida por R3 |
| S3 revocación donante | Handlers reales no close y update posterior simulado; cliente honesto se autoexpulsa | B01/B03 revalidación/cierre/group_discard de todos los canales y permiso de historial | PX22 red/Redis aislados distingue barrera de revocación y tráfico previo; riesgo de escucha posterior, no exploit completo certificado |
| H2-D01 plan rebased | Fake cambia revisión durante interpretación, plan ligado a revisión nueva pese a contexto viejo | B08 conserva base inmutable o rechaza; nunca copiar refresh_revision después de proveedor | PX23 se reproduce en destino antes de corregir algoritmo; cliente conservando base0 podía rechazar |
| H-D03 retry / duplicación | Retry misma revisión0 tras aplicación1 devuelve409; índices no unique y publicar resultado no significa entrega única | K06 respuesta del intento ya aplicado, constraints/dedupe por nivel, U01 filtro estado viejo | PX18/PX23 comprueban respuesta perdida y concurrencia sin duplicar mutación |
| WS DCraw/validated_data | Diferencia de flujo por inspección; documento normalizado distinto persistido no reproducido | B02 sólo persiste datos normalizados comunes; no copiar raw-path | Antes de afirmar caso de pérdida reproducir equivalencia con fixtures locales; tratar efecto como riesgo potencial |
| X3 XMI | Fixture con9clasificadores →0nodes/0edges/errors[]; _attr no reconoce namespace antiguo | Conservar XMI NB; B09 fusiona límites/preview sólo tras perfiles y rechazo de vacío inesperado | PX28/V23; no reemplazo real ejecutado. XMI avanzado no necesario para conversación documentada |
| Bigint/importación | NB comprueba int antes de bigint/long; pérdida de tipo reproducida; XMLconteos no certifica semántica | B02 valida tipos y B09 regresión XML, conservar perfil | F03/PX28; importación actual debe delegar writer aunque preview sea opcional |
| I3 invitación | Backendgenera /invitacion/token; Angular no tiene ruta; dashboardacepta por otra cadena | U05 completa conexión propia después de controles; no migrar invitaciones completas | PX31; no correo real enviado, no todo sistema de invitación roto |
| H-D04 legacy | ClaseUML heredada movida a diagrama ajeno por PATCH en prueba | Excluir API/modelos legacy como fuente de persistencia NB | No trasladar superficie; comprobar destino de toda FK en B01/B02 |
| Dependencias/entorno | Django5.2vs6.1, genai ausente DC, drivers/redis diferentes; suites incompletas | B00 entorno fiel y B05 adaptador actual; no fusionar requirements | Pruebas futuras aisladas, sin instalaciones en esta fase |
| Seguridad de configuración | Defaults permisivos NB/transporte fijo, origen WS DC no validador explícito; inspección, no servidor expuesto probado | B00/B01 transporte/orígenes/credenciales de entorno objetivo, no del donante por copia | PX27 entorno aislado; no tocar AWS/despliegue existente |
| Incertidumbre semántica | No proveedor/voz/EA/Java reales verificados | V17/V20 y gates opcionales específicos; ninguna garantía inventada | No presentar fake/conteos/ZIPtexto como prueba de contenido/dispositivo/compilación |

El corte de revocación debe especificar qué evento fue producido/enviado antes o después del commit de retiro. Datos ya transmitidos antes de la barrera no se pueden retirar retroactivamente; la aceptación requiere impedir nuevos envíos/lecturas/operaciones tras esa barrera, incluyendo sockets que sólo escuchan. No se propone afirmar que basta con expirar presencia o esconder controles.

## M. Plan incremental de implementación

**Etapas futuras, no fases de auditoría ejecutadas ni autorización para comenzar.** Los números S0–S8 representan secuencia lógica. Sólo se avanza con evidencia del gate; el orden de notas no reemplaza dependencias. Los cambios se entregan en cortes verticales pequeños con tests, nunca una migración masiva de DC.

| Etapa | Objetivo y funciones | Backend | Frontend | Dependencias | Pruebas/gate y criterio de aceptación | Resultado y condición para continuar |
|---|---|---|---|---|---|---|
| S0 Acuerdo y baseline | Preservar F01/F04/F21/F28; confirmar alcance/procedencia y contratos | B00, definición B01/K; V00 obtener/contrastar fuente académica cuando disponible | U00, fixtures de contratos y UX existentes | Autorización expresa futura; no perder trabajo sucio | PX01/PX02/PX27 y regresión base; fuente o limitación de procedencia documentada y aceptada como alcance | Baseline reproducible/entorno fiel. Diferencia de fuente redefine plan afectado antes de prometer cobertura, sin bloquear pruebas técnicas no dependientes |
| S1 Acceso seguro | F05; controles imprescindibles de F26/F27 | B01, incluido cierre/retiro de grupos que reutilizará B03 | U00/U05 acceso/roles/cierre | S0 | PX17/PX22/PX25/PX27; visualizador consulta pero no escribe, retirado no recibe ni usa REST | Permisos comunes antes de nuevas entradas; ningún camino de escritura inseguro se deja como excepción |
| S2 Documento y sincronía | F03/F06/F07, recuperar baseline XML/imagen | B02/B03; adaptar importación/imagen como escritores, sin preview nuevo | U01 y regresiónU00 | S1; contrato de revisión K | PX03/PX16/PX20/PX23/PX26 y regresiones H-N03/R3 | Un documento/revisión autoritativos, sin snapshot viejo; permite ampliar conversación sin trasladar inconsistencias |
| S3 Mensajes e historial | F16/F18 y configuraciónF32 | B04 y B05; publicaciónB03 | U02 mensajes/cursor/actor e historial | S2; contrato K03/K04/K09 | PX04/PX05/PX07/PX18/PX20/PX21/PX25 con fixtures/fake; actor/IDs/orden iguales | Tres usuarios comparten y recuperan mensajes; aún no declarar memoria o inteligencia por transportar respuestas |
| S4 Resolver memoria NE | F13/F17 (V17), contexto por actor | B06, contrato de causalidad de solicitudes y fuentes | U04/parteU02 para identidad/referencias/estado | S3 y revisiónS2 | PX09/PX10/PX11/PX19/PX21 con corpus versionado; memoria se reconstruye y fuentes/actor correctos | V17 produce diseño y pruebas; no cerrar AC10–AC13 si sólo hay array o resumen de diagrama |
| S5 Asesoría sólo lectura | F19/F20 (V20), orquestación de respuestas y fallos | B07 sobre B04/B05/B06; V20 rúbrica/trabajador y recovery | U02/U04 respuestas, pendiente/error y consejo | S4 para asesoría contextual; transporteB07 puede prototiparse con fake trasS3 | PX06/PX08/PX12/PX19/PX24/PX26/PX27 y evaluación semántica autorizada; cero escritura de consultas | Un asesor compartido atribuido, calidad documentada; fake permite gate técnico pero no cerrar comprensión/moderación real |
| S6 Mutaciones confirmadas | F10/F11/F12 y seguridad de planes | B08, writerB02/publicaciónB03 | U03/U01 | S2,S5 contexto; K05–K07 y policyroles | PX13–PX18/PX22/PX23/PX26, carreras y response perdido; plan/revisión/actor inmutables | Lote válido aplica una vez y sincroniza; cancelado/obsoleto/no autorizado no escribe |
| S7 Aceptación completa | Verificar AC01–AC22 y gates obligatorios, ampliar F27/F26; completar F31 recomendado | B00/B01/B04–B08 verificación conjunta; soporte de invitación existente en B01 (B11 permanece opcional S8) | U00–U05, enlace firmado cuando se apruebe, foco/accesibilidad | S1–S6 y V17/V20; procedencia V00 visible | PX01–PX27; subsetPX31 para enlace si se incorpora; matrizQ sin requisitos obligatorios abiertos ni qualityfake presentada como real | Evidencia de requisitos documentados, regresión primer parcial y riesgos residuales aceptados; no garantía de nota |
| S8 Opcionales separados | F02/F14/F15/F22/F24/F25; V08/V09/V23/V29 | B09/B10/B11 según selección posterior; no cambio masivo de auth/datos | U06–U09 según capacidad | Núcleo aceptado; aprobaciones y gates propios | PX28–PX31 y verificaciones NEopcionales; no instalar ni activar para aparentar cumplimiento básico | Cada opcional se acepta por separado; no condiciona el cierre del mínimo ni desaparece del inventario |

La definición de contratos/pruebas ocurre antes de la tarea de producto correspondiente. El backend y frontend pueden avanzar en paralelo sobre fixtures acordadas de una misma etapa; no empezar todos los módulos simultáneamente ni depender de un API inventado. B00/pruebas mínimas se repiten al cambiar alcance, no se posponen hasta F27. Si V17 o V20 no alcanzan evidencia de contenido, se entrega avance técnico y se mantiene la brecha académica abierta; no se etiqueta como requisito cumplido.

Los cortes parciales están delimitados: S1 integra cierre/retiro por B01 sin exigir la presencia/resync completos de B03; S3 implementa el estado/mensajes/historial de U02 con fixtures antes de respuestas reales de B07; S4 acuerda el contrato/corpus de U04 y S5 completa su asesoría. No se declara una tarea entera terminada por haber entregado sólo su corte inicial. B09/B10/B11 no son prerequisitos generales de memoria/chat. La importación/imagen existentes sí deben pasar por writer/revisión enS2 para no dejar un bypass, aun si el preview o generación avanzada se postergan. F30 es exclusión decidida enS0, no una tarea a implementar.

## N. Estrategia de pruebas

### Escenarios propuestos, no ejecutados en esta fase

Se cubren los 27escenarios solicitados por la instrucción y cuatro adicionales de integración opcional. Se identifica nivel, precondición, acción, resultado, dependencias y evidencia. “Académico documentado” remite al maestro, nunca a una fuente primaria del docente no disponible. Varias pruebas técnicas apoyan un mismo requisito y no añaden puntos/funciones al inventario.

| ID/escenario | Procedencia/naturaleza | Precondiciones | Acción | Resultado esperado | Nivel | Dependencias | Evidencia requerida |
|---|---|---|---|---|---|---|---|
| PX01 Tres sesiones independientes | Académico documentado + controles técnicos | Tres User/miembros de prueba; navegadores/perfiles distintos y tokens propios. | Autenticar A/B/C sin compartir almacenamiento de sesión. | Cada sesión muestra su actor; token de otra sesión no sustituye identidad. | Integración + aceptación | B00/B01,U00 | Registro de tres sesiones/IDs y capturas; sin tokens en evidencias. |
| PX02 Mismo proyecto compartido | Académico documentado + controles técnicos | A propietario, B editor, C visualizador activos y proyecto ajenoD. | Abrir la misma pizarra por A/B/C. | Mismo documento/proyecto; D no aparece como accesible. | Integración + aceptación | B01/B02,U00/U01 | IDs/revisión/documento y respuestas de acceso; fixtures reproducibles. |
| PX03 Sincronización del tablero | Académico documentado + controles técnicos | PX02 y WS/Redis aislados; revisiónr. | A mueve/edita entidad y B recibe el cambio. | Todos convergen al documento persistido/revisiónr+1; sin evento de transacción fallida. | Integración multiworker | B02/B03,U01 | Snapshot servidor/cliente, revisiones y traza commit/evento. |
| PX04 Enviar pregunta al chat | Académico documentado + controles técnicos | A/B/C dentro del proyecto; B04 y fake proveedor. | B envía texto con key estable. | Una pregunta canónica actorB, estado aceptado/pending; no escribe diagrama. | Unidad + integración | B04/B07,U02 | Respuesta HTTP, fila de mensaje y revisión antes/después. |
| PX05 Difundir pregunta | Académico documentado + controles técnicos | PX04, tres sockets activos. | Publicar mensaje persistido y simular entrega repetida/replay. | Los tres ven un mismo ID/texto/actor en orden; no filas duplicadas. | Integración + aceptación | B03/B04,U02 | Payloads por sesión y UI; secuencia/cursor iguales. |
| PX06 Respuesta para todo equipo | Académico documentado + controles técnicos | PreguntaB persistida; fake responde. | Trabajador termina y publica tras commit. | Respuesta única con reply_to preguntaB visible a A/B/C e historial. | Unidad + integración | B04/B07,U02 | Resultado fake identificado como tal, filas y eventos ligados. |
| PX07 Atribución de actor | Control técnico de AC08 | B autenticado; cliente intenta actor_id=A. | Enviar petición maliciosa con identidad ajena. | Se ignora/rechaza campo; actor canónico y contexto siguenB. | Seguridad + unidad | B01/B04/B06,U02 | Aserciones de actor servidor/serializador; sin proveedor real. |
| PX08 Respuesta dirigida correcta | Académico documentado + controles técnicos | Preguntas de A y B, ambas registradas. | Procesar respuestas con retrasos controlados. | Cada respuesta conserva autor de pregunta/destinatario; texto/etiqueta nombra al correspondiente. | Integración + evaluación de contenido | B06/B07,U02/U04 | IDs/reply_to/recipient y revisión humana de contenido; fake sólo comprueba vínculo. |
| PX09 Memoria grupal | Académico documentado + controles técnicos | Acuerdo anterior compartido y hecho del diagrama en historial. | Otro integrante pregunta por ese acuerdo tras recarga. | Context builder recupera fuente/corte del proyecto; respuesta semántica respeta acuerdo o aclara conflicto. | Unidad + aceptación semántica | B06/B07,V17/V20,U04 | Contexto auditado por IDs y corpus/rúbrica; no declarar comprensión por fixture fake. |
| PX10 Memoria individual | Académico documentado + controles técnicos | A y B registran preferencias/hechos distintos dentro del grupo. | Cada uno hace seguimiento sin repetir su dato. | Se usa historial del actor correcto; no intercambia los datos individuales. | Unidad + evaluación semántica | B06/B07,V17,U04 | IDs seleccionados por actor y resultados de corpus tras recarga. |
| PX11 Seguimientos y turnos | Académico documentado + controles técnicos | Tres participantes y preguntas ambiguas/pronombres; memoria recargada. | Preguntar seguimiento corto y caso ambiguo. | Resuelve referente respaldado o pide aclaración; nunca atribuye certeza falsa. | Unidad + aceptación semántica | B06/B07,V17/V20 | Casos y rúbrica aprobada, fuentes/cutoff y revisión del evaluador. |
| PX12 Concepto sin mutación | Académico documentado + controles técnicos | Documento persistido/revisiónr; miembro lector activo. | Consultar concepto UML y recibir respuesta/sugerencia. | Sólo mensaje; ORM/documento/revisiónr intactos; lector puede preguntar; consejo no aplica delta. | Unidad + integración + semántica | B07,U02/U04 | Diff ORM/snapshot vacío y validación de contenido separada del fake. |
| PX13 Crear clase mediante solicitud | Académico documentado + controles técnicos | EditorB; dominio NB actual de entidades/clases relacionales. | Solicitar clase/entidad y procesar salida válida y ambigua. | Propuesta tipada sólo del dominio soportado; no muta antes de confirmar; ambigüedad pregunta. | Unidad + integración | B02/B08,U03 | Plan/operaciones validadas y estado previo sin cambios; corpus comandos. |
| PX14 Confirmar/cancelar | Académico documentado + controles técnicos | Plan propio pendiente con TTL/revisión/hash. | Mostrar preview, cancelar; otro plan confirmar explícitamente. | Cancelar no escribe; confirmar corresponde exactamente a plan visto. | Unidad + aceptación | B08,U03 | Estado/ID/hash del plan, UI y revisión; no audio necesario. |
| PX15 Aplicación autorizada | Académico documentado + controles técnicos | Plan vigente y permiso editor/propietario. | Confirmar una vez dentro de transacción; inyectar error en mitad de otro lote. | Primer lote aplica completo una vez; segundo rollback total, sin evento. | Unidad + integración PG | B01/B02/B08,U03 | Estado ORM/snapshot/revisión y conteo de commits/eventos. |
| PX16 Sincronizar cambio IA | Académico documentado + controles técnicos | PX15, tres clientes. | Recibir respuesta y evento en distinto orden/repetidos. | Documento final/revisión iguales; echo no duplica entidades ni revierte autosave. | Integración + aceptación | B03/B08,U01/U03 | Snapshots de A/B/C y trazas de dedupe/generación. |
| PX17 Rechazo por permisos | Control técnico y autorización de AC19 | Visualizador/ajeno/revocado; plan/datos de otro actor o proyecto. | Intentar PATCH/snapshot/plan/modificar referencias. | Rechazo sin escritura; preguntar como miembro lector activo sí permitido. | Seguridad + integración | B01/B02/B08,U03/U05 | Matriz de roles/transporte, códigos y cero cambios persistidos. |
| PX18 Duplicados de mensajes y operaciones | Control técnico de integridad | Key estable; respuesta perdida y concurrencia de retries. | Repetir pregunta, evento y confirmación; reutilizar key con payload distinto. | Un mensaje/resultado por intento; payload distinto conflicto; no reaplica plan ni publica nuevo hecho por replay. | Unidad + integración PG | B03/B04/B08,U01/U02/U03 | Constraints/filas/request keys, resultado original y revisión aplicada; no promesa exactly-once de red. |
| PX19 Consultas simultáneas | Académico documentado + controles técnicos | A y B envían al mismo proyecto; dos workers simulados y proyectoD. | Procesar cola por proyecto y retrasar proveedor de A. | Orden/causalidad definidos por backend; una respuesta por pregunta; D progresa independientemente. | Integración + seguridad | B04/B06/B07,U02 | Claim/lease, orden de solicitudes, fuentes de contexto y reply_to; sin mezcla de actor/proyecto. |
| PX20 Desconectar/reconectar | Académico documentado + controles técnicos | Mensaje/cambio persistido mientras cliente desconectado; cursor guardado. | Cortar WS, fallar publicación y reconectar/consultar cabeza/cursor. | Autoriza de nuevo, recupera documento y mensajes faltantes, sin replay de snapshot viejo. | Integración + aceptación | B03/B04,U01/U02 | Fallas de red simuladas, mensajes/revisiones finales y dedupe; nada en BD real. |
| PX21 Recuperación del historial | Académico documentado + controles técnicos | Varias páginas, respuestas y tres actores; reinicio/recarga cliente. | Consultar historial paginado y retomar conversación. | Sin pérdidas/duplicados; orden y vínculos estables; acceso vigente y contexto recuperable. | Unidad + integración + aceptación | B04/B06,U02/U04 | Cursores, IDs y contexto antes/después de reinicio. |
| PX22 Revocar acceso abierto | Control técnico de seguridad | B con dos pestañas/sockets; grupo y presencia reales aislados. | A retira B o baja rol; B intenta sólo escuchar, luego enviar/reconectar. | No se entregan mensajes producidos tras barrera de revocación; no escritura; sólo lectura activa permitida si rol aún miembro. | Seguridad multiworker | B01/B03/B04/B08,U01/U05 | Tiempo/barrera de revocación, group_discard/cierre y payloads; distinguir tráfico ya enviado. |
| PX23 Conflicto y carrera de revisión | Control técnico de integridad | Dos escritores esperanr y proveedor fake altera documento durante interpretación. | Guardar/aplicar/importar desde base vieja y repetir confirmación ya aplicada. | Nuevo escritor obsoleto409 sin mutar; plan no se reetiqueta r+1; retry mismo intento recupera resultado previo sin reaplicar. | Unidad + integración PG | B02/B08,U01/U03 | Regresiones H-N03/H2-D01/H-D03 con versiones y estado final. |
| PX24 Fallo de proveedor | Control técnico de disponibilidad | Fake timeout/5xx/mal JSON y trabajador interrumpido; ninguna clave real. | Procesar solicitud y reintentar con misma key. | Error/estado persistido visible, sin raw/secretos ni diagrama cambiado; recuperación sin varias respuestas canónicas. | Unidad + integración | B05/B07/B08,U02/U04 | Contador fake, estados/jobs/leases, mensajes y revisión. |
| PX25 Aislamiento entre proyectos | Control técnico de seguridad | A miembroP, ajenoQ; mensajes/planes/IDs existentes de Q. | Consultar historial, enviar/confirmar y suscribirse usando IDsQ. | Nada de Q entra a respuesta/evento/contexto; referencias rechazadas. | Seguridad + integración | B01/B02/B04/B06/B08,U02/U05 | Pruebas negativas por REST/WS/FK y captura del contexto fake. |
| PX26 Validación de salidas/instrucciones IA | Control técnico de seguridad | Proveedor fake genera listas mal tipadas, campos extra, IDs inexistentes y texto con instrucciones. | Enviar consultas y propuestas inválidas; simular lote parcialmente válido. | Rechazo/clarificación sin ejecución parcial; texto nunca se evalúa como código o privilegio. | Unidad + integración | B02/B05/B07/B08,U03/U04 | Contratos y cero cambios por payload malformado; límites/tipos/campos. |
| PX27 Protección de datos/configuración | Control técnico | Entorno de prueba sin .env real, mensajes/secretos sintéticos. | Revisar bundles/logs/eventos/errores y acceso con JWT inválido/origen no permitido. | Claves sólo backend, logging mínimo, identidad/contexto correctos; no fuga por raw/config/otro proyecto. | Seguridad + integración | B00/B01/B05/B07,U00/U02 | Búsqueda de canarios sintéticos y pruebas negativas, sin imprimir secretos reales. |
| PX28 XMI y preview | Opcional/RT05, no requisito del chat | Fixtures NB y perfiles acordados; fuente no vacía y revisiónr. | Parsear/preview; cambiar estado después; intentar confirmar; roundtrip compatible. | X3 no se acepta como vacío silencioso; preview no escribe; stale409; semántica soportada/tipos se conservan. | Unidad + integración + EA manual futuro | B09/U07,V23 | Conteos, grafos/roles/multiplicidades/layout, errores y captura EA autorizada. |
| PX29 UML avanzado y código generado | Opcional/RT06 | DTO semántico aprobado, toolchain/dependencias aisladas disponibles. | Generar ZIP de class/interface/entity y compilar/probar proyecto representativo. | ZIP sin traversal/secretos, semántica correcta y compilación/CRUD reales; error apunta al elemento. | Unidad + integración Java | B10/U08 | Logs javac/Maven y pruebas ejecutadas; texto ZIP por sí solo insuficiente. |
| PX30 Voz final/TTS | Opcional/RT07 | Preferencias/permiso navegador y utilidades aisladas; sin llamadas IA reales. | Provisionales/finales duplicados, denegar micrófono, TTS habilitado/deshabilitado. | Sólo final una vez; texto funciona; no feedback ni confirmación accidental. | Unidad + navegador autorizado | U06; B07/B08 con fake | Eventos SpeechRecognition simulados y evidencia manual de dispositivo cuando se autorice. |
| PX31 Invitación y lifecycle | Mejora técnica RT08 | Firma temporal y miembros de prueba; copia/restauración sólo si aprobadas. | Seguir enlace /invitacion/token, aceptar interno, expirar; duplicar/restaurar proyecto. | Ruta conecta o falla explícito; activar cuenta no se confunde; copia/restauración privadas y sin miembros heredados. | Unidad + integración + aceptación | B01/B11,U05/U09 | Pruebas token/rol/propiedad y UI; sin SMTP real ni datos existentes. |

### Rúbrica y entornos de prueba futuros

- Unitarias: validadores, permisos, operaciones, contexto por actor y estados de plan con proveedor fake; sin BD/red si no hace falta.
- Integración: PostgreSQL de prueba aislado para locks/constraints/concurrencia y Channels/Redis aislados para presencia/revocación/eventos; nunca bases existentes. Tres sesiones separadas, incluyendo lector activo y usuario ajeno a otro proyecto.
- Frontend: servicios/componentes Angular, HttpClient/WS simulados con escenarios de orden/repetición/conflicto; navegador para integración real, sin React y con fixtures del contrato implementado.
- Contenido: corpus versionado con preguntas, actor, acuerdos/hechos previos, fuentes, expectativa de seguimiento, respuestas aceptables y casos que exigen aclaración. Cada caso debe cumplir corrección UML, coherencia con contexto, atribución, distinción hecho/sugerencia y ausencia de modificación no autorizada. Todos los casos críticos de actor/aislamiento/cero escritura deben pasar, y cada caso semántico del corpus aprobado debe tener revisión humana motivada. Tamaño/cobertura y rúbrica se acuerdan enV17/V20 antes de declarar calidad.
- Un fake o respuesta guionizada demuestra selección de contexto/flujo, no comprensión real. Para cerrar semántica se requiere evaluación humana con respuestas de un proveedor/artefactos de ejecución autorizados y política de datos acordada; cualquier llamada real futura requiere autorización correspondiente. **No se realizan ahora llamadas reales ni se resuelve la incertidumbre forzando un proveedor.**
- Preservación: repetir regresiones válidas H-N01/02/03, H-D03, H2-D01, R3, S3 y X3 cuando se implementa su límite en destino. Algunas describen código donante que no se incorpora; se prueban como comportamiento a no heredar, no copiando su suite como si certificara NB.
- Artefactos: logs sin secretos, IDs/revisiones/cursores, resultados de tests y capturas de tres clientes; QA contiene estado anterior/posterior y evidencia de cero efectos donde corresponda.

### Verificaciones ejecutadas durante esta auditoría

No se ejecutaron pruebas de aplicación nuevas, proveedores, migraciones ni servicios. Se reutilizaron resultados F1–F4 cuya fuente sigue idéntica. Sólo se hicieron lecturas, búsquedas, inventario/hash/Git, extracción de tablas, comprobación aritmética y coherencia de referencias del plan.

| Verificación ejecutada | Resultado/límite |
|---|---|
| Get-Content UTF8 de attachment fase5; lecturas completas de los cinco documentos | Instrucción y textos consultados, con fuentes previas idénticas; no se ejecutan sus tareas. |
| Get-Item/Test-Path; git status/rev-parse/branch/remote/ls-files con -c safe.directory y --no-optional-locks | Raíces/origins/ramas/commits y destino ausente; sin modificar config. |
| rg --files --hidden -g AGENTS.md excluyendo dependencias/.git | Sin coincidencias de instrucciones adicionales dentro de raíces consultadas. |
| rg --files para parcial/docente/transcripción/mp3/wav/pdf/docx; rg -n Markdown/TXT sobre docente/segundo parcial fuera de informes/dependencias | Sin fuente primaria independiente localizada; exit1 de rg significa sin coincidencias, no evidencia de que no exista fuera del alcance. |
| PY -B T5/read_and_extract.py T5 | 1889archivos iniciales; inventarios F1–F4 de1885/1886/1887/1888sin diferencias. Extrae tablas directamente de AUDITORIA_FASE_4.md; el primer intento falló por sufijoNE, corregido en temporal. |
| PY -B T5/plan_data.py T5 | Datos de planificación/documentación sólo enT5; 26puestos numéricos,6NE,23capacidades,12tareas backend,10frontend y31escenarios futuros. |
| PY -B T5/render_report.py T5; PY -B T5/verify_plan.py T5 | Rangos/IDs/ranking+NE=todo inventario, métricas intactas, dependencias de ranking y tareas, trazabilidad, modelo local opcional, seccionesA–T y ausencia de contratos nuevos declarados existentes. |
| PY -B T5/create_report.py T5 | Modo exclusivo, comparación SHA/Git antes y después, único archivo nuevo AUDITORIA_FASE_5.md, lecturaUTF8 final. El resultado se añade al cierre. |

El directorio temporal exclusivo T5 es C:\Users\juan\AppData\Local\Temp\nodoboard-phase5-1abcc419473a49b09010660cca5f8e55. Contiene read_and_extract.py, baseline.json, initial-git.json, validity.json, phase4-extracted.json, phase4-alternatives.json, plan_data.py/plan-data.json, report-template.md y scripts/artefactos de render/validación/creación final. No se escribieron pruebas/modelos/componentes/configuración en los repositorios. -B evita bytecode; Git sólo se consulta en modo lectura con safe.directory por proceso.

Las suites anteriores mantienen límites: DB85con69pasan/1 fallo/15 erroresSQLite; NBsubset en versión distinta; DF 28 utilidades/lint/build, NB tsc pero build/Karma no finalizados; XMLconteos; Java no compilado; proveedor/voz/EA/Redis/PG reales no verificados. No se ejecutan para fabricar un punto o cerrar NE.

Se omitieron nuevas suites/builds y reproducciones de pérdida/revocación porque no cambió código ni aportan evidencia necesaria a esta planificación; las apps nuevas no existen. Se omiten IA real, audio, SMTP/OAuth y E2E sobre infraestructura existente por restricciones/sin aislamiento acreditado. La extracción inicialmente fallida por sufijoNE se corrigió sólo enT5; salida final y recuentos se validaron contra las tablas, sin tocar fase4.

## O. Distribución del trabajo

Propuesta para dos integrantes humanos en una implementación posterior; no se asignaron agentes ni se inició trabajo de producto. La responsabilidad principal no excluye revisión cruzada. Se divide por complejidad y gates, no por número de archivos.

| Etapa | Integrante1 — backend principal | Integrante2 — frontend principal | Trabajo compartido y equilibrio |
|---|---|---|---|
| S0/S1 | B00/B01: fixtures de identidad/roles, política por acción y pruebas negativas | U00/U05: baseline editor/auth y respuestas de acceso/cierre | Revisar contratos K, scope académico V00, reproducir H-N01/02 y aceptación de tres sesiones. Integrante2 prepara fixtures/clients de seguridad para reducir cuello backend |
| S2 | B02/B03: writer/revisión/atomicidad/presencia/revocar | U01: autosave/generaciones/remapeo/resync y tests RxJS | Acuerdo del documento autoritativo y errores409; integración en corte pequeño con PX03/PX23 antes de otros escritores |
| S3 | B04/B05: mensajes/historial/keys y adaptador fake | U02: un chat, actor, páginas/cursores, dedupe y reconexión | Esquema mensaje por ambos; frontend entrega fixtures de orden/red. Backend revisa que la UI no sea barrera de seguridad |
| S4/S5 | B06/B07: memoria/corpus, claim/lease, proveedor fuera de lock y moderación | U04/U02: consejo/respuesta/estado, identidad/seguimientos, tests de componentes | V17/V20 y revisión humana de corpus por ambos; Integrante2 puede liderar corpus/arnés de aceptación y casos de contexto, con revisión backend, no limitarse a JSX inexistente |
| S6 | B08: planes/allowlist/confirmar/cancelar/retry seguro | U03: preview/confirmación/errorfoco/estado autoritativo | Pruebas de carrera y respuesta perdida conjuntas; revisar basecontexto/roles y evitar rebase silencioso |
| S7 | Cerrar seguridad/integración y verificación fuente/backend | Cerrar navegador/UX/trazabilidad/demo y regresión Angular | Ambos ejecutan revisión de seguridad/QA y demostración, documentan limitaciones, no se aprueba un PR sólo porque el autor lo probó |
| S8 | B09/B10/B11 sólo para opcional autorizado | U06–U09 sólo para el mismo corte opcional | Una capacidad a la vez; no meter todos los módulos para equilibrar cantidad de archivos |

La memoria/orquestación es mayor carga conceptual que un diálogo UI; se compensa asignando a Integrante2 corpus, fixtures de contrato y harness de aceptación, y trabajo pareado en writer/concurrencia. No se requiere que ambos desarrollen simultáneamente cada etapa; los mocks acordados permiten avance frontend sin inventar contratos que el backend no pueda cumplir.

## P. Estrategia Git

**Sólo propuesta. No se ejecuta ningún comando de mutación Git en esta fase.**

1. Mantener NodoBoard como destino, los repos donantes como referencia. Antes de implementar, revisar con el usuario el cambio previo de frontend/package-lock.json y los informes/otros no rastreados. No incluirlos, descartarlos ni limpiarlos automáticamente.
2. La rama actual es feat/integrar-diagramcraft en df5430d…; no se asume que main contenga el mismo primer parcial. Identificar una base aceptada y su commit de regresión. Tras autorización, crear rama de integración propuesta (p.ej.feat/ia-colaborativa) desde esa base, con los cambios preexistentes tratados separadamente por su propietario.
3. Ramas por cortes funcionales propuestos: seguridad/revisión, chat-historial, contexto-asesoría, planes-confirmación y opcionales individuales. No ramas por archivo ni copia masiva de commits DC. Dos integrantes trabajan en checkouts/worktrees separados autorizados, con contratos pactados para reducir conflictos.
4. Commits pequeños por comportamiento verificable: regla+test, contrato+cliente, adaptación+regresión. Mensajes describen cambio/porqué; no mezclar actualización de dependencias, UI y datos sin razón. Cada cambio de esquema futuro lleva modelo justificado, compatibilidad y prueba de migración en copia aislada, nunca aplicado a una base existente sin autorización.
5. PRs hacia integración con requisitos AC/RT, tareas B/U, pruebas PX, evidencia y riesgos/compatibilidad. Revisión cruzada, pruebas antes de integrar y protección de rama principal/integración a configurar sólo con autorización; no presentar esa protección como ya existente.
6. Coordinar serializers/contratos, consumer/writer y servicios Angular como áreas de alto conflicto. Cambios de formato se acuerdan en K antes de editar; resolución de conflictos se revisa por ambos y se repiten tests afectados. Mantener API antigua de lectura compatible y transición controlada de escritura con revisión, sin bypass.
7. Regresión: revertir futuro commit/PR revisado o aplicar corrección hacia delante, según impacto. Nunca recomendar reset duro/limpiar workspace para ocultar fallos. Esquema y datos requieren backup/restauración ensayada y autorización propia; revertir código no equivale a revertir una migración con datos.
8. Cerrar cada etapa con evidencia y baseline recuperable; etiquetas/releases futuros sólo después de validación y autorización. Ninguna rama/tag/commit/push/PR se crea ahora; tampoco despliegue o cambio AWS.

## Q. Matriz final de trazabilidad

Las columnas obligatorias se conservan; la columna Decisión incorpora los IDsF para expresar **requisito→funcionalidad→decisión→B→U→prueba→aceptación** sin una tabla paralela sin enlaces. Los AC vienen de E; RT son controles/recomendaciones técnicas expresamente identificadas. La obligación primaria atribuida al docente sigue NO VERIFICADA donde sólo existe el maestro.

| Requisito | Procedencia | Obligatoriedad | Estado actual | Decisión | Tarea backend | Tarea frontend | Dependencia | Prueba | Criterio de aceptación |
|---|---|---|---|---|---|---|---|---|---|
| AC01 Sesión independiente por integrante | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/párrafo y R1 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | PARCIALMENTE CUMPLIDO — JWT/token propio; parcial | F04 CONSERVAR; F05 ADAPTAR; F07 ADAPTAR | B00,B01,B03 | U00,U01 | Identidad/pertenencia vigentes | PX01,PX02 | Tres sesiones distintas conservan actor y permisos correctos sin compartir tokens. |
| AC02 Dispositivos/ubicaciones distintas | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R1 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | PARCIALMENTE CUMPLIDO — Canales/URLs conectados; E2E pendiente | F04 CONSERVAR; F07 ADAPTAR | B00,B03 | U00,U01 | Infra aislada, URL/transporte de prueba | PX01,PX20 | Tres clientes en sesiones separadas se reconectan al mismo proyecto; no se presume prueba geográfica real. |
| AC03 Un mismo tablero compartido | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/párrafo inicial | Obligatorio documentado; atribución textual al docente NO VERIFICADA | PARCIALMENTE CUMPLIDO — Eventos/snapshot/ORM; defectos de revisión | F01 CONSERVAR; F06 ADAPTAR; F07 ADAPTAR | B02,B03 | U00,U01 | B01/B02 | PX02,PX03,PX23 | Estado normalizado y revisión iguales tras cambios/reconexión; preservar editor NB. |
| AC04 Sincroniza cambios autorizados | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R16-R17 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | PARCIALMENTE CUMPLIDO — Parcial y permisos/snapshot defectuosos | F05 ADAPTAR; F06 ADAPTAR; F07 ADAPTAR; F12 ADAPTAR | B01,B02,B03,B08 | U01,U03 | Writer común y permisos | PX15,PX16,PX17,PX23 | Sólo cambio confirmado/permitido persiste y todos convergen a su revisión; ningún evento antes de commit. |
| AC05 Todo integrante del proyecto puede consultar IA | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R3 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | PARCIALMENTE CUMPLIDO — Entrada autenticada local; sin canal grupal completo | F16 DESARROLLO NUEVO; F19 FUSIONAR | B01,B04,B07 | U02,U04 | Preguntar separado de editar | PX04,PX12,PX17 | Propietario/editor/visualizador activos pueden consultar; visualizador no modifica. |
| AC06 Pregunta visible para todos los miembros | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R2,R4 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | NO CUMPLIDO — Sólo mensajesChat local | F16 DESARROLLO NUEVO | B03,B04,B07 | U02 | Identidad/mensaje persistido | PX04,PX05 | Los tres ven el mismo message_id/actor/texto en orden, sin duplicado tras replay. |
| AC07 Respuesta visible para todo el proyecto | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R5 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | NO CUMPLIDO — Respuesta local | F16 DESARROLLO NUEVO; F18 DESARROLLO NUEVO | B03,B04,B07 | U02 | Pregunta/reply_to y acceso | PX06,PX18 | Una respuesta canónica vinculada a pregunta aparece en todos y en historial. |
| AC08 Identifica quién pregunta | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R6 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | PARCIALMENTE CUMPLIDO — Autenticación sin actor al proveedor | F16 DESARROLLO NUEVO | B01,B04,B06,B07 | U02 | request.user, nunca actor libre | PX07,PX25,PX27 | Actor del mensaje y del contexto deriva de sesión; falsificar actor_id no lo cambia. |
| AC09 Dirige respuesta al participante correcto | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R7 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | NO CUMPLIDO — Sin flujo atribuido conectado | F16 DESARROLLO NUEVO; F20 DESARROLLO NUEVO | B04,B06,B07 | U02,U04 | reply_to/recipient autorizados | PX08,PX19 | Respuesta identifica al autor de la pregunta incluso con dos peticiones simultáneas. |
| AC10 Contexto conversacional grupal | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R8 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | NO CUMPLIDO — Sólo contexto del diagrama | F17 DESARROLLO NUEVO | B04,B06,B07 | U02,U04 | V17 y registro persistido | PX09,PX19,PX21 | Seguimiento usa acuerdos anteriores de ese proyecto con referencias de origen y sin mezclar otro. |
| AC11 Contexto individual por participante | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R9 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | NO CUMPLIDO — No memoria por actor | F17 DESARROLLO NUEVO | B04,B06,B07 | U02,U04 | V17, actor servidor | PX10,PX11 | Recupera hechos del actor correcto dentro de conversación compartida, también tras recarga. |
| AC12 Comprende preguntas de seguimiento | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R10 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | NO VERIFICADO — No historia enviada; semántica no probada | F17 DESARROLLO NUEVO; F20 DESARROLLO NUEVO | B06,B07 | U02,U04 | Historial + evaluación de contenido | PX09,PX10,PX11 | Corpus de seguimientos pasa rúbrica acordada; un fake no acredita comprensión real. |
| AC13 Diferencia intervenciones de distintos participantes | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R11 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | NO CUMPLIDO — Sin hilo/actor contextual | F16 DESARROLLO NUEVO; F17 DESARROLLO NUEVO | B04,B06,B07 | U02,U04 | Actor y causalidad por request | PX07,PX10,PX19 | No asigna a B un dato/acuerdo personal de A; turno y respuesta conservan destinatario. |
| AC14 Responde dudas conceptuales sin cambiar diagrama | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R12; cero mutación es control técnico | Obligatorio documentado; atribución textual al docente NO VERIFICADA | PARCIALMENTE CUMPLIDO — Prompt + transporte fake sin delta, calidad no probada | F19 FUSIONAR | B07 | U02,U04 | Consulta separada de aplicar | PX12,PX26 | Consulta produce answer y ningún cambio de revisión/ORM; contenido pasa rúbrica, no sólo HTTP200. |
| AC15 Asesora en diseño UML y modera al equipo | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/propósito y R13 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | NO VERIFICADO — Intención conceptual; sin moderación de equipo | F20 DESARROLLO NUEVO | B06,B07 | U04 | V17/V20, contexto y política | PX09,PX12,PX26 | Distingue hechos/acuerdos de sugerencias, pide aclaración y fundamenta consejo en el modelo/contexto. |
| AC16 Recomienda mejoras del diagrama | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R14 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | NO VERIFICADO — Calidad/flujo de consejo no acreditados | F13 FUSIONAR; F20 DESARROLLO NUEVO | B06,B07 | U04 | Contexto de revisión y rúbrica | PX12,PX26 | Presenta recomendación referida a elementos reales y no la aplica automáticamente. |
| AC17 Solicita modificaciones mediante lenguaje natural | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R15 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | PARCIALMENTE CUMPLIDO — Deltas cliente conectados y débiles | F03 ADAPTAR; F10 ADAPTAR; F13 FUSIONAR | B02,B05,B08 | U03 | Reglas/contexto autorizado | PX13,PX26 | Instrucción válida obtiene propuesta tipada; salida malformada/ambigua se rechaza o aclara sin mutar. |
| AC18 Confirma operaciones cuando corresponde | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R16; exigir toda mutación IA es política técnica propuesta | Obligatorio documentado; atribución textual al docente NO VERIFICADA | NO CUMPLIDO — Aplicación inmediata tras éxito | F11 ADAPTAR | B08 | U03 | Misma revisión del contexto y rol vigente | PX14,PX15,PX23 | Cancelar no escribe; confirmar plan propio vigente persiste una vez; obsoleto requiere nueva interpretación. |
| AC19 Modifica respetando permisos | RECOMENDACIÓN TÉCNICA; desarrolla autorización de maestro §11/R16 | Condición de seguridad del proyecto; no cita textual académica | PARCIALMENTE CUMPLIDO — PATCH/snapshot indebidos reproducidos | F05 ADAPTAR; F11 ADAPTAR | B01,B02,B08 | U01,U03,U05 | Política por acción, no sólo UI | PX17,PX22,PX25 | Retirado/lector no escriben por ningún transporte ni FK; consulta de miembro activo permanece permitida. |
| AC20 Todos ven modificaciones autorizadas | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R17 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | PARCIALMENTE CUMPLIDO — Sync parcial, sin revisión | F06 ADAPTAR; F07 ADAPTAR; F12 ADAPTAR | B02,B03,B08 | U01,U03 | AC04 y replay | PX03,PX16,PX20 | Los tres convergen, eco no aplica dos veces y respuesta/evento atrasado no pisa revisión nueva. |
| AC21 Recupera historial conversacional | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R18 | Obligatorio documentado; atribución textual al docente NO VERIFICADA | NO CUMPLIDO — Sólo array volátil | F18 DESARROLLO NUEVO | B04 | U02 | Persistencia/orden/acceso | PX18,PX20,PX21 | Recargar y paginar conserva preguntas/respuestas/actor/reply_to en orden autorizado. |
| AC22 Configura proveedor IA de forma segura | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/R19; seguridad de claves es recomendación técnica | Configuración obligatoria documentada; proveedor concreto/multimarcas no impuestos | PARCIALMENTE CUMPLIDO — Key/modelo configurables, SDK declarado | F32 FUSIONAR | B00,B05 | U00,U04 | Configuración backend y fake | PX24,PX27 | Key sólo backend; modelo/config inválida da error controlado; sin secreto en bundle/eventos/logs. |
| AC23 Modelo local como mejora opcional | INTERPRETACIÓN DEL DOCUMENTO MAESTRO §11/Modelo local y orden expresa de fase5 | OPCIONAL | OPCIONAL — Sin adaptador LLM local | F29 INVESTIGAR | V29/B05 | U04 (sólo futuro) | Modelo/hardware/corpus aún no definidos | V29 | No bloquea núcleo ni exige sustituir Gemini; sólo integrar tras decisión y pruebas propias. |
| RT01 Autorización/revocación uniforme por proyecto | RECOMENDACIÓN TÉCNICA | Condición técnica del núcleo; no cita docente | PARCIALMENTE CUMPLIDO | F05 ADAPTAR; F07 ADAPTAR | B01,B03 | U01,U05 | Identidad/membresía y canales | PX17,PX22,PX25 | Tras barrera de revocación no se entregan nuevos datos ni se aceptan operaciones; todas las pestañas cubiertas. |
| RT02 Revisión, escritor común, reconciliación e idempotencia | RECOMENDACIÓN TÉCNICA | Condición técnica de integridad | PARCIALMENTE CUMPLIDO | F03 ADAPTAR; F06 ADAPTAR; F12 ADAPTAR | B02,B03,B08 | U01,U03 | RT01 y reglas de dominio | PX18,PX23,PX26 | Stale409/rollback sin efectos; retry no reaplica ni un eco restaura una revisión antigua. |
| RT03 Entorno destino/contratos/pruebas y regresión primer parcial | RECOMENDACIÓN TÉCNICA | Condición técnica para integrar | PARCIALMENTE CUMPLIDO | F01 CONSERVAR; F04 CONSERVAR; F27 ADAPTAR | B00 | U00 | Entorno aislado/versiones y baseline | PX01,PX02,PX03,PX27 | Regresiones existentes pasan o fallo localizado entendido; nuevas garantías se prueban en entorno fiel. |
| RT04 Errores, fallos de proveedor y protección de datos | RECOMENDACIÓN TÉCNICA | Condición técnica del núcleo | PARCIALMENTE CUMPLIDO | F26 FUSIONAR; F32 FUSIONAR | B05,B07,B08 | U02,U03,U04 | Contrato de error y estados durables | PX24,PX26,PX27 | Error controlado sin secretos/raw; pregunta/estado recuperables y consulta fallida no modifica documento. |
| RT05 XMI compatible/preview y EA real | RECOMENDACIÓN TÉCNICA | Mejora opcional; conservar flujo actual | OPCIONAL | F21 CONSERVAR; F22 FUSIONAR; F23 INVESTIGAR | B09,V23 | U07 | X3, B02 y perfil objetivo | PX28,V23 | No éxito vacío ante fixture conocida; semántica/perfil declarado probado y preview obsoleto rechazado. |
| RT06 UML avanzado y generación Spring por capas | RECOMENDACIÓN TÉCNICA | Mejora opcional, no requisito de chat | OPCIONAL | F02 ADAPTAR; F24 MIGRAR | B10 | U08 | Tipos/ownership/JPA y toolchain | PX29 | DTO sin pérdida y proyecto representativo compila/ejecuta tests; ZIP/texto no basta. |
| RT07 Voz final y TTS | RECOMENDACIÓN TÉCNICA | Mejora opcional, texto se conserva | OPCIONAL | F14 ADAPTAR; F15 ADAPTAR | Reutiliza B07/B08; sin endpoint nuevo de voz | U06 | Preferencia/navegador; plan si confirma | PX30 | Final una vez, fallback escrito y sin feedback/confirmación accidental; no offline inferido. |
| RT08 Enlace de invitación, lifecycle, locks/undo investigables | RECOMENDACIÓN TÉCNICA | Mejoras técnicas; básicos de acceso se conservan | PARCIALMENTE CUMPLIDO | F25 ADAPTAR; F31 ADAPTAR; F08 INVESTIGAR; F09 INVESTIGAR | B01,B11,V08,V09 | U05,U09 | Permisos/estado/copia privada y diseños opcionales | PX31,V08,V09 | Enlace correcto/no confunde activación; copia/restore no hereda miembros; lease/undo sólo tras pruebas propias. |

Todas las funcionesF del inventario tienen destino de tarea/conservación/investigación o exclusión en F; no se obliga a incluir opcionales en el mínimo. Las ocho filasRT no son nuevas funcionalidades puntuadas ni nuevos requisitos docentes. V00 requiere contrastar fuente académica si aparece; V17/V20 no se reemplazan por una nota NE→0 ni por una frase de “implementado”.

## R. Limitaciones y decisiones pendientes

| Decisión/verificación | Estado / evidencia faltante | ¿Bloquea? | Acción y autoridad futura |
|---|---|---|---|
| Procedencia académica V00 | Maestro formaliza; no audio/transcripción primaria localizada | Bloquea atribución textual y promesa de cobertura docente exacta; no bloquea controles técnicos ni alcance documentado | Solicitar/contrastar fuente cuando exista y acordar diferencias/alcance mínimo; no inventar citas ni pedir autorización para completar este informe |
| V17 memoria | Selección/recuperación/corte/causalidad y corpus sin evidencia semántica | Bloquea aceptar contexto/seguimiento, no mensajes/historial previos | B06 y corpusPX09–PX11/PX19/PX21; conservar F17NE |
| V20 moderación | Política/rúbrica/respuestas de calidad no evaluadas | Bloquea aceptación de asesoría/moderación real | B07, corpus/evaluación humana autorizada; fake sólo gate técnico, F20NE |
| V08/V09 locks/undo | Lease/inversas/perfil de conflicto por definir | Sólo bloquea opcional, no chat o revisión | Decisión de necesidad antes de escribir código; no introducir snapshotundo como seguro |
| V23 EA | Perfil/herramienta y vuelta manual ausentes | Sólo certificación/interoperabilidad opcional | B09/U07/PX28; conservar XMI actual y X3 como gate de adaptación |
| V29 local/otro proveedor | Motor/modelo/hardware/operación desconocidos | No bloquea configuración Gemini/R19 | Estudio opcional futuro; no instalar ni cambiar proveedor ahora |
| Roles mínimos | Tres roles NB; architect no existe | Bloquea aplicar permisos de donante sin mapa; no exige rol nuevo | Mantener propietario/editor/visualizador para mínimo; ampliar rol sólo por necesidad aprobada |
| Retención/límites de historial/contexto | Tamaños/cursor/paginación/tokenbudget y resumen largo por definir | Bloquea cerrar diseño de B04/B06 y pruebas; no inventar capacidad infinita | Acordar política verificable en contratos/corpus antes de implementación; historial durable no equivale a mandar todo al modelo |
| Concurrencia/worker | Semántica cola/lease/recovery y despliegue operativo por concretar | GateB07 antes de producción; no obliga instalar Celery | Trabajador Django propuesto con cola durable, transacción corta/lease y salida única; probar PGaislado |
| Dedupe/publicación | on_commit no entrega garantizada; retries pueden repetir llamada física al proveedor | Bloquea promesas exactly-once y controles insuficientes | Keys/fingerprint, canonicalmessages, recovery y replay; una respuesta visible/aplicación, no una entrega o llamada física garantizada |
| Infra y dependencias | NB5.2 vs entorno6.1, SDK/PG/Redis/audio/EA/Java/navegador sin prueba completa | Gate de las funcionalidades que lo requieran, no instalar durante auditoría | B00 y entornos aislados/versiones declaradas; ninguna BD/despliegue existente se altera |
| Contratos de K | URI/JSON/versiones/errores/cursor exactos propuestos, no registrados | Bloquea editar cliente/servidor sin acuerdo | Gate compartido antes de cada corte; mantener lectura compatible y negar escrituras inseguras antiguas |
| Configuración/proveedor real | Key/modelo parametrizables, disponibilidad/calidad no probadas | No bloquear fakes/infra; sí aceptar desempeño real sin evidencia | AdaptadorB05 y evaluación futura autorizada, no llamar proveedor para cerrar informe |
| Autorización de implementación | Esta ejecución sólo permite un Markdown | Bloquea toda modificación de producto/infra/datos/Git | Autorización expresa posterior del usuario; las etapas no son permiso implícito |

No se realizaron escáneres externos de vulnerabilidad ni consultas de soporte/precio de versiones; las observaciones son locales. R3/S3/X3 mantienen sus límites y no se promocionan a incidentes. La confianza ALTA de un defecto/estado no certifica portabilidad o seguridad futura. La ausencia de modelo de conversación no prueba incapacidad de conocimiento general de Gemini.

## S. Criterios de finalización del segundo parcial

**Se evalúa cobertura de los requisitos documentados, no se garantiza aprobación ni calificación.** Estado actual: las capacidades faltantes/NE no están terminadas; este plan no cuenta como implementación.

| Criterio objetivo de cierre propuesto | Evidencia requerida | Qué impide darlo por cerrado |
|---|---|---|
| Alcance/procedencia claros | E/Q con fuente, categoría y obligatoriedad; V00 documentada y diferencias tratadas si hay fuente primaria | Atribuir al docente un control técnico o esconder que sólo se dispone del maestro |
| Tres usuarios/sesiones sobre proyecto compartido | PX01–PX03 y matrices de roles; no tokens compartidos ni estado de otro proyecto | Sólo una captura local, socket simulado presentado como dos dispositivos |
| Preguntas/respuestas grupales atribuidas | PX04–PX08: mismos IDs/cursor/actor/reply_to en A/B/C, persistencia y destinatario correctos | Array local, PlanIA usado como historial o respuesta asignada al último usuario que escribió |
| Memoria grupal/individual/seguimiento | V17/PX09–PX11/PX19/PX21 con corpus versionado, fuentes/corte y contexto por actor tras recarga | Sólo resumen del diagrama, hecho truncado sin recuperación o mezclar actores; F17NE no resuelto |
| Asesoría/moderación conceptual | V20/corpus PX12/PX26 y revisión humana que acredita corrección UML, contexto, destinatario, aclaración y sugerencias explícitas | Fake/HTTP200 usado para demostrar inteligencia; recomendaciones aplicadas automáticamente; F20NE no resuelto |
| Cambios IA autorizados/confirmados | PX13–PX17/PX23/PX26: plan propio/TTL/revisión/contexto, confirmación, atomicidad, rechazo de inválido/obsoleto | Prompt/UI como única validación, rebase tras proveedor o bypass de snapshot/PATCH |
| Sincronización y recuperación | PX03/PX16/PX18/PX20: todos convergen a revisión y mensajes persistidos, retry no duplica | Eventoantescommit, respuesta atrasada restaurada, pérdida tras publicación fallida sin replay |
| Seguridad/aislamiento/revocación | PX17/PX22/PX25/PX27 en PG/Redis aislados con múltiples canales | Sólo esconder botón, cerrar cliente honesto o revalidar permiso sólo al escribir |
| Historial recuperable | PX21 páginas/orden/actor/pregunta-respuesta y permisos vigentes | Historial seis entradas o memoria del navegador presentada como persistencia |
| Proveedor configurable con errores seguros | B05/PX24/PX27; configbackend, fake y fallos con estados durables; evaluación de contenido separada | Claves en frontend/log/raw, SDK no acreditado o modelo local impuesto para cumplirR19 |
| Regresión del primer parcial | B00/U00 y tests editor/proyectos/XML/imagen/roles existentes, versión destino | Suprimir capacidad propia para incorporar un módulo donante; limpiar cambios previos para aparentar éxito |
| Trazabilidad y riesgos residuales | Q completo, evidencias de cada criterio/gate y pendientes/opcionales separados | Requisito obligatorio sin solución/prueba, NE obligatorio presentado como hecho o plan como permiso |

El modelo local, voz/TTS, UMLampliado, XMIavanzado/EA, Spring y lifecycle adicional no condicionan estos criterios del mínimo documentado. Mantener funcionalidad actual y su integridad sí es condición: no dejar importación/imagen/metadata como camino sin autorización/revisión si modifican el agregado. Las mejoras opcionales se aceptan con su evidencia propia, sin sumarlas como supuestos puntos del examen.

## T. Recomendación final

| Pregunta de cierre | Respuesta técnica |
|---|---|
| ¿Qué conservar? | Angular/Django/Postgres/Channels/Redis del destino, JWT/usuarios, editor JointJS/servicios/ORM, proyectos/invitaciones internas, un chat/entradas propias y XMIactual; F01/F04/F21/F28 más configuraciónF32 |
| ¿Qué aprovechar de DiagramCraft? | Validadores/allowlist, operaciones tipadas, patrón de revisión/planes/TTL/confirmación, contexto autorizado, errores/filtros de estado, presencia/retry y utilidades voz opcionales; corregir límites del donante antes de adaptar |
| ¿Qué no trasladar? | Diana íntegra, React/JSX/Zustand/ReactFlow, auth paralela, ORMlegacy/migraciones y archivos vacíos, parserXMI directo incompatible; F30/A01/A03/A04/A05 descartados como soluciones |
| ¿Qué desarrollar nuevo? | Mensajes/historial/actor/destinatarioF16/F18; memoria grupal/individual y seguimientoF17; política/flujo moderador-asesorF20; implementación concreta de servicios y modelos NB que materialicen esas capacidades |
| ¿Problemas previos? | H-N01/02/03 permisos/snapshots; R3 autoridad de reconciliación; S3 revocación al escuchar; no heredar H-D03/H2-D01 ni raw-path; X3gate sólo si se amplíaXMI |
| ¿Qué necesita Django? | B00–B08 como núcleo: acceso uniforme, writer/revisión, eventos/resync, conversación/historial, proveedor único, contexto, orquestador y planes; esquema propio justificado, sin copia de apps |
| ¿Qué necesita Angular? | U00–U05 como núcleo: conservar editor/auth, revisión/autosave/resync, chat compartido/actor/cursor, previewconfirmar y UX de asesoría/error; no otro framework |
| ¿Qué contratos? | Extender carga/guardado/revisión y protocolo actual; nuevos mensajes/historial/estado/planes y eventos propuestos K; aprobar formas exactas antes de código |
| ¿Qué dependencias? | Identidad→permisos→writer/revisión→resync; mensajes→historial→memoria→asesoría; contexto/reglas/revisión→plan→confirmación→sync. Opcionales no bloquean esos caminos |
| ¿Cómo repartir? | Integrante1 backend/seguridad/datos/IA, Integrante2 Angular/estado/UX; contratos/corpus/QA/E2E/revisión compartidos, apoyo de frontend en fixtures/aceptación para balancear complejidad |
| ¿Qué pruebas? | PX01–PX27 más regresiones/gates obligatorios y corpusV17/V20; PX28–PX31 sólo según opcional/recorrido. Evidencia de tres sesiones y PG/Redis aislados, no sólo mocks |
| ¿Orden recomendado? | S0baseline/contratos, S1acceso, S2documento/resync, S3chat/historia/config, S4memoria, S5asesoría, S6planesconfirmables, S7aceptación, S8opcionales |
| ¿Alcance mínimo? | Requisitos documentados AC01–AC22, preservando primer parcial y resolviendo NE obligatorios; sólo dominio UML actual para cambios. AC23local y RT opcionales fuera del mínimo, sujeto a fuente/evaluación docente |
| ¿Qué postergar? | V08/V09/V23/V29 y ampliaciones de voz/TTS/kinds/métodos/EA/Spring/lifecycle; no postergar controles necesarios de escrituras existentes |
| ¿Qué necesita autorización? | Toda implementación, nuevos archivos/modelos/migraciones/dependencias, ramas/commits/PRs, tocar bases/infra/despliegue y pruebas reales con proveedores/dispositivos. Esta entrega no las autoriza |
| ¿Qué exigió el docente? | No hay fuente primaria verificable para atribuir literalmente; el maestro es fuente formalizada y la seguridad/corrección son recomendaciones técnicas. Modelo local OPCIONAL por instrucción vigente |
| ¿Incertidumbres bloqueantes? | Memoria/moderaciónV17/V20, contratos/causalidad/roles y entorno de pruebas fiel; fuenteV00 para asegurar interpretación académica. No bloquear núcleo por opcionales NE |

La solución seleccionada evita migración masiva y mantiene la autoridad de NodoBoard. El ranking queda cerrado para esta evidencia, las cifras de fase4 se preservan, y las incertidumbres continúan visibles con tareas/gates. Ninguna etapa se comenzó.

**FASE 5 DE TRABAJO FINALIZADA — auditoría y planificación detenidas. No implementar, migrar, corregir, crear ramas ni continuar sin autorización expresa del usuario.**

### Verificación final de integridad y coherencia

El bloque siguiente se añade durante la creación exclusiva del informe. Contrasta los archivos existentes, commits/ramas/origins y el único nuevo archivo permitido. Las comprobaciones del plan no son pruebas funcionales de una aplicación implementada.


~~~text
D:\Informatica\8vo Semestre\sw1-2-2026\pizarra-colaborativa
Rama: feat/integrar-diagramcraft; HEAD: df5430d221ddfbdc23e0a7882e535dc402ceafc4
 M frontend/package-lock.json
?? AUDITORIA_FASE_1.md
?? AUDITORIA_FASE_2.md
?? AUDITORIA_FASE_3.md
?? AUDITORIA_FASE_4.md
?? AUDITORIA_FASE_5.md
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

Integridad SHA-256: 1889 archivos existentes comprobados; 0 diferencias. Ramas, commits, origins y cambios Git previos conservados: True. Único archivo nuevo autorizado: True.

Maestro y fases 1–4 preservados byte por byte. Inventarios anteriores de1885/1886/1887/1888 archivos siguen sin diferencias. La comprobación cubre archivos rastreados/no ignorados inventariados, no todos los ignorados de dependencias/entorno.

Coherencia: recuentos extraídos directamente de AUDITORIA_FASE_4.md;32funciones conservadas=26puestos numéricos+6NEseparados;6alternativas; todas las cifras/decisiones/prioridades sin cambios. SeccionesA–T,23capacidades académicas/8controles técnicos,12tareas backend/10frontend y31escenarios futuros trazados. No se consideran implementados ni verificados funcionalmente por aparecer en el plan.

No se modificó código, modelos/configuración/dependencias ni bases existentes; no instalaciones/migraciones/ramas/tags/commits/pushes/PRs/despliegues/AWS ni llamadas reales a proveedores IA. No se revirtieron cambios. Única adición persistente en repositorios: AUDITORIA_FASE_5.md. Auditoría y planificación finalizadas; implementación requiere autorización expresa.
