# Ruta de implementación orientativa (fuente: FASE_5; releer plan real)

| Orden condicionado | IDs | Objetivo | Dependencia |
|---|---|---|---|
| Baseline | B00/U00 | Acreditar entorno, tests y cambios previos | Git y versiones reales |
| Seguridad | F05/B01 | Permisos REST/WS, revocación | JWT, membresía |
| Documento | F03/F06/F07, B02/B03/U01 | Validación, revisión, reconciliación y resync | permisos |
| Proveedor/contexto | F32/F13, B05 | Adaptador de proveedor y contexto autorizado del diagrama | proyecto/revisión |
| Conversación | F16/B04/U02 | Mensajes y respuestas compartidas; actor/destinatario | permisos, eventos |
| Historial | F18/B04/U02 | Persistencia y recuperación autorizadas | modelo/contrato de mensaje; obligatoriedad por confirmar |
| Contexto | F17/B06 | Memoria grupal/individual y continuidad | conversación; definición de alcance por confirmar |
| Asesoría | F19/F20/B07/U04 | Preguntas conceptuales sin escritura y moderación | chat, contexto, proveedor |
| Operaciones | F10/F11/F12, B08/U03 | Instrucciones tipadas, confirmación, idempotencia | autoridad de escritura/revisión |
| Cierre | pruebas PX y UAT | Multipestaña, aislamientos, regresión primer parcial | función completa |

Preservar XMI y generación Spring del primer parcial; su situación real no se redefine como opcional del primer parcial simplemente porque el núcleo conversacional sea prioritario.
