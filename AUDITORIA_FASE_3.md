# Auditoría — Fase 3 de trabajo: comparación técnica de backend y frontend

Fecha: 30 de octubre de 2026. Proyecto de destino: NodoBoard. Referencia: DiagramCraft backend y frontend. Ejecución exclusivamente analítica de las fases 3 y 4 del documento maestro, agrupadas por autorización del usuario. No constituye una migración ni un plan definitivo de implementación.

## A. Resumen ejecutivo

NodoBoard y DiagramCraft comparten Django/DRF/Channels, pero no comparten un contrato de dominio intercambiable. NodoBoard persiste entidades, atributos y relaciones normalizados, además de un snapshot visual en Proyecto; DiagramCraft edita principalmente un documento JSON nodes/edges versionado en Diagrama. Los modelos UML relacionales heredados de DiagramCraft siguen expuestos, pero no son la autoridad del editor React. Copiarlos a NodoBoard introduciría una tercera representación y no trasladaría las capacidades reales del editor.

NodoBoard debe conservar Angular, sus rutas, servicios, JointJS, proyectos y experiencia de pizarra. DiagramCraft aporta patrones aprovechables de revisión esperada, validación del documento, planes IA confirmables, presencia persistida con caducidad, recuperación de conflictos, importación XMI con límites y generación Spring Boot. Cada capacidad exige un adaptador al modelo normalizado y a JWT; ninguna justifica copiar JSX, Zustand, las migraciones del donante o su autenticación de sesión.

La conclusión de fase 2 se mantiene: conservar un único asistente integrado en NodoBoard y adaptar capacidades seleccionadas de Diana, sin trasladar íntegramente su interfaz. No se ha encontrado evidencia que certifique memoria conversacional compartida, individual/grupal o aislamiento de historiales como requisito plenamente implementado en ninguno. La carrera de revisión detectada en fase 2 impide considerar que los planes del donante resuelven por sí solos toda concurrencia.

Hallazgos nuevos de esta fase, con alcance preciso:

- **X3 — incompatibilidad XMI reproducida:** el parser puro de DiagramCraft devuelve cero nodos y cero relaciones para la fixture EA de NodoBoard con nueve clasificadores UML principales, sin errores en su reporte. El problema está en el reconocimiento de atributos XMI del namespace antiguo. No se ha ejecutado el endpoint de reemplazo ni escrito una base de datos.
- **R3 — reconciliación Angular reproducida:** WhiteboardApiService.reconciliarDatosDiagrama conserva relaciones de snapshot ausentes en ORM y asigna una entidad intermedia huérfana a la primera asociación elegible. Dos escenarios aislados reproducen la lógica; no se declara un incidente real en producción.
- **S3 — revocación de lectura WebSocket parcialmente verificada:** los handlers de DiagramCraft notifican member.removed, pero no cierran el canal; una entrega diagram.update posterior sigue enviándose en la prueba pura. La escritura sí tiene comprobaciones adicionales. No se ha probado un ataque de red completo.
- **F3 — corrección de inferencia documental:** AppRouter.jsx, authStore.js, ProjectsPage.jsx, ActiveUsers.jsx y VoiceCommand.jsx están vacíos. La navegación real es main.jsx → App.jsx → autenticación o DiagramCanvas. No debe deducirse React Router, un store de autenticación o componentes activos por esos nombres.
- **I3 — enlace de invitación incompleto por inspección:** NodoBoard genera /invitacion/{token}, pero app.routes.ts no declara esa ruta. La aceptación desde las notificaciones del dashboard sí tiene otra cadena implementada. No se envió correo.

Estado de verificación: el código y los contratos descritos fueron inspeccionados; las pruebas históricas siguen siendo aplicables al código fuente porque sus inventarios no cambiaron. Las nuevas pruebas son puras, sin migraciones, red ni servicios reales. PostgreSQL, Redis, navegadores, Enterprise Architect y compilación Java final siguen requiriendo verificación integrada. La suite backend de DiagramCraft heredada no está completamente verde; no se oculta ese resultado.

### Identidad, vigencia y notación

Rutas reales verificadas:

| Alias usado aquí | Carpeta real | Rama inicial | Commit inicial | Origin |
|---|---|---|---|---|
| NB | D:\Informatica\8vo Semestre\sw1-2-2026\pizarra-colaborativa | feat/integrar-diagramcraft | df5430d221ddfbdc23e0a7882e535dc402ceafc4 | https://github.com/Eze0507/pizarra-colaborativa.git |
| DB | D:\swProyecto\backend | main | 125dc3b72fed6a829299d5733f31277d0c789a1c | https://github.com/juanse8202/swbackend.git |
| DF | D:\swProyecto\frontend | main | e200fc82b2fa6cb3b79e62b5411a6942ccd0cc7a | https://github.com/juanse8202/swfrontend.git |

Todas las rutas relativas se interpretan respecto al alias correspondiente. Se leyeron completos AUDITORIA_MAESTRA.md, AUDITORIA_FASE_1.md y AUDITORIA_FASE_2.md. Sus SHA-256 iniciales son, respectivamente:

~~~text
e31d7c76755987a6542d033720f65276d3dbe1db5ff8026eb8405498d9deca41
9f696d650923ca4b27da9c0d4a4b4215f9b8bda85783f702f6c631326f6d180c
0c229547359d479c290ba3c51bac714c854feec788e1152de6b4e97839405d0a
~~~

Se compararon 1885 archivos del inventario de fase 1 y 1886 del de fase 2: ningún hash cambió. El inventario inicial de esta fase contiene 1887 archivos existentes. Esta verificación incluye los archivos rastreados y no ignorados inventariados; no certifica que todo el entorno instalado o servicios externos sean idénticos. El inventario de fuentes contiene NB 59 Python y 65 TypeScript, DB 64 Python, DF 42 JavaScript/JSX, incluidos archivos vacíos. Existencia, importación activa, comportamiento probado y experiencia integrada son evidencias distintas.

Estado inicial y al reanudar, antes de crear este informe:

~~~text
NB:
 M frontend/package-lock.json
?? AUDITORIA_FASE_1.md
?? AUDITORIA_FASE_2.md
?? AUDITORIA_MAESTRA.md
?? auditoria-diagramcraft-nodoboard.code-workspace
?? debug.log
DB: limpio
DF: limpio
~~~

Al reanudar no existía AUDITORIA_FASE_3.md; no había contenido parcial que sobrescribir. Se conservó la evidencia temporal de la ejecución interrumpida. No se repitieron pruebas al reanudar. La autorización posterior de completar un informe parcial no fue necesaria para modificar ningún otro archivo.

## B. Arquitectura del backend de NodoBoard

### Aplicaciones y responsabilidades

| Archivo/módulo NB | Responsabilidad observada | Dependencias y límite |
|---|---|---|
| backend/core/settings.py, urls.py, asgi.py | Configuración Django, rutas, JWT, CORS, SMTP, Channels | Auth/DRF, Redis y PostgreSQL según configuración; valores de desarrollo no equivalen a despliegue endurecido |
| backend/usuario/views.py, serializers.py, urls.py | Registro, activación, login JWT, refresh, logout y búsqueda de usuarios | Django User; UserColaborador depende de Proyecto; SMTP y firma temporal |
| backend/modelado/models.py | Proyecto, Entidad, Atributo, Relacion | ORM normalizado; Proyecto.datos_diagrama es representación visual adicional |
| backend/usuario/models.py | UserColaborador: rol y estado de invitación/membresía | Vincula User y Proyecto; unicidad del par |
| backend/modelado/views.py, serializers.py | CRUD de proyectos, carga de diagrama, invitaciones y colaboradores | Los serializers contienen parte de la lógica de invitación y correo; las vistas autorizan de forma desigual |
| backend/modelado/consumers.py | Eventos colaborativos, presencia, bloqueos y guardado total de snapshot | Acopla protocolo visual, permisos iniciales y persistencia ORM; no hay revisión del documento |
| backend/modelado/middleware.py, routing.py, realtime.py | JWT en handshake y eventos/grupos | ASGI y channel layer; no sustituyen autorización por operación |
| backend/asistente/views.py | Solicitud multimodal/instrucciones al proveedor y respuesta de deltas | Lee contexto de modelado; no tiene autoridad persistente de plan confirmado |
| backend/generador/views.py, services/xmi_importer.py, services/xmi_exporter.py | Importación/exportación XML UML/EA | Dependen directamente de Entidad/Atributo/Relacion y snapshot |

asistente/models.py y generador/models.py no implementan un almacén de conversaciones ni un generador Java. El nombre generador se refiere aquí a XML; paquete_base en Proyecto tampoco demuestra generación Spring Boot.

### Modelado, validación y persistencia

Proyecto usa ID entero grande, codigo único (máximo 20), nombre de 150, descripción, propietario FK, colaboradores mediante UserColaborador, paquete_base y JSON de diagrama. El código PROJ secuencial se calcula en aplicación; no se verificó concurrencia de esa asignación. Entidad tiene proyecto, nombre, estado activo/bloqueado/papelera, coordenadas, ancho y es_intermedia. Atributo pertenece a Entidad y restringe tipo a string/int/long/double/bool/date; es_clave, es_nulo y orden describen una fracción del modelo Java/JPA.

Relacion guarda proyecto, origen/destino, tipo asociación/agregación/composición/herencia, multiplicidades, puertos y clase_asociacion opcional SET_NULL. Su save ejecuta full_clean. La validación de multiplicidad reconoce formatos numéricos y rangos, pero no ofrece toda la semántica del validador UML/JPA del donante ni comprueba necesariamente límites invertidos. No hay modelado equivalente de interface/enum/embeddable/DTO, realización, dependencia, navegabilidad o extremo whole explícito.

El guardado de snapshot reconstruye el conjunto ORM: remapea IDs temporales, actualiza entidades/relaciones y elimina ausentes; los atributos se reconstruyen, por lo que no debe darse por estable su ID. La transacción protege atomicidad local, pero no detecta que otro cliente haya guardado una revisión posterior. Las pruebas de fase 1 reprodujeron borrado con snapshot obsoleto. La carga reúne ORM y JSON visual; R3 demuestra que la reconciliación puede recuperar elementos del snapshot que el ORM ya no contiene. No hay una única autoridad inequívoca en todos los recorridos.

### Autenticación, permisos y errores

Se usa Django User y SimpleJWT. La configuración declara acceso de 120 minutos, refresh de un día, rotación y blacklist. El registro solicita username, email, nombres y contraseña, crea usuario inactivo y firma activación de 24 horas; la ruta Angular /activar/:token existe. El serializer comprueba una longitud mínima, pero no equivale a invocar todos los validadores de contraseña configurados. El fallo SMTP se captura y puede imprimir el enlace de activación en consola: registro aceptado no demuestra correo entregado.

Las consultas de proyectos permiten propietario o colaborador activo. DELETE exige propietario; PATCH del proyecto no aplica una separación equivalente de escritura por rol, hallazgo H-N01 previo probado con visualizador. El consumer comprueba acceso al conectar, pero guardar_snapshot no revalida de forma suficiente el rol y la membresía vigente en cada escritura, H-N02. Las restricciones visuales Angular no son autorización de servidor.

core/asgi.py envuelve el WebSocket con AllowedHostsOriginValidator y JwtAuthMiddlewareStack. ALLOWED_HOSTS abierto reduce la utilidad de ese filtro como lista estricta de orígenes. JWT en query string exige además cuidar registros y transporte en un despliegue; no se cambió esa configuración ni se reprodujeron fugas. Los errores del asistente y las importaciones no tienen el mismo esquema ni granularidad que los de las vistas de proyectos.

### Fortalezas y límites

El dominio normalizado, los límites entre usuario/modelado/generador, el editor Angular ya conectado y la importación EA existente son bases útiles para conservar. La mezcla de reglas en serializers, views y consumer hace difícil garantizar permisos, validación y concurrencia uniformes. La ausencia de revisión, un único servicio de escritura y publicación posterior al commit exige diseño antes de incorporar capacidades del donante. Las migraciones modelado/0001–0011 y usuario/0001 muestran evolución real de datos, no un esquema que deba sustituirse por el del donante.

## C. Arquitectura del backend de DiagramCraft

### Organización efectiva

| Archivo/módulo DB | Responsabilidad observada | Acoplamiento/límite |
|---|---|---|
| config/settings.py, urls.py, authentication.py, serializers.py, usernames.py | Configuración, sesión/CSRF, registro/login y normalización de nombres | Django/allauth, dotenv y DATABASE_URL; flujo distinto del JWT de NB |
| proyectos/models.py, permissions.py, services.py, signals.py | Proyectos, miembros, invitaciones, ciclo de vida y propietario | Servicios transaccionales; señal asegura miembro owner |
| proyectos/views.py, serializers.py, realtime.py, consumers.py | API de proyectos, consultas, permisos y avisos en grupos | Consultas de conteo usan funciones PostgreSQL; notificación no garantiza revocación de sockets |
| diagramas/models.py | Diagrama JSON, revision, PlanIA, PresenciaDiagrama y modelos UML heredados | Coexisten representaciones; JSON es autoridad del editor actual |
| diagramas/serializers.py, foreign_keys.py | Validación/normalización del documento, tipos, relaciones y FK heredadas | Semántica UML/JPA y formato React Flow influyen en el contrato |
| diagramas/views.py, api_errors.py | CRUD, interpretación/aplicación IA, Spring Boot, XMI | Orquesta permisos, locks y publicación; sigue siendo módulo con muchas responsabilidades |
| diagramas/ai_interpreter.py, ai_operations.py, ai_plans.py | Interpretación, operaciones tipadas y ciclo de plan persistido | Requiere adaptación a IDs/entidades NB y corrección de la ventana de revisión de fase 2 |
| diagramas/consumers.py, realtime.py | Presencia, sincronización y guardado, autorización de escritura | REST es escritor del React actual; WS también expone guardado, no debe ignorarse |
| diagramas/xmi.py | Parser/exportador XMI, perfiles EA y geometría | lxml y normalización; el namespace de X3 rompe una fixture real |
| diagramas/spring_generator.py | Transformación de documento UML/JPA a ZIP Spring Boot | Jinja2, validaciones y plantillas internas; no es un servidor Spring en ejecución |
| modelador/models.py, views.py, tests.py | Esqueleto de app | No hay una capacidad funcional adicional que migrar por existir el directorio |

### Servicios y transacciones

proyectos/services.py centraliza create_project_with_main_diagram y duplicación/ciclo de vida. Crear un proyecto crea el diagrama principal en una transacción. No se observó creación automática de un nuevo espacio personal al listar proyectos; no debe confundirse con datos históricos. Proyecto tiene nombre de 200, creador, fechas, plantilla y archivado. Una restricción condicional hace único Lower(nombre) por creador entre activos; archivar, restaurar y duplicar tienen reglas propias.

ProyectoMiembro separa owner/architect/editor/reader; InvitacionProyecto es entidad aparte, con estado y unicidad de invitaciones pendientes. Se pueden ajustar roles y salir o retirar miembros con restricciones sobre owner. La invitación se comunica mediante API/avisos del sistema; reenviar actualiza invitación, no prueba envío SMTP equivalente a NodoBoard.

Diagrama contiene nodes/edges JSON y revision positiva grande. DiagramaSerializer valida y normaliza IDs string, referencias, tipos, relaciones y metadatos. Las escrituras documentales con expected_revision usan bloqueo transaccional, revalidan permisos y publican después del commit. La revisión aumenta al cambiar el documento. Eso permite rechazar 409 y recargar, pero no fusiona automáticamente ediciones concurrentes ni ofrece CRDT/OT.

PlanIA usa UUID, usuario/diagrama FK, operaciones, revisión base, hashes, caducidad, estado y resultado. request_id tiene índice, no unicidad suficiente para prometer deduplicación total. PresenciaDiagrama usa canal único, usuario/diagrama y actividad con expiración de 45 segundos: es más apta para múltiples procesos que el diccionario local NB, aunque necesita depuración y pruebas reales de canales/Redis.

### Validación y seguridad

La configuración DRF usa sesión autenticada y CSRF; el registro invoca validate_password. allauth expone proveedores sociales Google/GitHub/GitLab. CORS con credenciales, cookies HttpOnly/SameSite y Secure condicionado por DEBUG exigen conservar configuración coherente; no sirven como reemplazo directo de JWT. ASGI no muestra el equivalente explícito a un validador de origen WS de NB. CORS HTTP por sí solo no controla el origen de los WebSockets.

Owner/architect pueden editar estructura de relaciones, importar/exportar XMI y generar Spring; editor tiene facultades más limitadas y reader sólo lectura. El serializer detecta modificación de edges no autorizada. No obstante, la API ORM heredada de ClaseUML permite cambiar parent FK comprobando sólo el padre original, H-D04 probado previamente. Es incorrecto declarar seguro todo el backend por la fortaleza del flujo JSON principal.

El guardado WS valida con DiagramaSerializer pero persiste nodes/edges originales en lugar de serializer.validated_data en save_diagram_if_user_can_access. Es un riesgo estático de divergencia de normalización frente a REST, especialmente para formatos heredados; no se ejecutó un caso nuevo de persistencia para medirlo. Los handlers de revocación tienen además la limitación S3.

Las migraciones fueron leídas, no aplicadas: diagramas/0002 incorpora JSON, 0003–0005 presencia y limpieza histórica, 0006 revisión/planes, 0007 identidad de solicitud; proyectos/0004 unicidad y 0005 archiva espacios de nombre histórico. Hay RunPython que elimina presencias sin actividad y archiva datos concretos. No son reutilizables como una migración de NodoBoard.

## D. Comparación técnica de backend

### Dominio, servicios y API

| Aspecto | NodoBoard | DiagramCraft | Compatibilidad y recomendación |
|---|---|---|---|
| Autoridad del diagrama | Entidad/Atributo/Relacion más datos_diagrama | Diagrama.nodes/edges; ORM UML heredado adicional | Requiere DTO canónico/adaptador; conservar dominio NB, no copiar ambas autoridades |
| Escritura | Snapshot completo en consumer y PATCH de proyecto | REST versionado, WS alternativo, planes IA e importación | Adaptar servicio único con permisos/revisión y salida autoritativa; no conectar rutas sin unificar reglas |
| Separación de negocio | Parte en serializers, views y consumer | Servicios de proyectos, validadores y módulos de IA/exportación | Aprovechar separación y funciones puras, conservando configuración y autenticación NB |
| Errores | DRF, mensajes de snapshot y errores IA con formatos dispares | Validación estructurada, errores de revisión y generación con referencias | Normalizar en Angular; no asumir que todo error es detail string |
| API | /api/usuario, /api/modelado, /api/asistente, /api/generador | /api/login, /api/registro, /api/csrf, /api/me, /api/logout, /api/proyectos, /api/diagramas y cuentas sociales | No hay versionado semántico público equivalente /v1; igual prefijo /api no indica compatibilidad |
| Invitación | UserColaborador pendiente, firma/correo, rol editor | InvitacionProyecto separada, roles elegibles, avisos API | Adaptar estados/roles/identidad; I3 afecta enlace por correo NB, no aceptación interna |
| Ciclo de proyecto | Crear/listar/eliminar; snapshot en proyecto | Diagrama independiente, archivar/restaurar/duplicar/plantilla | Capacidad adicional real por código; requiere reglas de propiedad, nombres y privacidad NB |

### Colaboración, persistencia y concurrencia

| Aspecto | NB: backend/modelado/consumers.py y socket Angular | DB/DF: diagramas/consumers.py, realtime.py y useDiagramSocket.js |
|---|---|---|
| Ruta/autenticación | /ws/pizarra/{proyecto_id}/?token=JWT; acceso inicial por propietario/activo | /ws/diagramas/{id}/ con sesión; canales de diagrama y proyecto |
| Grupos | pizarra_{id} | diagram_{id} y grupo del proyecto para cambios de miembros |
| Identificación/presencia | Diccionario de clase por proceso, usuarios/canales; no presencia distribuida duradera | PresenciaDiagrama por canal, actividad y expiración; heartbeat del cliente cada 20 s |
| Eventos | Movimiento, creación/edición/borrado, cursor, bloqueo/desbloqueo y guardar_snapshot; envoltura pizarra.evento y evento/data | diagram.update, avisos de proyecto/miembro/presencia; documento/revisión/request identity |
| Persistencia principal | Eventos visuales no necesariamente persisten; guardar_snapshot reescribe conjunto ORM | Cliente React guarda por REST con expected_revision; WS puede guardar mediante servicio autorizado |
| Confirmación | snapshot_guardado con exito, id_map, rel_id_map, usuario_id y timestamp | Documento nodes/edges y revision autoritativos; el cliente aplica respuesta o evento |
| Concurrencia | Sin expected_revision; snapshot obsoleto puede borrar ediciones | Lock y revisión; conflicto 409 recarga estado, no fusiona cambios |
| Bloqueos | Avisos de bloqueo por conexión, no lease persistido con dueño verificable | Revisión optimista; no equivalente a un bloqueo colaborativo fuerte por elemento |
| Desconexión/reconexión | Sin reintento efectivo encontrado; enviarMensaje pierde envío si no conectado | Hook reintenta a los 2 s; buffer sólo del último evento, no cola durable |
| Duplicación | Remapeo de IDs no equivale a idempotencia | Filtros de revisiones/solicitud en collaborationSync; idempotencia de aplicación no demuestra una sola publicación WS |
| Revocación | Guardados tras revocación reproducidos históricamente | Revalida escritura; S3 indica que notificar expulsión no corta entrega futura del socket |

Conservar los eventos finos y la interacción local de NB tiene valor. Adaptar revisión, ack autoritativo, recuperación tras reconexión y presencia con expiración exige decidir qué persiste cada evento y qué estado se descarta ante conflicto. No trasladar sólo el hook o sólo el contador de revisión: ambos extremos, todas las rutas de escritura, importaciones y planes deben compartir la misma precondición. Ni una transacción ni Redis garantizan convergencia de dos snapshots completos.

### Generación: responsabilidades distintas

NB/backend/generador exporta XML e importa modelos. No hay en el código inspeccionado generador Java/Spring, repositorios, servicios o controladores equivalentes. DB/diagramas/spring_generator.py transforma el documento canónico del donante a clases Java y, para entidades válidas, repositorios, servicios, controladores, DTO y mappers; incluye configuración y estructura Maven. Genera ZIP mediante temporales, nombres/rutas validados y Jinja2 con StrictUndefined. Los tipos class/interface/dto/enum/embeddable y entity no se traducen todos a tablas; JPA está condicionado por kind y jpaManaged.

Los valores implementados observados son Maven, Java 21, Spring Boot 3.4.0, PostgreSQL e herencia JPA JOINED. No se verificó un selector de Gradle, otros motores o estrategias porque la skill mencione posibilidades; la UI envía opciones vacías y utiliza valores por defecto. Las capas de entidades se generan conjuntamente; no se constató configuración de cada capa por separado. .env.example usa marcadores, no credenciales reales de usuario. Ordenar archivos no prueba identidad binaria de ZIP entre ejecuciones por sus timestamps.

La generación exige completar identidad JPA, tipos y relaciones más allá de lo requerido para dibujar; errores pueden referenciar element_id para enfocar el nodo en DF. La prueba heredada que lleva generated_java_compiles en su nombre inspecciona ZIP/texto y no ejecuta javac. Ventaja parcialmente verificada: hay una transformación y artefactos consistentes con sus pruebas; compilación y comportamiento Spring final siguen pendientes. La integración futura sería un exportador de NodoBoard, sin reemplazar Django ni acoplar la base de datos real a la aplicación generada.

### XMI y Enterprise Architect

| Tema | NB: xmi_importer.py / xmi_exporter.py | DB: diagramas/xmi.py y acción importar_xmi |
|---|---|---|
| Perfil | XML EA con namespaces schema.omg.org/spec/UML/2.1 y XMI/2.1 | Núcleo UML y extensiones EA, atributos XMI reconocidos con URI 20131001 |
| Lectura/escritura | Class/AssociationClass, atributos, cuatro tipos de relación y posiciones; paquetes aplanados | Seis tipos de relación, kinds, geometría y avisos; mapping class/entity/auto |
| Autoridad | Importación crea ORM y reconstruye snapshot | Importación produce nodes/edges normalizados y reemplaza Diagrama |
| Seguridad de entrada | Archivo limitado a 10 MB; texto JSON no muestra el mismo tope explícito; ElementTree | 2 MB, 20000 elementos, profundidad 100, sin DTD/entidades/red en lxml |
| Vista previa | No equivalente completo en el flujo inspeccionado | dry_run, report, preview, selección/exclusión por xmi_id; no persistencia en preview |
| Reemplazo | reemplazar_existente, transacción; UI vuelve a cargar | mode=replace; fila bloqueada, revisión incrementada, publicación posterior al commit |
| Concurrencia de importación | Sin revisión esperada | No recibe expected_revision del preview; lock serializa escrituras pero no rechaza preview obsoleto |
| Preservación | IDs nuevos/UUID de exportación, límites de tipos; bigint mal clasificado como integer en prueba previa | Identificadores/anchors y sourceLabel, sanitización Java; no preserva toda extensión EA |
| Resultado real | Round-trip de fixture 9 entidades, 33 atributos, 10 relaciones en fase 1; sólo conteos | Pruebas internas de perfiles propios válidas; X3 falla para la fixture NB |

Detalle de X3: la fixture NB/backend/generador/fixtures/diagramaExamen.xml declara XMI 2.1 con http://schema.omg.org/spec/XMI/2.1. _attr en DB/diagramas/xmi.py reconoce atributo sin namespace o {http://www.omg.org/spec/XMI/20131001}, de modo que no identifica type/id del perfil antiguo. La detección EA tolera versión no reconocida y retorna vacío con warning ea_core_only, sin report.errors. La prueba corregida cuenta nueve packagedElement Class/AssociationClass del núcleo, no los duplicados de definición en extensiones. El exportador NB usa el mismo URI antiguo, aunque esta prueba concreta se hizo sobre la fixture, no sobre una nueva exportación.

Un documento vacío puede superar validación estructural; conectar directamente ese parser a un reemplazo sería un riesgo de pérdida silenciosa. No se llamó al endpoint ni se ejecutó ese reemplazo. No se concluye que todo XMI 2.1 falle: un transporte de esa versión con los URIs reconocidos puede funcionar. Tampoco se concluye compatibilidad general con Enterprise Architect por los conteos previos. Antes de recomendar trasladar el parser completo deben resolverse perfiles, rechazo de vacío inesperado y ensayos cruzados reales.

### Seguridad comparada y conclusión

NB conserva un sistema JWT ya integrado; DB presenta validación de documento y revalidación de escritura más extensas, pero tiene superficies heredadas y revocación de lectura insuficiente. No conviene importar SessionAuthentication/allauth para obtener validadores o Spring. Reutilizar funciones de negocio debe ir acompañado de los permisos NB y una decisión explícita sobre propietario/editor/visualizador frente a owner/architect/editor/reader. El nuevo rol architect no existe actualmente en NB.

## E. Arquitectura frontend de NodoBoard

La entrada frontend/src/main.ts configura Angular standalone mediante app.config.ts. app.routes.ts separa AuthLayout, DashboardLayout y PizarraLayout con componentes cargados de forma diferida. Hay rutas login, registro, activar/:token, control, panel redirigido y pizarra/:id; wildcard vuelve a login. auth.guard.ts comprueba presencia de token, no autorización real al proyecto. jwt.interceptor.ts agrega credenciales; token-storage.service.ts usa localStorage. No se observó renovación automática integral ante 401; la existencia de refresh en backend no demuestra que el cliente lo use en todo recorrido.

| Área NB/frontend/src/app | Flujo y estado efectivos | Observaciones |
|---|---|---|
| features/auth | Formularios → auth.service.ts → API usuario → token-storage/rutas | Activación conectada; errores de HTTP y estado de carga; no sesión cookie DC |
| features/dashboard/pages/projects-list | projects.service.ts, tarjetas y modales crear/eliminar | Lista de proyectos del usuario; conserva diseño y navegación existente |
| features/dashboard/services/invitaciones.service.ts | BehaviorSubject de pendientes, contador y notificación de aceptación | Header acepta/rechaza, actualiza pendientes y permite recargar proyectos |
| features/whiteboard/pages/whiteboard/whiteboard.page.ts | Orquestación de carga, permisos UI, eventos, guardado y componentes | Coordina varias representaciones; no es una capa de negocio del servidor |
| services/whiteboard-canvas.service.ts | JointJS graph, mapas ID → celda y eventos del lienzo | Fuente local visual, obtiene snapshot y aplica remapeos de IDs |
| whiteboard-entity.service.ts, whiteboard-relationship.service.ts | Nodos, atributos, relaciones, puertos, vértices y asociación-clase | Esquema normalizado NB; cuatro tipos de relación |
| whiteboard-camera.service.ts | Movimiento de cámara/zoom | Separación útil, conservar comportamiento |
| whiteboard-api.service.ts | GET diagrama y reconciliarDatosDiagrama | Combina ORM con snapshot visual; R3 limita seguridad de esa combinación |
| whiteboard-socket.service.ts | RxJS WebSocket, estado de conexión y eventos | No se encontró reconexión funcional; imports de timers no prueban reintento |
| asistente-ia.service.ts, diagrama-parser.service.ts | Contexto, solicitud y aplicación de cambios al lienzo | Servicio extenso; requiere validación autoritativa/confirmación futura, según fase 2 |
| generador.service.ts | XML import/export mediante HttpClient/blob/FormData | No cliente de generación Java implementado |
| core/services y shared/components | Toasts, búsqueda y botones reutilizables | Manejo visual de errores no unifica contrato del servidor |

El editor crea y modifica nodos/relaciones localmente, con selección y posición en JointJS. editor-inline interpreta atributos de los seis tipos NB y flags PK/nulabilidad. menu-cardinalidad, menu-relacion y modales de propiedades permiten cambiar relación y multiplicidad; hay clase asociativa mediante entidad intermedia. Las herramientas de zoom, sidebar y menús están conectadas al lienzo; no son evidencia de interfaces, enums o realización soportadas por backend.

La carga llega antes o después de inicializar la vista y WhiteboardPage conserva datos pendientes para poblar el canvas. El guardado se agrupa mediante debounce de aproximadamente dos segundos y se representa guardando/error. snapshot_guardado remapea IDs temporales en entidades y relaciones. Las salidas/beforeunload/destroy intentan guardar, pero el envío al abandonar no garantiza entrega o confirmación. El socket descarta mensajes cuando no está conectado; una reconexión no implementada agrava la divergencia local.

La separación por servicios DI y RxJS es aprovechable. No hace innecesaria una fuente autoritativa clara: mapas JointJS, snapshot JSON y ORM pueden divergir. R3 confirma dos heurísticas de reconciliación que no deben convertirse en adaptador de migración sin reglas semánticas. Los flags de sólo lectura ocultan controles, pero no sustituyen controles de escritura del backend.

Hay roles/etiquetas en modales y chat y avisos mediante toasts; ello es evidencia estática de accesibilidad básica, no una validación con teclado o lector de pantalla. No se ejecutó prueba visual manual ni se certifica conformidad global.

## F. Arquitectura frontend de DiagramCraft

La cadena activa es src/main.jsx → src/App.jsx. App maneja autenticación y vista login/registro con useState, obtiene sesión mediante authApi y renderiza directamente DiagramCanvas al autenticar. Logout llama al backend y limpia estado de sesión del cliente. OAuth redirige por window.location. EditorPage.jsx es un envoltorio pequeño que no constituye la entrada activa observada.

**Corrección de inferencias previas:** src/routes/AppRouter.jsx, src/stores/authStore.js, src/pages/ProjectsPage.jsx, src/components/collaboration/ActiveUsers.jsx y src/components/voice/VoiceCommand.jsx tienen cero bytes. No implementan router, store, página ni controles. El inventario no cambió entre auditorías; se corrige la interpretación de presencia de archivos, sin modificar los informes anteriores. Las funciones activas de proyectos están en ProjectsDialog/NewProjectDialog dentro de DiagramCanvas; la presencia está integrada allí y en CollaboratorsDialog; la voz está en lógica de Canvas y utilidades. La conclusión de fase 2 sobre mantener Angular y un asistente único no depende de esos archivos vacíos y permanece válida.

| Módulo DF | Responsabilidad y estado | Acoplamiento/límite |
|---|---|---|
| components/editor/DiagramCanvas.jsx | Orquesta diagrama, proyectos, roles, revisión, autosave, diálogos, IA/voz y XMI | Componente central grande; trasladarlo entero también trasladaría acoplamiento |
| ClassNode.jsx, RelationEdge.jsx | Representación React Flow de clases y conectores | JSX/handles no portables a JointJS |
| PropertiesPanel.jsx, EditorToolbar.jsx | Edición, clases/atributos/métodos, multiplicidades, acciones | La semántica se puede adaptar; componentes deben seguir Angular |
| ProjectsDialog.jsx, NewProjectDialog.jsx, PeopleDialog.jsx, collaboration/CollaboratorsDialog.jsx | Proyectos, búsqueda de personas, invitaciones/roles y conectados | Dependen de contratos de sesión/usuario y roles DC |
| stores/diagramStore.js | Zustand: nodes/edges, selección, normalización, historial/futuro | Autoridad local JSON; no representa ORM NB |
| hooks/useDiagramSocket.js | Conexión, reintento, heartbeat, recepción y buffer limitado | No reemplaza REST de guardado; no ofrece entrega durable |
| api/authApi.js, axios.js | fetch/axios con credentials y CSRF | Diferente a HttpClient/JWT; no copiar cliente de autenticación |
| api/diagramApi.js, xmiApiContract.js | Operaciones proyectos/diagramas, archivos y FormData XMI | Resultados paginados/aliases normalizados para el cliente |
| utils/collaborationSync.js | Revisión, autoría de evento y aplicación autoritativa | Patrón aprovechable con tests, no garantía global de deduplicación |
| api/aiApi.js, utils/aiFlow.js, utils/dianaVoice.js | Interpretar/confirmar plan, fases y voz | Véase fase 2; cancelar UI no implica anular todo plan de servidor |
| utils/xmiImport.js, runtimeUrls.js | Selección/contrato importación y URLs de entorno | Adaptables a DTO/entornos Angular, sin trasladar Vite |
| hooks/useEscapeClose.js | Cierre del overlay superior con Escape | Patrón de interacción trasladable, pendiente prueba manual |

El store maneja historial de hasta 50 snapshots. restore normaliza tipos heredados, relaciones FK, anclajes y geometría EA; puede preservar selección y normalmente limpia historial salvo recordHistory. Undo/redo restaura snapshots y Canvas programa otro guardado; no implementa una operación inversa validada contra cambios colaborativos concurrentes. Recibir estado remoto suele invalidar el historial anterior.

El editor soporta seis kinds de nodo y seis tipos de relación, multiplicidades UML/JPA, métodos, ownership y associationClassNodeId. IDs son strings, con generación local estable; no utiliza el remapeo numérico NB. El estado optimista se guarda por REST después de aproximadamente 700 ms con expected_revision. Se aplican documento/revisión autoritativos, se invalidan guardados pendientes y se preserva selección/viewport cuando corresponde. Un conflicto recarga el servidor y puede descartar cambios locales; no es fusión.

El hook reintenta a los dos segundos y envía actividad cada 20 s, pero sólo conserva el último evento pendiente. Las restricciones visuales canEdit y canUseRelations corresponden a owner/architect/editor y no al conjunto de roles NB. El cliente responde al aviso de expulsión regresando al lienzo principal y comprueba acceso periódicamente; S3 muestra por qué esa buena conducta no puede sustituir el cierre en servidor.

El borrador principal puede guardarse en sessionStorage y no equivale a un proyecto servidor persistido o a un modo offline integral. Los indicadores de carga/error, aria-live, roles de diálogo, confirmaciones y enfoque de element_id son ventajas observables en fuente. No hubo validación de accesibilidad con navegador. React Router y @xyflow/react están declarados pero no se hallaron imports activos en src; se debe investigar su necesidad, sin eliminarlos durante esta auditoría.

## G. Comparación técnica frontend

| Aspecto | Angular NodoBoard | React DiagramCraft | Conclusión preliminar |
|---|---|---|---|
| Estructura | Rutas/layouts, DI, servicios y RxJS | App condicional, Canvas central, hooks, Zustand | Conservar arquitectura Angular; adaptar funciones puras y reglas, no JSX |
| Motor gráfico | JointJS con mapas de IDs ORM | React Flow con nodes/edges/handles | Adaptador de coordenadas, puertos y geometría; no cambiar motor sólo por copiar funciones |
| Tipos UML | Entidad, 6 tipos de atributo, 4 relaciones, clase asociativa | Kinds UML/JPA, métodos, 6 relaciones y metadatos avanzados | Ampliación exige backend/DTO antes de habilitar controles |
| Estado | Estado distribuido entre página/servicios/celdas y snapshot | Documento store con historial, estado local Canvas y revisión | Centralizar reglas del documento mediante servicios Angular; no añadir Zustand |
| Persistencia | Socket snapshot, ID remap y reconcilia ORM/JSON | REST expected_revision y estado autoritativo | Adaptar ciclo confirmar/aplicar/reconciliar con revision, no sustituir snapshot a ciegas |
| Conflicto | Sin detección equivalente; errores de guardado | 409 con recarga; invalida autosave pendiente | Adaptar control de generación/solicitud y aviso de descarte local |
| Presencia | Socket/grupo y usuarios; almacenamiento por proceso | DB presence/heartbeat y UX de miembros | Adaptar caducidad y control de revocación, no confiar sólo en polls/UI |
| Undo/redo | No se constató equivalente colaborativo sólido | Historial local de 50 snapshots | Investigar alcance local; no importar como garantía multiusuario |
| Navegación/proyectos | Dashboard y rutas reales | Diálogos dentro del editor; archivos de router vacíos | Conservar dashboard, adaptar archivo/restauración/duplicación si se autoriza después |
| Errores | Toast/flags locales y HTTP; formas heterogéneas | Errores de revisión/generación y enfoque del elemento | Un DTO de errores facilitaría Angular; debe mantener permisos y mensajes claros |
| Accesibilidad | Etiquetas/roles y controles existentes | Diálogos, Escape, aria-live y enfoque | Fusionar patrones de UX, pendiente ensayo manual en ambos |

La fase 2 recomienda un único asistente NB. Técnicamente, chat-asistente-ia.component.ts → asistente-ia.service.ts envía contexto y aplica delta local; DC separa aiApi.interpretar/aplicar y maneja plan persistido en backend. La adaptación útil es representar estados interpretando/pendiente de confirmación/aplicando/error, validar operaciones en servidor y aplicar su respuesta autoritativa. Requiere DTO para IDs y relaciones NB, permisos, revision/TTL y solicitud identificada; no basta copiar aiFlow.js. No se propone un segundo chat.

La voz activa del donante usa Web Speech del navegador y dianaVoice.js, no VoiceCommand.jsx. Sus dependencias de disponibilidad, idioma, wake phrase y cancelación siguen siendo las de fase 2. Sería un adaptador a la misma entrada del chat Angular. No se ejecutó reconocimiento de micrófono ni se verificó ausencia de servicios externos en Web Speech real; por ello quedó fuera de las pruebas.

La mantenibilidad se debe evaluar por reglas centralizadas y pruebas, no por elegir framework: NB separa más servicios, pero algunos son extensos; DC tiene utilidades probadas, pero Canvas acumula responsabilidades. Es razonable trasladar validadores y máquinas de estado a servicios Angular acotados. No hay justificación observada para React embebido, React Flow dentro de Angular o un nuevo store Zustand.

## H. Contratos frontend-backend

Los siguientes recorridos son conexiones de código reales. No todos fueron ejercitados de extremo a extremo: la columna de errores describe validaciones presentes y pruebas referenciadas, no solicitudes realizadas ahora. Las rutas se componen de core/config urls, app urls y acciones DRF; {id} es notación de parámetro, no un literal. Respuestas resumidas muestran campos relevantes y no sustituyen un esquema OpenAPI versionado.

### REST: autenticación y proyectos

| Operación | NodoBoard: componente → servicio → endpoint → backend/modelo → respuesta/estado/errores | DiagramCraft: componente → servicio → endpoint → backend/modelo → respuesta/estado/errores |
|---|---|---|
| Sesión | LoginForm/AuthService → POST /api/usuario/login/ → usuario.LoginView/serializer, User → access/refresh/user → TokenStorage y navegación; credenciales inválidas no autorizan. Registro y activación son rutas separadas; refresh /api/usuario/token/refresh/ | LoginPage → authApi → POST /api/login/ con CSRF → config.authentication.LoginView, User/sesión → usuario/sesión → App isAuthenticated. GET /api/csrf/ y /api/me/; POST /api/logout/ devuelve 204. No devuelve JWT equivalente |
| Crear proyecto | CreateProjectModal/ProjectsListPage → ProjectsService → POST /api/modelado/proyectos/ con nombre/descripción → ProyectoListCreateView y ProyectoCreateSerializer asignan propietario/UserColaborador → detalle creado → actualizar lista/cerrar modal; campos inválidos 400, autenticación requerida | NewProjectDialog/DiagramCanvas → diagramApi → POST /api/proyectos/proyectos/ con nombre → ProyectoViewSet/serializer → create_project_with_main_diagram, Proyecto/Diagrama y miembro owner → proyecto/diagrama principal → selección y carga; duplicado activo por creador 400, permisos autenticados |
| Listar/abrir | ProjectsListPage → ProjectsService GET colección; WhiteboardPage → WhiteboardApiService.getDiagrama → GET /api/modelado/proyectos/{id}/diagrama/ → DiagramaCargaInicialView → Proyecto/Entidad/Atributo/Relacion → proyecto, entidades, relaciones → reconciliarDatosDiagrama, Canvas; acceso ajeno no devuelve documento | ProjectsDialog → diagramApi GET /api/proyectos/proyectos/ con filtros → ProyectoViewSet.get_queryset/serializer; Canvas → obtenerDiagramaPrincipal, GET /api/diagramas/diagramas/?proyecto={id} si hace falta → JSON/revision → restore del store; SQL de conteo requiere PostgreSQL |
| Cambiar/eliminar | PATCH/PUT /api/modelado/proyectos/{id}/ → ProyectoDetailView/serializer → Proyecto; DELETE exige dueño. H-N01 demuestra que visualizador puede PATCH de contenido; no se comprobó que todo PATCH sea correcto por existir CRUD | PATCH/DELETE /api/proyectos/proyectos/{id}/ → ProyectoViewSet con propietario; acciones POST archivar/restaurar/duplicar → servicios/Proyecto/miembros/diagrama → proyecto o 204 → lista/selección; restauración debe respetar unicidad de nombre |
| Diagrama principal | Proyecto mismo y snapshot; no endpoint de múltiples diagramas por proyecto equivalente | diagramApi.obtenerDiagramaPrincipal usa dato embebido o primera respuesta; crearDiagramaPrincipal manda es_principal:true pero Diagrama no tiene ese campo persistente. No afirmar garantía de flag principal sólo por payload |

Las API adicionales de DC incluyen /api/proyectos/usuarios/ de lectura y /api/diagramas/clases/, atributos/, relaciones/, versiones/ como CRUD heredado. No son las operaciones que el editor React usa para crear cada clase; conservarlas como adaptador de NodoBoard expondría H-D04 y otra autoridad de datos.

### Colaboradores e invitaciones

| Recorrido | Contrato y efectos verificados por inspección |
|---|---|
| NB invitar/listar | ModalColaboradores → WhiteboardApiService → GET /api/modelado/proyectos/{id}/colaboradores/ o POST /{id}/invitar/ con email/username → ProyectoColaboradoresListView o InvitarColaboradorView/serializer → UserColaborador pendiente editor, firma/correo → respuesta de acción y recarga. Dueño requerido para invitar; usuario ya existente/membresía valida en serializer |
| NB reenviar/retirar | Mismo modal/servicio → POST /{id}/colaboradores/{colaborador_id}/reenviar/ o DELETE /{id}/colaboradores/{colaborador_id}/ → vistas de colaborador → fila de membresía → mensaje y lista. colaborador_id identifica UserColaborador, no User; no sustituir por ID de usuario DC |
| NB aceptar dentro del sistema | Header/InvitacionesService → GET /api/modelado/invitaciones/ y POST /{pk}/aceptar/ o rechazar/ → vistas directas → estado de UserColaborador → pendientes/counter y acceptedSubject para recargar proyectos. Esta cadena existe aunque I3 afecte el enlace externo |
| NB aceptar firmado | Enlace generado /invitacion/{token}; backend POST /api/modelado/proyectos/aceptar-invitacion/ AllowAny consume token firmado de 48 h. Falta ruta Angular correspondiente. No confundir con /activar/:token de cuenta ni declarar este flujo UI completo |
| DC invitar/gestionar | CollaboratorsDialog/PeopleDialog → diagramApi → POST /api/proyectos/proyectos/{id}/invitar/ con email/username/usuario_id y rol → ProyectoViewSet + serializers/permissions → InvitacionProyecto → invitación/resumen y recarga. PATCH /{id}/miembros/{usuario_id}/ cambia rol; DELETE /{id}/colaboradores/{usuario_id}/ retira/sale → eventos de proyecto y cliente. Roles owner restringidos |
| DC aceptar/rechazar | Diálogos de proyectos/personas → diagramApi → GET /api/proyectos/invitaciones/pendientes/; POST /api/proyectos/invitaciones/{id}/aceptar/ o rechazar/, reenviar/; DELETE detalle → InvitacionProyectoViewSet → invitación/miembro → listados y estado del proyecto. No equivale al token de correo NB |

### Editor y guardado: cadena de autoridad

| Operación | NB | DC |
|---|---|---|
| Crear/editar entidad | WhiteboardPage/EditorInline/propiedades → Canvas/EntityService y parser → JointJS y eventos socket; no POST individual de Entidad desde el editor. guardar_snapshot → PizarraConsumer → transacción Entidad/Atributo/Relacion y Proyecto.datos_diagrama → snapshot_guardado remapea IDs → mapas Canvas. Validación y rol por escritura insuficientes, H-N02; debe distinguirse evento visual de persistencia |
| Crear/modificar relación | Menú/modal → RelationshipService/Canvas → tipo, multiplicidad, puertos e IDs NB → evento y snapshot → Relacion.full_clean y sincronización → rel_id_map. Clase asociativa usa clase_asociacion; R3 afecta reconciliación posterior; tipo no soportado no tiene mapeo automático |
| Guardar documento | WhiteboardPage debounce → Socket.enviarMensaje guardar_snapshot → consumer guarda conjunto completo → ack exito/id_map/rel_id_map; flags guardando/error. Sin expected_revision; prueba previa demuestra borrado de ausentes por snapshot viejo |
| Sincronizar | Evento local emitido a pizarra_{id} → pizarra.evento → evento/data → Socket/Page/servicios actualizan celdas sin convertir cada evento en transacción. Presencia/bloqueos comparten canal. No hay comprobación de revisión para converger |
| DC crear entidad/relación | Canvas/PropertiesPanel → diagramStore acciones de nodos/edges; flags y permisos UI → estado local React Flow. Cambios no llaman ClaseUMLViewSet. Autosave central persiste documento completo |
| DC guardar | Canvas autosave → diagramApi.guardarDiagrama → PATCH /api/diagramas/diagramas/{id}/ con nodes, edges, expected_revision → DiagramaViewSet.perform_update + DiagramaSerializer, lock/autorización → Diagrama normalizado/revision → respuesta autoritativa y on_commit publish → store/revision; validación 400, rol denegado, conflicto 409. Edición de relaciones requiere owner/architect |
| DC sincronizar | useDiagramSocket recibe diagram.update → collaborationSync filtra revisión/autoría → Canvas invalida envíos viejos y aplica documento/store, mantiene viewport/selección. Reconexión/heartbeat del hook; no merge de operaciones. Aviso member.removed activa returnToPrincipalCanvas del cliente, pero S3 exige cierre server |

### IA, confirmación, XML y artefactos

| Operación | Cadena efectiva y diferencias |
|---|---|
| NB IA | ChatAsistenteIa → AsistenteIaService → POST /api/asistente/ejecutar-instruccion/ (y POST generar-diagrama-imagen/ para imagen), declarados en backend/asistente/urls.py → backend/asistente/views.py → proveedor con contexto → mensaje y delta de seis listas → aplicación local mediante servicios/canvas → posterior snapshot. No hay PlanIA persistido ni endpoint separado de confirmar con revisión. Pruebas F2 con proveedor falso muestran aceptación de delta mal tipado; un HTTP 200 no prueba corrección semántica |
| DC IA | DiagramCanvas/aiFlow → aiApi → POST /api/diagramas/diagramas/{id}/interpretar-ia/ con instrucción/revisión e identidad → DiagramaViewSet.interpretar_ia → ai_interpreter + ai_operations/ai_plans → PlanIA y propuesta → UI pendiente de confirmación. Confirmar → POST aplicar-plan-ia/ → plan, TTL/hash/rol/revisión → aplicar transaccionalmente → resultado/documento → store y publicación. F2-D01: modificación durante proveedor puede cambiar base del plan; no reutilizar sin corregir esa precondición en futuro |
| NB importar XML | Sidebar/Page → GeneradorService → POST /api/generador/proyectos/{id}/importar-xml/ multipart archivo_xml o contenido_xml y reemplazar_existente → ImportarDiagramaXMLView/servicio → ORM y snapshot → detail/metricas → UI recarga getDiagrama. Dueño/editor; archivo ≤10 MB, XML inválido se rechaza. No devuelve el mismo documento autoritativo ni publica actualización colaborativa desde la vista |
| NB exportar XML | Sidebar/Page → GeneradorService → GET /api/generador/proyectos/{id}/exportar-xml/ → ExportarDiagramaXMLView/xmi_exporter → datos ORM → attachment XML/blob. Lectura permitida a miembros activos, más amplia que permiso DC |
| DC preview/importar | Canvas → xmiApiContract/diagramApi → POST /api/diagramas/diagramas/{id}/importar-xmi/ multipart file, mode=replace, mapping_mode, dry_run y selección → DiagramaViewSet.importar_xmi → parse_xmi/apply_xmi_mapping/serializer → dry_run devuelve report y preview nodes/edges/xmi_ids, final guarda Diagrama y devuelve documento+report → aplicar estado, revisión y aviso. Owner/architect; XmiError/validación 400, límites de entrada. Preview no implica aprobación de una revisión futura |
| DC exportar | Canvas/diagramApi → GET /api/diagramas/diagramas/{id}/exportar-xmi/ → DiagramaViewSet.exportar_xmi/export_xmi → documento → XML attachment → descarga; owner/architect. No conectar con endpoint NB sin adaptar roles y formato |
| DC Spring Boot | Toolbar/Canvas → diagramApi → POST /api/diagramas/diagramas/{id}/generar-spring-boot/ con opciones opcionales artifact/package (UI por defecto {}) → DiagramaViewSet.generar_spring_boot → generate_spring_boot_zip/normalize_diagram → Diagrama JSON → ZIP y warnings/errores referenciados → descarga o enfoque/aviso. Owner/architect; no equivalente implementado en NB ni compilación Java real verificada |

Los nombres de clase/vista/función anteriores se contrastaron con sus archivos; las rutas se verificaron en urls.py y acciones. Se evita inventar endpoints para métodos, atributos individuales NB, conversaciones compartidas, confirmación NB o selección de build tool, que no están conectados en el estado actual.

## I. Compatibilidad de modelos de datos

| Concepto | NB: campos/restricciones | DB: campos/restricciones | Adaptación necesaria y pérdida posible |
|---|---|---|---|
| Usuario | Django User; username/email/nombres, activación y JWT | Django User; email o username, sesión/social, username derivado de correo | Mismo origen de clase no garantiza IDs/usuarios iguales; conservar identidad NB, no copiar registros ni sesión |
| Proyecto | BigAutoField; nombre150, codigo20 único, paquete_base, propietario CASCADE, JSON visual | BigAutoField; nombre200, creador CASCADE, plantilla/archivado, unicidad condicional Lower por creador | Longitud, códigos, soft lifecycle y nombres requieren reglas; no truncar sin aviso |
| Miembro | UserColaborador único usuario/proyecto, propietario/editor/visualizador y pendiente/activo | ProyectoMiembro único par, owner/architect/editor/reader; invitación separada | propietario≈owner y visualizador≈reader, pero editor NB y DC difieren en relaciones; architect sin equivalente |
| Invitación | Estado de membresía + token firmado/email; IDs de fila | InvitacionProyecto con inviter/invitee/rol/estado/fechas y unicidad pendiente | Crear traductor de estados e identidad, caducidad y permisos; no migración directa de tablas |
| Diagrama | Proyecto.datos_diagrama + tablas Entidad/Relacion | Diagrama FK Proyecto, nombre, nodes/edges, revision, varios por proyecto | Decidir un diagrama o varios; revisión debe cubrir todas las escrituras del agregado NB |
| Entidad/nodo | ID numérico, nombre150, coords floats, estado, ancho, intermedia | node.id string, position/data, kind class/entity/dto/enum/embeddable/interface | Mapa reversible de IDs/posición, kind explícito; no marcar toda clase como entity JPA |
| Atributo | FK Entidad CASCADE; 6 tipos, es_clave/es_nulo/orden | Atributos JSON con identificadores Java, tipo, flags/visibilidad y metadatos | long debe conservarse; prueba H-N05 detectó bigint→integer. IDs de atributos NB se reconstruyen |
| Métodos | Sin modelo y flujo de edición equivalente comprobado | Métodos en JSON y generación Java | No meter como atributo o texto silenciosamente; ampliación pendiente de diseño |
| Relación | FK proyecto/origen/destino CASCADE, 4 tipos, multiplicidades, puertos | edge.id/source/target string, 6 tipos, data y handles | Referencias y puertos necesitan mapa, realización/dependencia sin equivalente actual |
| Composición/agregación | Convención de extremos y tipo; sin campo whole explícito equivalente | wholeNodeId/ownerNodeId, convention target-whole-v1, roles/navegabilidad y JPA flags | No inferir whole sólo por source/target; evita invertir semántica o generar JPA incorrecto |
| Clase asociativa | Entidad.es_intermedia y Relacion.clase_asociacion SET_NULL | associationClassNodeId en edge y nodo | Enlazar por identidad; descartar heurística de primera asociación R3 como regla de conversión |
| Multiplicidad | String vacío o formatos numéricos/rango | UML general; JPA administrado restringe N,*,1,0..1,0..*,1..* y reglas de extremos | Validar dominio antes de exportar; no confundir 0..N con equivalencia sin normalización explícita |
| Revisión/historia | Sin revisión documental; snapshot no detecta obsolescencia | revision positiva grande, expected_revision; VersionDiagrama legacy adicional | Implementación futura requiere agregado y lock, no copiar historial legacy como control optimista |
| Plan IA | Sin modelo persistido equivalente | UUID, FK usuario/diagrama, operaciones/hashes/TTL/status/resultado | IDs y operación NB diferentes, atomicidad y revisión deben definirse; no copiar migraciones |
| Presencia | Diccionario por proceso; usuarios/canales | PresenciaDiagrama ORM, canal único, actividad/expiración | Adaptar a proyecto NB y usuario, múltiples pestañas, limpieza y revocación |

La equivalencia visual no asegura equivalencia semántica: un class importado no es necesariamente entity, una relación FK inferida no necesariamente asociación UML, y una arista con diamante requiere extremo whole conocido. La validación de documento del donante permite guardar modelos aún incompletos para JPA; el generador realiza validaciones adicionales. Deben distinguirse documento dibujable y documento generable.

Persistencia/migraciones: NB enlaza modelado y usuario y ha evolucionado hasta modelado/0011; DB enlaza proyectos, diagramas y auth, con datos heredados. Restricciones de nombres, CASCADE/SET_NULL, IDs y funciones RunPython impiden copiar migraciones o asumir el mismo estado aplicado. Se inspeccionaron archivos de migración, no la tabla real django_migrations ni sus datos. Las bases existentes no se abrieron ni migraron durante esta fase.

## J. Compatibilidad de dependencias

Versiones declaradas se distinguen de las instaladas observadas. No se consultó internet ni se evaluó el estado actual de vulnerabilidades; esto es compatibilidad local, no certificación de soporte o seguridad de versiones.

| Capa | NB declarado | DiagramCraft declarado/observado | Implicación |
|---|---|---|---|
| Django | >=5.2,<5.3 | 6.1.1 | No reemplazar requirements NB por el del donante; pruebas NB en venv DB no certifican Django 5.2 |
| DRF | 3.17.1 | 3.18.0 | Revisar serializers/errores/permissions en entorno real destino antes de portar |
| Channels | 4.2.2 | 4.3.2 | API cercana, pero auth/grupos/consumers distintos; ASGI y Redis deben probarse juntos |
| Channels Redis / cliente | channels-redis4.3.0, redis>=7,<8 | channels-redis4.3.0, redis5.3.1 | Rangos redis Python distintos; versión del cliente no revela versión del servidor |
| PostgreSQL driver | psycopg2-binary2.9.12 | psycopg3.3.5 y binary | Imports/configuración no intercambiables automáticamente; jsonb_array_length DC impide suite equivalente en SQLite |
| IA | google-genai2.23.0 | Uso google.genai, ausente en requirements y venv auditado | Dependencia faltante DC; mocks no prueban proveedor. Conservar abstracción/configuración NB y no claves externas |
| Plantillas | Sin generador Java equivalente | Jinja2 3.1.3 | Eventual dependencia del exportador, no de la UI; comprobar StrictUndefined y escape/rutas |
| XML | ElementTree estándar | lxml6.1.3 | Límites y parser endurecido útiles; X3 impide asumir compatibilidad sólo por usar lxml |
| Auth/config | SimpleJWT5.5.1, PyJWT2.12.1, cors4.9, Daphne4.2.3 | Sesión/allauth65.19.2, dotenv/decouple, dj-database-url, WhiteNoise y otras transitivas | No importar allauth o drivers sólo para reutilizar generación; paquetes declarados no prueban uso activo |
| Angular NB | Angular/CLI/devkit19, RxJS~7.8, zone~0.15, TS~5.6 | Sin Angular en DF | Instalados NB observados: core19.2.25, RxJS7.8.2, TS5.6.3; conservar arquitectura |
| Motor | @joint/core^4.3.3 | reactflow^11.11.4 y @xyflow/react^12.11.6 | Joint4.3.3 y ReactFlow11.11.4 observados. No mezclar contratos ni instalar ambos motores en Angular |
| UI/estado | Angular/servicios/RxJS | React/react-dom^19.2.8, Zustand5.0.15, react-icons5.7, Tailwind3.4 | Reglas adaptables; React/Zustand/JSX no necesarios para NB |
| HTTP | HttpClient/interceptor JWT | Axios1.20 y fetch credentials/CSRF | Equivalentes en transporte, no en autenticación. Conservar HttpClient |
| Router | Angular Router activo | react-router-dom7.18.3 declarado, sin imports activos observados | INVESTIGAR necesidad del donante; AppRouter vacío no justifica trasladarlo |
| Voz | API navegador en integración discutida en fase 2 | Web Speech desde Canvas/utils, no paquete de motor local | Disponibilidad depende del navegador; no implica procesamiento offline |
| Build/tests | Angular devkit/Karma/Jasmine; no target lint equivalente hallado | Vite8.2.2/plugin-react6.1, ESLint10.9, pruebas node:test | Vite6.4.3 en dependencias NB corresponde a tooling transitivo, no una app React/Vite activa |

El package-lock.json NB ya estaba modificado al comenzar; se conserva byte por byte. Los manifiestos/lock no deben fusionarse mecánicamente. @xyflow/react y react-router-dom del donante son candidatos a investigación por ausencia de imports, no una orden de eliminación; un paquete transitivo o una app vacía tampoco constituye una capacidad implementada. pip check previo pasó para paquetes instalados, pero no detecta una dependencia de aplicación ausente que nunca se instaló, como genai DC. No se instaló, actualizó ni retiró ningún paquete.

## K. Matriz técnica comparativa

Clasificación preliminar por módulo; las filas no establecen orden de ejecución, puntaje ni ranking. MIGRAR significa capacidad aprovechable ausente, sujeta al diseño y autorización posterior; no copiar archivos o ejecutar cambios. DESCARTAR se refiere a su incorporación al destino, no a borrar archivos existentes.

| Módulo | DiagramCraft | NodoBoard | Diferencias técnicas | Compatibilidad | Riesgos | Recomendación |
|---|---|---|---|---|---|---|
| Autenticación y navegación | Sesión/CSRF/allauth, App condicional | JWT y rutas/layouts Angular activos | Credenciales y UX diferentes | Baja directa | Dos sesiones, CSRF/JWT mezclados | CONSERVAR NB; no trasladar auth donante |
| Proyectos base | Proyecto/Diagrama separados | Proyecto con dominio/snapshot | Estructura y restricciones distintas | Parcial por servicios | Privacidad/nombres/IDs | CONSERVAR NB |
| Archivo/restauración/duplicación | Servicios y acciones reales | Sin equivalente completo constatado | Soft lifecycle y copia independiente | Requiere diseño | Miembros heredados/restauración conflictiva | ADAPTAR servicios y patrones |
| Invitaciones/roles | Entidad invitación, owner/architect/editor/reader | UserColaborador pendiente/activo, 3 roles | Estados, IDs y firma/correo | Parcial | Escalar privilegios o perder invitaciones | FUSIONAR capacidades con contrato NB explícito |
| Persistencia UML | JSON canónico + tablas legacy | Tablas canónicas + JSON visual | Autoridad e IDs incompatibles | No directa | Duplicidad y pérdida de semántica | CONSERVAR dominio NB; adaptar DTO |
| ORM UML legacy DC | CRUD separado aún registrado | Entidad/Atributo/Relacion ya activos | No alimenta editor actual | Redundante | H-D04 y tercera autoridad | DESCARTAR incorporación de legacy |
| Revisión/concurrencia | Lock, expected_revision, 409 | Snapshot sin revisión | Requiere agregado NB | Patrón adaptable | Omitir rutas de escritura, plan con base incorrecta | ADAPTAR |
| Validación UML/JPA | 6 tipos de relación/kinds, ownership | 4 relaciones, tipos NB | Mayor semántica y restricciones | Parcial | Inventar JPA desde dibujo | ADAPTAR validadores tras acordar datos |
| Eventos finos/canvas | Documento/revisión, React Flow | JointJS/eventos de interacción | Protocolo/motor distintos | Semántica adaptable | Dos escritores divergentes | CONSERVAR interacción NB; FUSIONAR confirmación autoritativa |
| Presencia/reconexión | ORM/heartbeat/reintento y expiración | Diccionario por proceso/sin retry efectivo | Identidad por canal y lifecycle | Parcial | Revocación S3, duplicados, múltiples pestañas | ADAPTAR con pruebas de revocación |
| Historial undo/redo | 50 snapshots locales | Sin equivalente colaborativo comprobado | No inversas multiusuario | Incierta | Revertir cambios remotos | INVESTIGAR alcance antes de portar |
| Generación Spring | ZIP Maven/Java21/Spring3.4/PostgreSQL | Sólo XML, no Java | Capacidad nueva y metadatos más ricos | Adaptador necesario | Código no compilado, tipos insuficientes | MIGRAR capacidad mediante exportador, no backend completo |
| XMI perfiles/límites | Preview/mapping/lxml/EA geometría | Fixture EA importada/ORM/XML | X3 y namespaces, IDs, límites | Parcial; incompatibilidad reproducida | Importación vacía, pérdida de información | FUSIONAR tras resolver perfil; no sustituir parser ahora |
| Preview XMI | dry_run/report/selección | Importación directa | Nuevo contrato/UI | Adaptable | Preview obsoleto al confirmar | ADAPTAR con revisión vinculada |
| Plan IA | Plan persistido, TTL/confirmación | Deltas aplicados por cliente | Autoridad y IDs diferentes | Parcial | Carrera F2 y duplicación de eventos | ADAPTAR según conclusión F2 |
| Chat único | Diana integrada a Canvas | Chat Angular existente | Framework y flujo distintos | UX adaptable | Dos asistentes divergentes | CONSERVAR chat NB; DESCARTAR segundo chat completo |
| Voz | Web Speech/utils; archivo VoiceCommand vacío | Punto de entrada del asistente Angular | Contexto/idioma/estados de voz | Patrón adaptable | Disponibilidad y cancelación no vinculada al servidor | ADAPTAR sujeto a pruebas de navegador |
| React/Zustand/Router | Motor/estado del donante; router sin imports activos | Angular/DI/RxJS | No portabilidad de componentes | Baja directa | Reescritura y dependencias innecesarias | DESCARTAR incorporación de frameworks |
| Vacíos modelador/authStore/AppRouter/etc. | Sin implementación efectiva de esas piezas | Capacidades propias existentes | Archivo no demuestra función | Sin código aprovechable | Conclusión documental falsa | DESCARTAR como módulos a trasladar |
| Accesibilidad/errores | Escape/aria-live/enfoque de errores | Roles/labels/toasts Angular | Patrones complementarios | Adaptable | Declarar cumplimiento sin prueba | FUSIONAR patrones; INVESTIGAR experiencia manual |

## L. Puntos de integración recomendados

Son propuestas técnicas para una ejecución futura, no archivos creados ni cambios autorizados. Cuando el destino no existe, se indica pendiente de diseño; no se presenta como clase implementada. Los tests enumerados son necesarios para esa eventual implementación y NO se ejecutaron en esta fase.

### Revisión del agregado y guardado autoritativo — ADAPTAR

Origen: DB/diagramas/views.py::DiagramaViewSet.perform_update, diagramas/serializers.py::DiagramaSerializer y diagramas/consumers.py::save_diagram_if_user_can_access; DF/src/utils/collaborationSync.js y DiagramCanvas. Destino: NB/backend/modelado/models.py, consumers.py, views.py, serializers.py y Angular whiteboard.page.ts, whiteboard-api.service.ts, whiteboard-socket.service.ts, whiteboard-canvas.service.ts. El servicio común de escritura y su DTO no existen en NB con ese contrato: quedan pendientes de diseño.

Endpoint implicado: PATCH de proyecto, guardar_snapshot y todas las importaciones/planes que cambien el mismo agregado. Dependencias: transacciones/locking de Django y estado RxJS; no necesita React/Zustand. Adaptar IDs numéricos/remapeo, scope Proyecto frente a Diagrama, revisión esperada, 409, publicación posterior al commit y respuesta completa autoritativa. Riesgo: implementar revisión sólo en un camino y dejar otros sobrescribir; persistir input WS sin normalizar como el donante. Pruebas futuras: dos clientes con misma revisión, rollback sin evento, permisos reevaluados, remapeos, reconexión, snapshot atrasado, importación y plan invalidado por edición concurrente.

### Validación de documento UML y ampliación semántica — ADAPTAR

Origen: DB/diagramas/serializers.py::DiagramaSerializer, foreign_keys.py y spring_generator.py::normalize_diagram; DF/src/stores/diagramStore.js y utils/xmiImport.js. Destino: modelos/serializers de NB y diagrama-parser.service.ts, whiteboard-relationship.service.ts, whiteboard-entity.service.ts, interfaces/diagrama.interface.ts y modales de propiedades. Endpoint: carga/guardado e importación, no CRUD legacy del donante.

Dependencias: esquema canónico independiente de React Flow. Traducir node.kind, IDs, tipos de atributos, source/target, handles, whole/owner, JPA flags y clase asociativa; no asignar JPA a toda Entidad sin decisión. Los campos sin destino requieren diseño de dominio, no esconderlos en JSON arbitrario. Riesgo: pérdida de realización, dependencia, métodos o semántica whole. Pruebas futuras: referencias inválidas, IDs duplicados, cardinalidades invertidas, herencia cíclica, interface/realización, tipos long, asociación-clase e ida/vuelta sin pérdida documentada.

### Ciclo de proyectos y permisos de miembros — ADAPTAR/FUSIONAR

Origen: DB/proyectos/services.py::create_project_with_main_diagram, ProyectoViewSet y permissions.py, models.py, signals.py; DF/src/components/editor/ProjectsDialog.jsx y CollaboratorsDialog.jsx. Destino: NB/backend/modelado/views.py, models.py, serializers.py, usuario/models.py y Angular dashboard/ProjectsService/InvitacionesService/ModalColaboradores. Rutas NB actuales se conservan como base; nuevas acciones de archivar/restaurar/duplicar o cambio de rol quedan pendientes de contrato.

Dependencias: auth NB y transacciones; no allauth. Traducir invitación separada a estado NB o decidir nueva entidad en otra fase, mapear rol architect explícitamente y distinguir miembro-ID de user-ID. Riesgos: heredar colaboradores al duplicar, restaurar con nombre conflictivo, exposición tras retiro y enlace I3. Pruebas futuras: dueño/miembro/ajeno en cada acción, unicidad concurrente, duplicado privado, invitación expirada, token firmado, rutas de enlace y cambios de rol con socket ya conectado. No copiar RunPython de nombres históricos del donante.

### Presencia, reconexión y revocación — ADAPTAR

Origen: DB/diagramas/models.py::PresenciaDiagrama, consumers.py::DiagramaConsumer y realtime.py; proyectos/realtime.py y consumers.py; DF/src/hooks/useDiagramSocket.js. Destino: NB/backend/modelado/consumers.py, middleware.py, realtime.py y Angular WhiteboardSocketService/WhiteboardPage/modal de colaboradores. Endpoint: /ws/pizarra/{proyecto_id}/ y operaciones REST de miembros.

Dependencias: Channels/Redis, identidad JWT, reloj/TTL y posiblemente presencia persistida adaptada al proyecto. No trasladar cookies de sesión. Reconectar debe recuperar estado autoritativo y decidir qué hacer con cambios locales; un buffer del último evento no conserva todas las operaciones. Riesgos: S3, varias pestañas por usuario, presencia fantasma, loops de reintento y eventos de una sesión antigua. Pruebas futuras: Redis con múltiples workers, expiración, salida abrupta, permisos durante conexión, cierre y group_discard al retirar miembro, sin entrega posterior, heartbeat sólo autorizado, sin doble publicación al reintentar.

### Generación Spring Boot — MIGRAR capacidad con adaptador

Origen: DB/diagramas/spring_generator.py::normalize_diagram y generate_spring_boot_zip, DiagramaViewSet.generar_spring_boot. Destino plausible: NB/backend/generador/services y views.py, Angular GeneradorService/sidebar. El nombre y ruta de un nuevo exportador/endpoint NB quedan pendientes de diseño; no existe hoy.

Dependencias: Jinja2, zipfile/tempfile y normalización UML/JPA, permisos JWT. Convertir Entidad/Atributo/Relacion al DTO del generador: tipos, identidad, nulabilidad, ownership, kinds y paquete_base. Decidir cómo representar información no disponible; rechazar modelo insuficiente con errores localizables. Riesgos: generar JPA incorrecto desde una asociación visual, nombres/rutas inseguros, suponer compilación por texto ZIP. Pruebas futuras: inspección de ZIP sin traversal/secretos, archivo Java válido con javac/Maven en entorno aislado con dependencias ya disponibles, relaciones bidireccionales, herencia JOINED, repositorios/servicios/controladores, errores referidos al elemento y soporte real del runtime declarado. No desplegar proyecto generado como parte de esta integración.

### XMI seguro y preview — FUSIONAR/ADAPTAR

Origen: DB/diagramas/xmi.py::parse_xmi, apply_xmi_mapping, export_xmi y DiagramaViewSet.importar_xmi; DF/src/api/xmiApiContract.js, utils/xmiImport.js y controles de DiagramCanvas. Destino: NB/backend/generador/services/xmi_importer.py, xmi_exporter.py, views.py, serializers.py y Angular GeneradorService/WhiteboardPage. Endpoints NB importar-xml/exportar-xml requieren una versión de contrato o una extensión compatible explícita para preview/selección.

Dependencias: parser con límites y adaptador ORM; lxml sólo si se decide después. Antes de reutilizar, corregir reconocimiento de namespaces X3 y preservar el perfil EA que NB ya importa. Preview final debe quedar ligado a revisión esperada. Mapear xmi_id a IDs NB, coordenadas, puertos/anchors, clase asociativa, multiplicidades y nombres originales. Riesgos: importar cero como éxito, reemplazo de estado más nuevo, pérdida de paquetes/extensiones o inversión whole. Pruebas futuras: fixture NB y perfiles oficiales del donante en ambos sentidos, rechazo explícito de DTD/entidades/depth/size, preview sin escritura, conflicto posterior al preview, vacío inesperado, nombres/tipos/multiplicidades/semántica/posición y validación manual con EA. No basta que el conteo coincida.

### Confirmación de IA y voz en el chat Angular — ADAPTAR

Origen: DB/diagramas/ai_operations.py, ai_plans.py, ai_interpreter.py y DiagramaViewSet.interpretar_ia/aplicar_plan_ia; DF/src/api/aiApi.js, utils/aiFlow.js, dianaVoice.js y estados de Canvas. Destino: NB/backend/asistente/views.py, sus serializers/servicios aún por diseñar, dominio modelado, Angular ChatAsistenteIa/AsistenteIaService e interfaces de IA. Contrato de interpretar/confirmar NB pendiente; no existe hoy PlanIA.

Dependencias: proveedor configurado NB, modelos/validación/revisión y DTO de instrucciones. Conservar chat existente, mapear IDs, permitir sólo operaciones tipadas, confirmación explícita en servidor y aplicar su documento autoritativo. No reproducir F2-D01: la revisión debe corresponder al contexto usado, no refrescarse tras el proveedor. Dedupe de solicitud y publicación deben especificarse por separado. Cancelación cliente y TTL no son equivalentes. Pruebas futuras: proveedor falso, delta inválido, rol denegado, plan expirado, cambio durante interpretación, confirmación repetida, publicación única definida, cancelación, recarga del cliente y voz con permisos/idioma reales bajo autorización. Memoria compartida/privada pendiente de diseño propio; no adjudicarla al donante.

### Recuperación de errores, importación y accesibilidad — FUSIONAR

Origen: DF/src/components/editor/DiagramCanvas.jsx, PropertiesPanel, utils/collaborationSync.js y hooks/useEscapeClose.js; api_errors.py y errores del generador. Destino: NB/frontend/src/app/core/services/toast-notification.service.ts, modales Angular, whiteboard.page.ts, Camera/Canvas, interfaces de error. Endpoints: cualquier guardado/importación/generación; sin nueva biblioteca de UI requerida.

Traducir error/element_id al ID NB, mostrar qué cambio fue rechazado o sustituido, mantener foco/selección/viewport sin aplicar dos veces una respuesta atrasada. Incorporar semántica de carga, Escape del overlay superior y mensajes aria-live sólo mediante componentes Angular. Riesgos: foco perdido y errores suprimidos por recarga. Pruebas futuras: respuestas fuera de orden, 400/403/409/500, lector de pantalla/teclado, múltiples diálogos y foco sobre el elemento correcto. No declarar accesibilidad completa por atributos HTML.

## M. Riesgos arquitectónicos

| Riesgo | Evidencia y grado de verificación | Consecuencia y condición para futura integración |
|---|---|---|
| Dos autoridades del diagrama | NB ORM/snapshot y R3 reproducido; DC JSON/ORM legacy por código | Elegir DTO y reglas de persistencia; no añadir una tercera copia ni reconciliar por orden |
| Autorización desigual | H-N01/H-N02 y H-D04 probados en fase 1; permisos principales DC inspeccionados | Cada entrada REST/WS/import/IA debe autorizar contra el mismo proyecto, rol y referencia destino |
| Revocación de lectura | S3: handlers reales aislados siguen enviando update; cliente se autoexpulsa | Implementación futura debe cortar canal/grupos y comprobar cambios de permiso; falta prueba red/Redis |
| Actualización perdida | NB snapshot viejo probado; DC revisiones evitan parte de conflicto; F2-D01 carrera de plan | Revisión vinculada al contexto y exigida en todos los reemplazos, incluido preview XMI |
| Importación vacía | X3 9→0 sin errores en parser del donante | Rechazar pérdida inesperada; no conectar reemplazo directo sin compatibilidad de perfil |
| Información UML/JPA insuficiente | Cuatro relaciones y seis tipos NB frente a kinds/metadatos DC | No inferir semántica por orientación/etiqueta. Diseñar datos y validaciones antes de habilitar exportación avanzada |
| Divergencia de transportes | WS DC valida pero guarda raw; REST guarda normalizado, inspección estática | Servicio único que utilice datos validados; futura prueba de equivalencia REST/WS |
| IDs y remapeos | Numéricos/temporales NB, strings DC y xmi_ids | Mapa reversible y manejo de respuestas atrasadas; no reutilizar ID de miembro como user ID |
| Eventos duplicados/obsoletos | Filtros DC y dedupe parcial; reintento IA 409 histórico | Definir identidad de operación/documento y semántica de publicación; no prometer exactly-once |
| Conectividad/presencia | NB estado por proceso/sin retry; DC TTL y buffer último evento | Reconexion con resync, múltiples procesos y pestañas; TTL no reemplaza autorización |
| Paquetes/migraciones | Django5.2 vs6.1, drivers y redis distintos; RunPython específicos | Adaptación incremental en fase autorizada, nunca copiar requirements o migraciones |
| Confianza en pruebas | DB suite previa con fallos, NB fuera de versión, Java sin compilar, EA sin abrir | Mantener etiquetas de verificación; no declarar listo para producción ni interoperabilidad total |
| Acoplamiento frontend | Canvas DC y algunos servicios NB extensos | Extraer conceptos a servicios Angular, no trasladar monolito JSX |
| UX y seguridad desacopladas | I3 enlace sin ruta; controles readonly frente a escritura permitida; S3 | Probar flujo completo y servidor, no sólo botones/deshabilitados |
| Configuración de despliegue | NB debug/hosts/CORS amplios; DC sin validador de origen WS explícito | Revisar configuración del entorno autorizado después; no se alteró aquí |

No se ejecutó escáner de vulnerabilidades ni se certifica seguridad general. Estas observaciones describen rutas de código y pruebas limitadas; no son un inventario de incidentes ocurridos. No hay puntuación de riesgo, prioridad ni ranking en esta fase.

## N. Pruebas y verificaciones

### Criterio de seguridad y evidencia conservada

Antes de las pruebas nuevas se revisaron imports, llamadas y rutas de escritura. Se evitó arrancar Django con configuraciones reales o ejecutar test runners que creen bases/migraciones en esta fase. Se creó un directorio temporal exclusivo fuera de los repositorios:

~~~text
T3 = C:\Users\juan\AppData\Local\Temp\nodoboard-phase3-e613595407db4fe5b274031a09d001d7
T1 = C:\Users\juan\AppData\Local\Temp\nodoboard-audit-52aff2032c65410ea64d503eabc879af
T2 = C:\Users\juan\AppData\Local\Temp\nodoboard-phase2-f46ef03b467846458ffc3c28469ac040
PY = D:\swProyecto\backend\.venv\Scripts\python.exe
~~~

Se copiaron sólo xmi.py y foreign_keys.py a T3/probe_pkg, sin settings/.env ni modelos. Python se ejecutó con -B/PYTHONDONTWRITEBYTECODE, TEMP/TMP apuntando a T3 y audit hook que rechaza conexiones/red y escritura fuera de T3. No hubo importación del proyecto Django ni bases de datos. Para handlers se compilaron únicamente los métodos AST originales con un objeto falso send_json/close; no se abrió event loop de red.

En Node se leyó TypeScript ya instalado en NB, se extrajo el método original mediante AST, se transpilo en memoria y ejecutó en vm con entradas sintéticas. Sin bootstrap Angular, HttpClient, compilación emitida a disco ni servidor. El script usa sólo fs de lectura, vm y assert; se desactivó compile cache. Estas comprobaciones prueban funciones concretas, no integración E2E.

Se aplicaron como guía de inspección las skills locales diagramcraft-ai-uml-platform, diagramcraft-xmi-interoperability y diagramcraft-generate-spring-boot. Sus contratos orientaron las preguntas; sus descripciones no se tomaron como prueba de que una capacidad exista. Las restricciones del usuario prevalecieron sobre ejecuciones de pruebas/migraciones sugeridas por las skills. No se utilizó un servicio externo ni un agente delegado.

### Vigencia y resultados reutilizados, sin volver a ejecutarlos

| Evidencia previa | Resultado real reutilizado | Alcance/límite vigente |
|---|---|---|
| Fase 1: AST Python | 123 archivos parseados, sin error sintáctico | No demuestra ejecución ni dependencias completas |
| Fase 1: pip check | Exit 0 en entorno instalado | No prueba completitud de requirements; genai ausente en DB |
| Fase 1: Django DB check y consistencia de migraciones en aislamiento | check exit0; dry-run histórico sin cambios detectados | Se reutiliza registro; ninguna migración ni comando de migración ejecutado en fase 3 |
| Fase 1: backend DC | 85 pruebas: 69 pasan, 1 falla, 15 errores | Fallo proyecto por expected_revision omitida en prueba vieja; errores por jsonb_array_length bajo SQLite. No suite verde ni prueba PostgreSQL |
| Fase 1: NB | 3 tests de proyectos y 5 probes aislados: 8 pasan | URLconf reducido, Daphne excluido y Django6.1 en lugar de5.2; reproduce PATCH visualizador, snapshot de visualizador/revocado, snapshot obsoleto y bigint mal tipado. No suite completa ni handshake real |
| Fase 1: XML NB | Importar/exportar/reimportar fixture: 9 entidades,33 atributos,10 relaciones | Conteos, no preservación semántica completa ni EA manual |
| Fase 1: frontend DC | 28 tests Node pasan; lint exit0; build exit0 | Tests utilitarios IA/voz/colaboración/XMI/URLs, no componentes E2E. Vite268 módulos, JS609.27kB/gzip182.72kB y CSS56.12kB según registro histórico |
| Fase 1: frontend NB | tsc exit0 | Build impedido por acceso a ancestro bajo sandbox; Karma generó bundle pero Chrome falló al iniciar GPU. Dos casos Jasmine no acreditados en ejecución |
| Fase 1: Spring | Pruebas de ZIP/texto dentro de suite | La prueba llamada generated_java_compiles no invoca compilador. No Java/Maven real |
| Fase 2: NB con proveedor falso | 7 probes pasan | Vacío400, sin clave500, mensaje conceptual200 con deltas vacíos, delta mal tipado aceptado200, JSON inválido500, contexto incompleto y outage502 tras cuatro modelos. No calidad del proveedor |
| Fase 2: DC con proveedor falso | 1 probe pasa reproduciendo carrera | Cambio durante llamada avanza revisión0→1; plan se liga a1; aplicar con1 llega a2 y sobrescribe título. Simulación secuencial de ventana, no stress test. Si cliente sigue esperando0 puede recibir409 |

Las rutas/commands/errores completos históricos están en AUDITORIA_FASE_1.md sección7 y AUDITORIA_FASE_2.md secciónK y sus temporales T1/T2. No se vuelven a ejecutar porque todos los hashes inventariados siguen idénticos y las pruebas nuevas cubren preguntas distintas. El intérprete local observado es Python3.14.7; el Python de PATH es alias no utilizable para estas verificaciones. Las dependencias venv DB no representan un entorno NB fiel.

### Pruebas adicionales realmente ejecutadas en esta fase

| Caso | Método y comando real | Resultado | Qué verifica y qué no |
|---|---|---|---|
| X3: fixture EA NB en parser DB | PY -B T3/pure_backend_probes.py, CrossXmiTests | FAIL; primera salida contó18 definiciones incluyendo extensión. Parser0nodos/0edges, errors[], warning ea_core_only | La expectativa inicial duplicaba clasificadores; no se usa18 como conteo final |
| X3: corrección de la expectativa y repetición dirigida | PY -B T3/run_xmi_final.py T3 invocó PY -B T3/pure_backend_probes.py CrossXmiTests.test_nb_ea_fixture_classifier_count_survives_diagramcraft_parser | FAIL exit1: 0 !=9 | Corrección de contador sólo en temporal; nueve packagedElement del núcleo. Se repitió únicamente este caso por necesidad. No endpoint ni escritura |
| S3: revocación/entrega posterior | Mismo primer runner Python: RevocationHandlerTests.test_member_removed_handler_does_not_close_and_later_update_is_sent | OK; cierre no llamado, posterior diagram.update enviado | OK significa reproducción del comportamiento débil esperado por el probe, no seguridad aprobada. Métodos AST reales, transporte falso; sin usuario/DB/Redis real |
| R3: relación ausente en ORM | node T3/reconcile_probe.cjs | Exit0; relación44 del snapshot reaparece en resultado con ORMrelaciones[] | Método Angular original transpilado en memoria; no se hizo guardado ni se probó persistencia de ese resultado |
| R3: entidad intermedia huérfana | Mismo runner Node | Exit0; entidad9 Unrelated se vincula a primera asociación2 | Reproduce heurística sin identidad semántica; no demuestra incidente de un proyecto real |

Son cuatro escenarios nuevos únicos: uno XMI, uno de handlers y dos de reconciliación; la ejecución dirigida XMI repite sólo el primer escenario. La salida Node dice “2 diagnostic assertions”, pero contiene tres assert.equal repartidos entre dos escenarios; no se infla el conteo de casos. Python inicial ejecutó dos tests, uno falla y otro pasa; el fallo XMI permanece tras corregir la expectativa y no se presentó como éxito.

Artefactos T3: initial-git.json, baseline.json, validity.json, source-inventory.json; snapshot.py, run_probes.py, pure_backend_probes.py, reconcile_probe.cjs, run_xmi_final.py; probe-results.json, pure-backend.log, angular-reconcile.log, cross-xmi-final.log. Las copias de módulos son snapshots de código leído, no modificaciones a su origen. El cuerpo del informe se preparó en report-body.txt fuera del repositorio antes de crear el entregable.

### Bitácora reproducible de inspección y comprobación

Las variables T1/T2/T3/PY anteriores son abreviaturas documentales de las rutas completas, no comandos que se hayan instalado en el sistema. Los comandos de inspección usaron rutas literales y parámetros de lectura. No se imprimieron .env, tokens ni credenciales en el informe.

| Comando/familia ejecutada | Propósito y resultado |
|---|---|
| Get-Item / Test-Path de las tres raíces y de AUDITORIA_FASE_3.md | Rutas existentes e identidad comprobada; informe ausente al inicio y al reanudar |
| git -c safe.directory=<raíz> --no-optional-locks -C <raíz> status --porcelain=v1 --untracked-files=all | Estado inicial, al reanudar y final. safe.directory sólo en el proceso, sin escribir config |
| Mismo prefijo git con rev-parse HEAD, branch --show-current, remote get-url origin, ls-files --cached --others --exclude-standard | Identidad, commit, rama e inventarios; ownership distinto resuelto sin cambiar permisos ni config |
| rg --files y rg -n de imports, clases, def, rutas, acciones, validadores, eventos y uso de stores | Localización de implementaciones activas y ausencia de import de Router/@xyflow en src; salida contrastada con lectura de código |
| Get-Content -LiteralPath y lecturas por rangos/Select-Object -Skip/-First | Maestro e informes, attachment fase3, skills, modelos, vistas, serializers, servicios, consumers, migraciones, tests y componentes relacionados |
| PY -B T3/snapshot.py T3 | Hashes SHA-256, inventario, comparación con T1/T2 y git inicial; 1887 archivos, ningún cambio previo detectado |
| Lectura de package.json/requirements/lock y metadatos de paquetes instalados | Versiones locales, discrepancias y dependencias activas; no instalación ni resolución remota |
| PY -B T3/run_probes.py T3 | Preparó temporales exclusivos y ejecutó Python/Node con logs. Código de retorno1 Python por XMI,0 Node |
| PY -B T3/run_xmi_final.py T3 | Repetición XMI dirigida, expectativa corregida, sigue exit1; no se repitieron los demás casos |
| Get-Content de logs/JSON T3 al reanudar | Reutilización de resultados conservados; no nueva ejecución de pruebas |
| Script final de hashes y git | Se registra su resultado al final del informe; compara baseline, commits, ramas, reportes previos y único archivo nuevo permitido |

Para reconstruir argumentos exactos de los runners consultar probe-results.json, run_probes.py y run_xmi_final.py; preservan comandos y código. Las búsquedas y lecturas repetidas no se confunden con pruebas funcionales. Algunas salidas PowerShell muestran mojibake según su codificación; el informe se escribe UTF-8 y los contenidos se leen con codificación explícita al verificarlo.

### Pruebas omitidas y por qué

| Prueba no ejecutada en esta fase | Motivo y estado pendiente |
|---|---|
| Nueva suite Django/makemigrations/migrate o fixtures contra BD | Esta fase prohíbe aplicar migraciones; test runner puede crearlas. Se reutilizó evidencia anterior y se eligieron funciones puras. Ninguna base real tocada |
| Postgres/Redis con varios clientes/workers y handshake real | Sin entorno aislado íntegramente acreditado para esta ejecución; servicios/config existentes no deben alterarse. Presencia distribuida, revocación y concurrencia integradas pendientes |
| Repetir build/lint/tsc/Karma | Código inventariado igual, resultados previos conocidos; runners pueden escribir caches/output en repos. No aporta evidencia necesaria para nuevas preguntas puras |
| Compilar/arrancar proyecto Spring generado | No se acreditó toolchain y dependencias completos en aislamiento sin descargas; no instalar ni llamar red. ZIP/texto no equivale a compilación |
| Proveedor IA real, OAuth, SMTP o reconocimiento de voz real | Prohibición de llamadas IA externas y de envío de datos; sin necesidad ni garantía de aislamiento de servicios externos. Calidad/entrega/flujo navegador pendientes |
| EA manual y navegador E2E/accessibility | No se abrió aplicación/servidor real ni modificó entorno. Interoperabilidad semántica/visual, teclado, foco y lectores pendientes |
| Reemplazo XMI vacío real en endpoint | La incompatibilidad ya se prueba en parser y el riesgo se deriva del flujo; provocar borrado no es necesario para auditoría segura |
| Reproducir normalización WS raw→DB | Requeriría ORM y datos; inspección estática suficiente para señalar riesgo como pendiente, sin inventar resultado |
| Auditoría de vulnerabilidades/actualización de paquetes | Fuera de alcance y sin red ni instalaciones; versiones locales no certifican ausencia de vulnerabilidades |

### Clasificación del estado de funcionalidades

**Verificadas mediante código y pruebas acotadas:** parsers XML en los perfiles explícitamente probados; incompatibilidad X3; reconciliación R3; comportamiento aislado S3; utilidades Node cubiertas históricamente; vulneraciones de autorización/obsolescencia previas y carrera IA con mocks. “Verificada” describe el comportamiento observado, incluso cuando es un defecto.

**Parcialmente verificadas:** CRUD/proyectos y permisos en entornos de prueba limitados, persistencia y sincronización general, planes IA, normalización, Spring por inspección ZIP/texto, XMI por conteos/perfiles y UX por fuente. Las rutas y conexiones están implementadas, pero eso no certifica el flujo completo desplegado.

**Pendientes de comprobar:** conjunto backend con PostgreSQL y dependencias de cada proyecto, Redis/multiworker y revocación real, compilación Java, EA semántico/visual, navegador/voz/accesibilidad, entrega SMTP/OAuth/proveedor real y garantías de convergencia/idempotencia en fallos. **No implementado o no conectado en el estado auditado:** Spring en NB, revisión/plan confirmable NB equivalente, memoria conversacional compartida/privada equivalente, ruta UI del token de invitación NB y los cinco archivos React vacíos. Ningún archivo relacionado se tomó como prueba suficiente de funcionalidad.

## O. Recomendaciones técnicas preliminares

1. **¿Qué módulos backend DC podrían aprovecharse?** Validadores de DiagramaSerializer/foreign_keys, patrón transaccional de revisión, servicios de ciclo de proyectos, presencia con actividad, operaciones/planes IA, Spring Boot ZIP y límites/preview XMI. El parser XMI requiere resolver X3; los planes, la carrera F2; WS, normalización/revocación. Son capacidades a adaptar al dominio NB, no paquetes listos para copiar.
2. **¿Qué backend NB conservar?** core y autenticación JWT, usuario y membresías con reglas revisadas, Proyecto/Entidad/Atributo/Relacion como base de dominio, rutas ya consumidas por Angular, interacción colaborativa y generador XML que procesa su fixture actual. Conservar no significa dar por correctas sus autorizaciones o su concurrencia; H-N01/H-N02/R3 requieren trabajo futuro autorizado.
3. **¿Qué lógica React vale adaptar a Angular?** Filtros de revisión y aplicación autoritativa de collaborationSync, invalidación de autosave atrasado, presencia/reconexión, preview XMI, estados confirmar/aplicar del asistente, voz como entrada del mismo chat, enfoque de errores y cierre de diálogos. Extraer conceptos a servicios/componentes Angular; no JSX/ReactFlow/Zustand.
4. **¿Qué sería redundante?** Segunda autenticación/sesión, segundo chat completo, CRUD UML legacy DC y su app modelador vacía, migración de router/store/páginas vacíos y framework React en destino. Las dependencias sin imports deben investigarse, no borrarse por esta conclusión. Un endpoint duplicado sin autoridad común añade riesgo y no capacidad.
5. **¿Qué modelos son incompatibles?** Proyecto con snapshot frente a Diagrama separado; UserColaborador con estado frente a InvitacionProyecto+ProyectoMiembro; IDs numéricos frente a strings/UUID; cuatro relaciones y tipos limitados frente a kinds/métodos/JPA/ownership; presencia y planes inexistentes equivalentes en NB. Las FK, longitudes, nombres únicos y migraciones tampoco coinciden. Requiere contrato y mapa explícitos.
6. **¿Qué contratos necesitan adaptación?** Session/CSRF a JWT; /api/proyectos/proyectos y /api/diagramas/diagramas a rutas NB; documentos nodes/edges a ORM/snapshot; expected_revision/409 y respuesta autoritativa; IDs de miembros, roles/invitaciones; interpretar/confirmar plan; archivos file/dry_run/mapping frente a archivo_xml/reemplazar_existente; generación ZIP y errores element_id. No existen endpoints NB nuevos autorizados o implementados por este informe.
7. **¿Qué WebSocket conservar/mejorar?** Conservar interacción fina y grupos de pizarra NB. Adaptar revisión, heartbeat, presencia por canal, reconexión con resync y publicación posterior al commit. Revalidar permiso en toda escritura y revocar también lectura; S3 demuestra que obediencia del cliente no basta. Buffer de un evento, locks visuales y transacciones no equivalen a cola durable o convergencia multiusuario.
8. **¿Qué ventajas reales ofrecen Spring/XMI?** Spring añade exportación que NB no tiene, con validación UML/JPA y estructura por capas; su compilación real está pendiente. XMI donante añade preview/selección, límites y geometría, mientras NB tiene evidencia sobre su fixture EA específica. La ventaja es complementaria: X3 descarta reemplazo directo y exige pruebas cruzadas y rechazo de vacío inesperado.
9. **¿Principales riesgos?** Autoridades duplicadas, autorización inconsistente, sobrescritura por concurrencia, importación vacía, semántica UML/JPA e IDs perdidos, revocación incompleta, dependencias incompatibles y confianza excesiva en pruebas parciales. Se describen en M sin puntajes ni orden de implementación.
10. **¿Qué investigar antes de implementar?** DTO autoritativo y alcance de revisión, semántica de roles/whole/kinds, todas las rutas de escritura/publicación, preview ligado a revisión, namespaces EA y preservación semántica, toolchain Spring, entorno NB Django5.2 y PG/Redis, idempotencia y reconexión, memoria conversacional del requisito, y accesibilidad/navegador. El diseño de módulos nuevos está pendiente; este informe no es plan definitivo ni autorización para crearlos.

Se ejecutó únicamente la comparación técnica autorizada y las verificaciones adicionales seguras. No se instalaron/actualizaron dependencias, aplicaron migraciones, editaron configuraciones, enviaron datos a proveedores IA, implementaron módulos, hicieron commits/pushes o desplegaron aplicaciones. Se detiene el trabajo al entregar este informe y se espera autorización expresa para otra ejecución.

### Verificación final de integridad

El bloque siguiente se añade al crear el entregable, después de comparar el estado inicial con el actual. Incluye archivos no rastreados inventariados para que la comprobación no dependa únicamente de Git.

~~~text
D:\Informatica\8vo Semestre\sw1-2-2026\pizarra-colaborativa
HEAD df5430d221ddfbdc23e0a7882e535dc402ceafc4; rama feat/integrar-diagramcraft
 M frontend/package-lock.json
?? AUDITORIA_FASE_1.md
?? AUDITORIA_FASE_2.md
?? AUDITORIA_FASE_3.md
?? AUDITORIA_MAESTRA.md
?? auditoria-diagramcraft-nodoboard.code-workspace
?? debug.log
D:\swProyecto\backend
HEAD 125dc3b72fed6a829299d5733f31277d0c789a1c; rama main
(limpio)
D:\swProyecto\frontend
HEAD e200fc82b2fa6cb3b79e62b5411a6942ccd0cc7a; rama main
(limpio)
~~~

Comparación SHA-256: 1887 archivos existentes comprobados; 0 diferencias. Maestro e informes de fases 1 y 2 incluidos y conservados.

Git: ramas, commits y cambios preexistentes conservados. Único archivo nuevo no ignorado: AUDITORIA_FASE_3.md. No se revirtió ningún cambio.

La comprobación cubre el inventario de archivos rastreados/no ignorados, no todos los archivos ignorados del entorno. Las pruebas y el staging se realizaron en T3. No se detectaron alteraciones de archivos existentes inventariados.

Nota de cierre: una comprobación posterior por Python -c terminó con SyntaxError al construir el subcomando Git por escapes de PowerShell. La parte previa sí confirmó los 1887 hashes sin diferencias. Se sustituyó ese comando por T3/final-read.py, de sólo lectura, para verificar de nuevo hashes, Git, secciones y UTF-8; no se repitieron pruebas funcionales ni se modificaron otros archivos.
