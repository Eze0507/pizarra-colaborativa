# Mapa de integración auditado (verificar estado actual)

| ID | Origen donante | Destino / cautela |
|---|---|---|
| F05/B01 | `proyectos/permissions.py`, controles de escritura `diagramas/views.py` | `backend/modelado/views.py`, `consumers.py`, `usuario/models.py`; roles distintos (lector/arquitecto ≠ visualizador/editor), JWT de NB |
| F03/F06/B02 | `diagramas/serializers.py`, `ai_operations.py`, revisión de Diagrama | `modelado/models.py`, `serializers.py`, `consumers.py`; ORM más snapshot; evitar pérdida por snapshot viejo |
| F07/B03 | `diagramas/consumers.py`, `realtime.py`, frontend `useDiagramSocket.js` | `modelado/realtime.py`, `consumers.py`, Angular `whiteboard-socket.service.ts`; donante no cierra siempre lectura tras revocación |
| F10/F11/F12/B08 | `diagramas/ai_interpreter.py`, `ai_operations.py`, `ai_plans.py`, `views.py` | `backend/asistente/views.py`, ORM NB, Angular `asistente-ia.service.ts` y `whiteboard.page.ts`; revisar rebase y reintentos |
| F13/B07 | Resumen del diagrama autorizado de IA | Contexto servidor con proyecto/revisión, no confiar en `contexto_diagrama` libre del cliente |
| F22/B09/U07 | `diagramas/xmi.py` | `backend/generador/services/xmi_importer.py`, `xmi_exporter.py`; preservar perfil EA de NB |
| F24/B10/U08 | `diagramas/spring_generator.py` | `backend/generador/`, interfaz Angular; no afirmar compilación sin tests |

Evidencias: AUDITORIA_FASE_1.md H-N01/H-N02/H-N03/H-N05; FASE_2.md H2-D01 y reintentos; FASE_3.md X3/R3/S3; FASE_4.md matriz Fxx; FASE_5.md secciones I/J/K/M/Q. Los códigos son identificadores documentales, no módulos importables.
