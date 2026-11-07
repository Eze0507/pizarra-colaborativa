# PROMPT MAESTRO PARA CODEX — Auditoría, comparación técnica, evaluación de IA y priorización de funcionalidades para migrar de DiagramCraft a NodoBoard

Actúa como arquitecto de software senior, analista de sistemas y desarrollador full-stack especializado en Django, Django REST Framework, Django Channels, Angular, React, PostgreSQL, Redis, WebSocket, inteligencia artificial, modelado UML, integración de sistemas, seguridad, pruebas automatizadas y migración de funcionalidades entre proyectos.

Tu responsabilidad es realizar una auditoría técnica exhaustiva, objetiva y verificable de DiagramCraft y NodoBoard para determinar qué funcionalidades, módulos, servicios, algoritmos, componentes, patrones arquitectónicos y capacidades existentes en DiagramCraft conviene trasladar, adaptar o integrar en NodoBoard.

**IMPORTANTE: En esta etapa solamente quiero comparar, evaluar, ejecutar pruebas no destructivas y elaborar un informe. No quiero implementar, modificar ni migrar código todavía.**

---

## 1. Objetivo principal y repositorios

### Proyecto principal y de destino: NodoBoard

Repositorio:

https://github.com/Eze0507/pizarra-colaborativa.git

### Identificación del proyecto y rutas

- **Nombre del proyecto:** NodoBoard.
- **Nombre mostrado en el workspace:** NodoBoard.
- **Nombre real de la carpeta:** `pizarra-colaborativa`.
- **Repositorio:** [https://github.com/Eze0507/pizarra-colaborativa.git](https://github.com/Eze0507/pizarra-colaborativa.git)

Todas las referencias a NodoBoard dentro de este documento corresponden al proyecto ubicado en la carpeta real `pizarra-colaborativa`.

Las rutas de archivos deben resolverse desde la raíz de esa carpeta.

Por ejemplo:

- Backend: `pizarra-colaborativa/backend/`
- Frontend: `pizarra-colaborativa/frontend/`
- Informe de auditoría: `pizarra-colaborativa/AUDITORIA_FASE_1.md`

Antes de utilizar cualquier ruta, verifica su existencia en el sistema de archivos. No supongas que el nombre mostrado en el workspace coincide con el nombre físico de la carpeta.

Tecnologías principales:
- Frontend: Angular.
- Backend: Django.
- Colaboración: WebSocket y Django Channels.
- Base de datos: PostgreSQL.
- Comunicación en tiempo real: Redis, según la configuración existente.
- Inteligencia artificial: asistente IA ya integrado.

### Proyecto de origen y referencia: DiagramCraft

Backend:

https://github.com/juanse8202/swbackend.git

Frontend:

https://github.com/juanse8202/swfrontend.git

Tecnologías principales:
- Frontend: React.
- Backend: Django.
- Colaboración: Django Channels y WebSocket.
- Base de datos: PostgreSQL.
- Inteligencia artificial: asistente Diana.
- Interacción por voz.
- Operaciones de modelado UML mediante IA.

### Regla principal

**NodoBoard debe conservar su arquitectura actual Angular + Django. DiagramCraft solamente servirá como fuente de funcionalidades que realmente aporten mejoras.**

No quiero convertir NodoBoard a React ni sustituir automáticamente su arquitectura, su backend, su frontend o su asistente de IA.

El objetivo es conservar las fortalezas de NodoBoard e identificar las capacidades de DiagramCraft que realmente merecen reutilizarse.

No asumas que DiagramCraft es superior en todas las funcionalidades.

---

## 2. Primera fase: auditoría integral de los tres repositorios

Inspecciona completamente los tres repositorios, su estructura, código, dependencias, arquitectura, seguridad, modelos, API, servicios, componentes, configuración y pruebas.

Analiza especialmente:

1. Gestión de usuarios, autenticación y permisos.
2. Gestión de proyectos y colaboradores.
3. Creación y edición de diagramas UML.
4. Creación, modificación y eliminación de clases, entidades y atributos.
5. Creación, actualización y eliminación de elementos.
6. Relaciones UML, cardinalidades y multiplicidades.
7. Importación y exportación XMI.
8. Generación de código, servicios y aplicaciones.
9. Colaboración en tiempo real mediante WebSocket.
10. Sincronización de diagramas entre usuarios.
11. Manejo de conflictos de edición y control de concurrencia.
12. Interacción mediante lenguaje natural.
13. Reconocimiento y síntesis de voz.
14. Asistentes de inteligencia artificial.
15. Interpretación y ejecución de instrucciones mediante IA.
16. Validación, confirmación y seguridad de operaciones.
17. Historial de conversaciones y gestión del contexto.
18. Persistencia de datos.
19. Arquitectura y organización del código.
20. Calidad, mantenibilidad y pruebas existentes.
21. Manejo de errores y respuestas.
22. Gestión del estado frontend.
23. Integración frontend/backend.
24. Seguridad de endpoints y WebSocket.
25. Configuración de proveedores de inteligencia artificial.

Para cada funcionalidad identifica:

- Archivos responsables.
- Clases y funciones relevantes.
- Endpoints involucrados.
- Modelos de datos.
- Dependencias.
- Estado de implementación.
- Pruebas existentes.
- Limitaciones conocidas.
- Posibles errores o riesgos.

**No consideres una funcionalidad implementada únicamente porque existe un archivo con su nombre. Inspecciona su comportamiento real, integración y pruebas.**

---

## 3. Segunda fase: comparación detallada de asistentes de inteligencia artificial

Esta sección es especialmente importante.

**NodoBoard ya tiene un asistente de inteligencia artificial. No quiero trasladar Diana automáticamente ni tener dos asistentes innecesarios.**

Compara detalladamente:

- IA existente de NodoBoard.
- Diana, asistente de DiagramCraft.

Determina:

1. Qué puede hacer actualmente cada asistente.
2. Qué modelos o proveedores utiliza cada uno.
3. Cómo interpretan instrucciones en lenguaje natural.
4. Cómo ejecutan operaciones sobre el diagrama.
5. Qué mecanismos utilizan para validar las instrucciones.
6. Cómo gestionan errores y respuestas.
7. Cómo procesan instrucciones de voz.
8. Si implementan reconocimiento y síntesis de voz.
9. Si mantienen historial o contexto conversacional.
10. Si reconocen al usuario que realiza una petición.
11. Qué tan integrados están con el modelador y la colaboración.
12. Cómo gestionan confirmaciones de operaciones.
13. Qué mecanismos de seguridad aplican.
14. Cómo separan las consultas conceptuales de las órdenes de modificación.
15. Qué capacidades de cada asistente son reutilizables.

### Preguntas que debes responder obligatoriamente

- ¿Es necesario trasladar Diana a NodoBoard?
- ¿Es mejor conservar la IA actual de NodoBoard?
- ¿Qué funcionalidades de Diana son superiores?
- ¿Qué funcionalidades del asistente de NodoBoard son superiores?
- ¿Podemos integrar las capacidades útiles de Diana dentro de la IA existente de NodoBoard sin reemplazarla?
- ¿Qué lógica, algoritmos o servicios de DiagramCraft conviene reutilizar?
- ¿Qué componentes serían redundantes?
- ¿Qué solución requiere menos cambios?
- ¿Qué alternativa presenta menor riesgo?
- ¿Qué alternativa tiene mejor integración y seguridad?
- ¿Cuál sería la solución más mantenible?
- ¿Es conveniente fusionar ambos enfoques?
- ¿Cuál permite cumplir mejor los requisitos del segundo parcial?

**Prioriza mejorar la IA existente de NodoBoard antes que reemplazarla por Diana, siempre que el análisis técnico lo justifique.**

No recomiendo introducir un segundo asistente si se pueden incorporar sus capacidades al asistente actual.

---

## 4. Tercera fase: comparación técnica del backend Django

### Backend de DiagramCraft

Analiza especialmente:

- `config/`
- `diagramas/`
- `proyectos/`
- `diagramas/ai_interpreter.py`
- `diagramas/ai_operations.py`
- `diagramas/ai_plans.py`
- `diagramas/consumers.py`
- `diagramas/realtime.py`
- `diagramas/models.py`
- `diagramas/views.py`
- `diagramas/tests.py`
- `diagramas/xmi.py`
- `diagramas/spring_generator.py`
- Autenticación y permisos.
- Configuración de Django Channels.
- Configuración de Redis.
- Configuración de PostgreSQL.
- Migraciones y dependencias.
- Skills y convenciones existentes del repositorio.

### Backend de NodoBoard

Analiza especialmente:

- `backend/asistente/`
- `backend/modelado/`
- `backend/generador/`
- `backend/usuario/`
- `backend/modelado/consumers.py`
- `backend/modelado/realtime.py`
- Modelos y serializers.
- Vistas y endpoints.
- Servicios de colaboración.
- Procesamiento de instrucciones IA.
- Sistema de generación de código.
- Importación y exportación XMI.
- Permisos y autenticación.

### Objetivo de la comparación backend

Identifica:

- Funcionalidades equivalentes.
- Funcionalidades exclusivas de DiagramCraft.
- Funcionalidades exclusivas de NodoBoard.
- Diferencias en la implementación.
- Código potencialmente reutilizable.
- Lógica que debe adaptarse.
- Posibles incompatibilidades entre modelos.
- Dependencias innecesarias.
- Riesgos de integración.
- Oportunidades de mejorar seguridad y mantenibilidad.

No propongas copiar migraciones, modelos, servicios o endpoints directamente sin verificar compatibilidad.

No dupliques funcionalidades existentes.

---

## 5. Cuarta fase: comparación técnica de frontend React y Angular

Compara los componentes React de DiagramCraft con los componentes Angular de NodoBoard.

### Frontend DiagramCraft

Analiza:

- `src/components/editor/DiagramCanvas.jsx`
- `src/components/voice/VoiceCommand.jsx`
- `src/hooks/useDiagramSocket.js`
- `src/api/aiApi.js`
- `src/utils/aiFlow.js`
- `src/utils/dianaVoice.js`
- `src/stores/`
- Componentes de colaboradores.
- Manejo de usuarios autenticados.
- Sincronización del estado.
- Pruebas existentes.

### Frontend NodoBoard

Analiza:

- `frontend/src/app/features/whiteboard/`
- Componentes del editor.
- Componente de chat con asistente IA.
- Servicios de IA.
- Servicios de WebSocket.
- Servicios de modelado.
- Gestión del estado.
- Autenticación.
- Componentes de colaboración.
- Servicios de importación/exportación.
- Pruebas existentes.

### Funcionalidades a comparar

- Editor visual.
- Herramientas de modelado.
- Chat con IA.
- Comandos de voz.
- Reconocimiento y síntesis de voz.
- Gestión de estado.
- Integración con backend.
- WebSocket.
- Interfaz de colaboración.
- Confirmación de operaciones.
- Manejo de errores.
- Actualización visual de diagramas.
- Sincronización entre participantes.
- Experiencia de usuario.

### Restricción

**No propongas copiar componentes React directamente a Angular.**

Determina qué comportamiento, patrones de interacción o lógica conviene reimplementar utilizando los servicios y componentes Angular existentes.

Conserva el frontend Angular de NodoBoard.

---

## 6. Quinta fase: pruebas y verificación del estado actual

Antes de recomendar cualquier migración, establece el estado actual de ambos proyectos.

Siempre que el entorno lo permita, ejecuta pruebas no destructivas.

### Backend

- Verifica dependencias.
- Ejecuta comprobaciones de Django.
- Ejecuta pruebas automatizadas.
- Verifica migraciones pendientes sin aplicar cambios.
- Comprueba módulos de autenticación.
- Comprueba colaboración.
- Comprueba endpoints de IA.
- Revisa validación y permisos.

### Frontend

- Verifica dependencias.
- Ejecuta las pruebas existentes.
- Ejecuta lint cuando esté configurado.
- Ejecuta compilación o build.
- Revisa errores de integración.
- Comprueba contratos con el backend.

### NodoBoard

- Ejecuta las pruebas disponibles de Angular y Django.
- Identifica componentes funcionales.
- Identifica fallos existentes.
- Verifica los mecanismos de colaboración.
- Examina el comportamiento de su asistente IA.

### DiagramCraft

- Ejecuta las pruebas disponibles de React y Django.
- Comprueba los servicios de IA.
- Verifica las pruebas del sistema de planes tipados.
- Examina las pruebas de colaboración.
- Revisa las utilidades de voz.

### Condiciones de ejecución

- No modifiques código para corregir fallos.
- No elimines volúmenes ni datos existentes.
- No ejecutes pruebas sobre bases de datos reales de producción.
- No instales dependencias innecesarias.
- Si una prueba requiere instalaciones, explica las necesidades y utiliza un entorno aislado cuando esté disponible.
- Registra comandos ejecutados.
- Registra resultados.
- Registra errores y pruebas omitidas.
- No declares pruebas exitosas si no llegaron a ejecutarse.
- Si alguna prueba no puede ejecutarse, explica la causa.

---

## 7. Sexta fase: matriz comparativa obligatoria

Construye una matriz comparativa detallada.

Para cada funcionalidad incluye:

| Campo | Descripción |
|---|---|
| Funcionalidad | Capacidad evaluada |
| DiagramCraft | Implementación existente |
| NodoBoard | Implementación existente |
| Mejor implementación | Proyecto con solución más conveniente |
| Evidencia | Archivos, funciones y pruebas |
| Dependencias | Componentes necesarios |
| Ventajas | Beneficios técnicos y funcionales |
| Limitaciones | Problemas o restricciones |
| Riesgos de integración | Posibles incompatibilidades |
| Decisión | CONSERVAR, MIGRAR, ADAPTAR, FUSIONAR, DESCARTAR o INVESTIGAR |
| Puntuación | Valor de 0 a 100 |
| Prioridad | P0, P1, P2 o P3 |

Clasifica cada funcionalidad utilizando estas decisiones:

### CONSERVAR
NodoBoard ya tiene una implementación adecuada que debe mantenerse.

### MIGRAR
DiagramCraft tiene una funcionalidad útil que falta en NodoBoard y que conviene incorporar.

### ADAPTAR
Conviene reutilizar parte de la lógica, algoritmos o comportamiento de DiagramCraft.

### FUSIONAR
Ambas implementaciones tienen ventajas complementarias y conviene combinarlas.

### DESCARTAR
No aporta suficiente valor, es innecesaria o genera duplicación.

### INVESTIGAR
No existe evidencia suficiente para tomar una decisión confiable.

Justifica cada decisión utilizando archivos, clases, funciones, endpoints y pruebas reales.

---

## 8. Séptima fase: sistema de puntuación ponderada

Evalúa cada funcionalidad candidata a migración utilizando criterios objetivos y cuantificables.

### Criterios de evaluación

| Criterio | Peso máximo |
|---|---:|
| Relevancia para el segundo parcial | 25 |
| Beneficio funcional frente a NodoBoard | 20 |
| Compatibilidad arquitectónica | 15 |
| Facilidad de integración | 15 |
| Calidad, seguridad y pruebas existentes | 10 |
| Mantenibilidad futura | 10 |
| Impacto positivo en la experiencia del usuario | 5 |
| **TOTAL** | **100** |

### Método de cálculo

Asigna a cada criterio una calificación entre 0 y 5.

Utiliza la siguiente fórmula:

**Puntuación final = Σ (calificación / 5 × peso del criterio)**

Redondea el resultado final a un decimal.

### Interpretación de resultados

- **85–100 puntos:** Muy recomendable para migrar o adaptar.
- **70–84,9 puntos:** Recomendable, sujeto a evaluación de dependencias.
- **50–69,9 puntos:** Prioridad condicionada; estudiar alternativas.
- **30–49,9 puntos:** Baja conveniencia.
- **0–29,9 puntos:** No recomendable en las condiciones actuales.

### Reglas de puntuación

1. La puntuación refleja conveniencia técnica, no obliga a migrar.
2. Una funcionalidad importante que NodoBoard ya resuelve correctamente puede recibir la decisión CONSERVAR.
3. Una funcionalidad con puntuación alta no necesariamente es obligatoria para el examen.
4. No asignes puntuaciones sin evidencia.
5. Si falta información, utiliza INVESTIGAR.
6. Registra cuáles criterios no pudieron verificarse.
7. Evita favorecer DiagramCraft solamente porque una funcionalidad tenga mayor complejidad técnica.
8. Considera el beneficio real frente al esfuerzo necesario.
9. Justifica cada calificación.
10. Diferencia características implementadas de características simplemente documentadas.

---

## 9. Octava fase: criterios de priorización

Clasifica todas las funcionalidades evaluadas utilizando cuatro niveles.

### P0 — CRÍTICA

Funcionalidad necesaria para cumplir el segundo parcial, resolver un bloqueo funcional o corregir un problema importante de seguridad.

Características:

- Imprescindible para cumplir requisitos obligatorios.
- Puede impedir el funcionamiento correcto del sistema.
- Tiene impacto directo sobre seguridad, integridad de datos o colaboración.
- Debe atenderse antes que mejoras opcionales.

### P1 — ALTA

Funcionalidad que proporciona mejoras importantes y cuya integración es viable.

Características:

- Aporta valor sustancial.
- Mejora capacidades relevantes.
- Tiene beneficios funcionales comprobables.
- Conviene implementarla después de resolver los bloqueos P0.

### P2 — MEDIA

Funcionalidad útil pero no indispensable para el examen.

Características:

- Aporta valor adicional.
- Puede mejorar experiencia o mantenibilidad.
- Su implementación puede postergarse.
- No bloquea requisitos principales.

### P3 — BAJA

Funcionalidad complementaria, redundante, costosa o poco relevante.

Características:

- No es necesaria para el segundo parcial.
- Tiene beneficio limitado.
- Puede generar duplicación.
- Presenta costes de integración elevados.
- Puede descartarse o implementarse posteriormente.

### Reglas obligatorias de priorización

1. Los requisitos obligatorios del docente tienen precedencia sobre funcionalidades opcionales.
2. Los problemas de seguridad y permisos pueden elevar la prioridad aunque la puntuación sea moderada.
3. Una puntuación alta no convierte automáticamente una función en P0.
4. Una funcionalidad con dependencias no resueltas no debe recomendarse como primera implementación.
5. Si NodoBoard ya cumple un requisito correctamente, prioriza conservarlo.
6. No propongas migrar funcionalidades con beneficio marginal y riesgo alto.
7. Considera dependencias técnicas entre funcionalidades.
8. Justifica por qué una funcionalidad debe implementarse antes que otra.
9. Distingue obligatoriedad académica de conveniencia técnica.
10. No confundas prioridad con facilidad de implementación.

---

## 10. Novena fase: evaluación de esfuerzo y riesgo

Para cada funcionalidad candidata estima el esfuerzo de integración y el riesgo técnico.

### Esfuerzo de integración

Utiliza la escala:

- **1:** Muy bajo.
- **2:** Bajo.
- **3:** Medio.
- **4:** Alto.
- **5:** Muy alto.

Considera:

- Cantidad de archivos afectados.
- Dependencias.
- Adaptaciones del backend.
- Adaptaciones del frontend.
- Diferencias React/Angular.
- Cambios en modelos.
- Cambios en contratos API.
- Necesidad de nuevas pruebas.
- Complejidad de integración.

### Riesgo técnico

Utiliza la escala:

- **1:** Muy bajo.
- **2:** Bajo.
- **3:** Moderado.
- **4:** Alto.
- **5:** Crítico.

Considera:

- Posibles regresiones.
- Problemas de compatibilidad.
- Cambios en migraciones.
- Seguridad.
- Permisos.
- Colaboración en tiempo real.
- Conflictos de actualización.
- Integridad de datos.
- Dependencias externas.
- Complejidad de mantenimiento.

### Confianza de la evaluación

Asigna una clasificación:

- **ALTA:** Código y pruebas suficientes para respaldar la conclusión.
- **MEDIA:** Evidencia parcial, pero técnicamente consistente.
- **BAJA:** Implementación no verificada o información insuficiente.

Explica las razones de cada estimación.

---

## 11. Décima fase: evaluación frente a los requisitos del segundo parcial

Considera el siguiente enunciado académico.

El segundo parcial consiste en ampliar el modelador UML existente incorporando una IA colaborativa que funcione como moderadora y asesora del equipo.

Cada integrante utiliza su propia sesión y puede encontrarse en una ubicación física diferente.

Todos comparten el mismo tablero y deben poder visualizar las preguntas y respuestas de la IA.

### Requisitos funcionales

1. Usuarios conectados desde diferentes dispositivos y sesiones.
2. Chat grupal visible para todos los colaboradores.
3. Cualquier integrante puede enviar preguntas a la IA.
4. Todos visualizan las preguntas.
5. Todos visualizan las respuestas.
6. La IA identifica al usuario que realiza cada pregunta.
7. La IA responde de forma individualizada mencionando al participante correspondiente.
8. La IA mantiene el contexto general del equipo.
9. La IA mantiene contexto individual por participante.
10. La IA comprende preguntas de seguimiento.
11. La IA distingue conversaciones individuales dentro del contexto grupal.
12. La IA resuelve dudas conceptuales.
13. La IA actúa como asesora del diseño UML.
14. La IA puede recomendar mejoras de diagramas.
15. La IA puede interpretar solicitudes de modificación del diagrama.
16. Las modificaciones requieren autorización cuando corresponde.
17. Los cambios autorizados se sincronizan entre colaboradores.
18. El historial puede conservarse y recuperarse.
19. El proveedor IA debe poder configurarse.
20. Se admite opcionalmente un modelo local.

### Modelo local

El docente indicó que utilizar un modelo local es valorable, pero no obligatorio.

No propongas reemplazar el proveedor existente solamente para cumplir el requisito opcional de ejecución local.

### Objetivo del análisis

Identifica:

- Qué requisitos ya cumple NodoBoard.
- Qué requisitos ya cumple DiagramCraft.
- Qué funcionalidades de DiagramCraft podrían incorporarse a NodoBoard.
- Qué funcionalidades deben conservarse en NodoBoard.
- Qué requisitos requieren desarrollo nuevo.
- Qué funcionalidades no es necesario migrar.
- Qué mejoras son imprescindibles.
- Qué mejoras pueden postergarse.

**No implementes todavía el segundo parcial. Utiliza sus requisitos únicamente como criterio para decidir qué merece la pena trasladar.**

---

## 12. Undécima fase: ranking final de funcionalidades

Construye un ranking ordenado utilizando:

1. Obligatoriedad para el segundo parcial.
2. Prioridad P0–P3.
3. Puntuación ponderada.
4. Dependencias técnicas.
5. Menor riesgo y esfuerzo cuando los beneficios sean similares.

Entrega obligatoriamente una tabla:

| Ranking | Funcionalidad | Decisión | Puntuación /100 | Prioridad | Esfuerzo /5 | Riesgo /5 | Confianza |
|---|---|---|---:|---|---:|---:|---|

Para cada funcionalidad indica:

- Archivo de origen en DiagramCraft.
- Archivo de destino o punto de integración en NodoBoard.
- Dependencias.
- Beneficio esperado.
- Justificación de la puntuación.
- Razón de su prioridad.
- Riesgos.
- Recomendación final.

Explica por qué una funcionalidad con menor puntuación podría implementarse antes que otra, por ejemplo por dependencias técnicas o requisitos obligatorios.

La clasificación debe permitir tomar decisiones reales, no solamente enumerar características.

---

## 13. Duodécima fase: módulos recomendados y descartados

Identifica específicamente los módulos que conviene aprovechar de DiagramCraft.

Para cada módulo recomendado indica:

1. Funcionalidad que aporta.
2. Archivos responsables en DiagramCraft.
3. Archivos o componentes de NodoBoard donde se integraría.
4. Código o lógica potencialmente reutilizable.
5. Dependencias.
6. Compatibilidad.
7. Cambios necesarios.
8. Dificultad de adaptación.
9. Riesgos.
10. Beneficios.
11. Prioridad.
12. Puntuación.
13. Confianza de la recomendación.

### Módulos que NO deben migrarse

Identifica también las funcionalidades que:

- NodoBoard ya tiene implementadas.
- Son inferiores a las existentes.
- Son redundantes.
- No aportan beneficios relevantes.
- Requieren demasiado esfuerzo frente a su valor.
- Introducen riesgos innecesarios.
- No forman parte del alcance académico.

Justifica por qué deben conservarse las implementaciones actuales de NodoBoard.

No recomiendes fusionar o trasladar código por el simple hecho de que existe en DiagramCraft.

---

## 14. Decimotercera fase: informe técnico final

Entrega un informe organizado en las siguientes secciones:

### A. Diagnóstico actual de NodoBoard

- Arquitectura.
- Funcionalidades existentes.
- Fortalezas.
- Debilidades.
- Estado de su IA.
- Estado de colaboración.
- Pruebas ejecutadas.
- Limitaciones.

### B. Diagnóstico actual de DiagramCraft

- Arquitectura.
- Funcionalidades existentes.
- Fortalezas.
- Debilidades.
- Capacidades de Diana.
- Funcionalidades potencialmente reutilizables.
- Pruebas ejecutadas.
- Limitaciones.

### C. Comparación detallada de asistentes IA

Explica si conviene:

- Conservar la IA de NodoBoard.
- Mejorar la IA existente utilizando capacidades de Diana.
- Integrar determinados servicios de DiagramCraft.
- Fusionar partes de ambas implementaciones.
- Reemplazar el asistente solamente si existe una justificación técnica excepcional.

Entrega una conclusión clara sobre la necesidad real de Diana.

### D. Matriz comparativa completa

Incluye:

- Funcionalidades.
- Implementación de ambos proyectos.
- Evidencias.
- Decisiones.
- Puntuaciones.
- Prioridades.
- Riesgos.
- Esfuerzo.
- Confianza.

### E. Ranking de funcionalidades recomendadas

Ordena las funcionalidades según criterios académicos, funcionales y técnicos.

### F. Módulos recomendados para migrar

Identifica archivos, funciones, dependencias y puntos de integración.

### G. Módulos que deben conservarse en NodoBoard

Justifica por qué no requieren migración.

### H. Módulos que deben descartarse

Explica duplicaciones, incompatibilidades o beneficios insuficientes.

### I. Riesgos y dependencias

Analiza:

- Compatibilidad Django.
- Diferencias React/Angular.
- Modelos de datos.
- Migraciones.
- Endpoints.
- WebSocket.
- Autenticación.
- Seguridad.
- Persistencia.
- Colaboración.
- Integridad de datos.

### J. Brechas respecto al segundo parcial

Indica lo que falta por desarrollar sin comenzar la implementación.

### K. Orden recomendado de integración

Propón una secuencia de trabajo justificada por prioridad, puntuación, riesgo, esfuerzo y dependencias.

### L. Resultados de pruebas

Incluye:

- Comandos ejecutados.
- Pruebas exitosas.
- Pruebas fallidas.
- Pruebas omitidas.
- Problemas del entorno.
- Limitaciones de verificación.

### M. Conclusión técnica final

Responde explícitamente:

1. ¿Qué funcionalidades de DiagramCraft conviene trasladar a NodoBoard?
2. ¿Qué funcionalidades de NodoBoard son mejores?
3. ¿Qué funcionalidades deben conservarse?
4. ¿Qué funcionalidades deben fusionarse?
5. ¿Qué funcionalidades deben descartarse?
6. ¿Es realmente necesario incorporar Diana?
7. ¿Basta con mejorar la IA existente de NodoBoard?
8. ¿Qué modificaciones futuras necesitaría Django?
9. ¿Qué modificaciones futuras necesitaría Angular?
10. ¿Qué falta para cumplir el segundo parcial?
11. ¿En qué orden conviene trabajar?
12. ¿Qué alternativa ofrece mejor relación entre beneficio, esfuerzo y riesgo?

---

## 15. Restricciones estrictas

- No modificar código.
- No implementar funcionalidades.
- No migrar módulos todavía.
- No crear migraciones.
- No cambiar modelos.
- No reemplazar Angular por React.
- No reemplazar la IA de NodoBoard sin justificación.
- No introducir Diana automáticamente.
- No eliminar funcionalidades existentes.
- No duplicar módulos.
- No modificar DiagramCraft.
- No modificar NodoBoard.
- No cambiar rutas.
- No alterar contratos API.
- No instalar dependencias innecesarias.
- No realizar operaciones destructivas.
- No borrar volúmenes ni bases de datos.
- No ejecutar pruebas sobre bases de datos de producción.
- No exponer credenciales ni secretos.
- No desplegar aplicaciones.
- No modificar servidores AWS.
- No realizar commits ni pushes.
- No inventar resultados de pruebas.
- No inventar puntuaciones.
- No asumir que DiagramCraft es superior en todo.
- No recomendar migraciones sin evidencias.
- No comenzar el desarrollo del segundo parcial.
- Respetar las instrucciones y skills existentes de ambos proyectos.

Las pruebas deben ejecutarse en entornos seguros y aislados, siempre que estén disponibles.

---

## 16. Resultado final esperado

Quiero obtener una **auditoría comparativa técnica, objetiva, verificable, cuantificada y priorizada** que determine exactamente qué vale la pena trasladar de DiagramCraft a NodoBoard.

El análisis debe favorecer la solución que permita cumplir los requisitos del segundo parcial con el menor esfuerzo razonable, sin sacrificar seguridad, calidad, compatibilidad ni mantenibilidad.

Debes indicar claramente:

1. Qué funcionalidades conviene migrar.
2. Cuáles conviene adaptar.
3. Cuáles deben fusionarse.
4. Cuáles deben conservarse.
5. Cuáles deben descartarse.
6. Qué funcionalidades requieren desarrollo nuevo.
7. Qué prioridad tiene cada una.
8. Qué puntuación obtiene cada una.
9. Qué esfuerzo y riesgo representa.
10. Qué evidencia respalda las conclusiones.
11. Si Diana realmente es necesaria o únicamente conviene aprovechar algunas de sus capacidades.
12. Cuál es el orden óptimo para una implementación futura.

**DETENTE AL FINALIZAR LA AUDITORÍA, LAS PRUEBAS, LA MATRIZ COMPARATIVA Y EL RANKING.**

**NO IMPLEMENTES, NO MODIFIQUES Y NO MIGRES NADA HASTA QUE REVISE Y APRUEBE EXPRESAMENTE LOS RESULTADOS.**
