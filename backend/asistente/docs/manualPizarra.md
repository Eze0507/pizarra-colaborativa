# Manual de Usuario y Procesos de la Pizarra Colaborativa (NodoBoard CASE)

## Descripción General
La **Pizarra Colaborativa** es el entorno principal de diseño visual y modelado conceptual de bases de datos de la herramienta CASE. Diseñada con un enfoque centrado exclusivamente en el diseño de datos, emula una pizarra física interactiva donde múltiples ingenieros y diseñadores colaboran de forma simultánea y en tiempo real. 

La herramienta incorpora control avanzado de concurrencia y exclusión mutua para evitar conflictos de edición, auditoría de consistencia del modelo, capacidades de inteligencia artificial generativa (diseño mediante comandos de voz/texto, transformación de bocetos dibujados a mano y asesoría de un Agente Senior), e interoperabilidad model-driven capaz de convertir los diagramas de clases en código backend ejecutable (**Java 17+ / Spring Boot 3+**) y en archivos estándar de la industria (**OMG UML / XMI 2.1 para Enterprise Architect**).

---

## Estructura de la Interfaz de la Pizarra

La interfaz de trabajo se compone de 5 áreas principales:

1. **Barra Lateral Izquierda (Sidebar)**:
   - **Cabecera**: Logotipo oficial de NodoBoard, título del proyecto editable in-place, indicador de autoguardado (nube/check), indicador de estado de la conexión WebSocket (*«En vivo»*), pila de avatares de colaboradores conectados y botón de administración de equipo (*«Colaboradores»*).
   - **Pestaña «Elementos» (Toolbox)**: Tarjeta interactiva de *«Nueva Entidad»* (tabla/clase relacional) lista para hacer clic o arrastrar (`drag & drop`) al lienzo, y panel de *«VALIDACIÓN DEL MODELO»* con selector de perfiles (UML, Java, JPA) y visualizador de hallazgos.
   - **Pestaña «Boceto IA»**: Zona de carga de fotografías de diagramas en papel o pizarra física (JPG, PNG, WebP), campo de instrucciones contextuales y botón generador asistido por visión artificial.
   - **Pie del Sidebar**: Acciones globales del proyecto: *«Descargar Spring Boot (ZIP)»*, *«Exportar XML (EA 2.1)»*, *«Importar XML (EA 2.1)»*, enlace de retorno al *«Dashboard»*, interruptor de tema (*Modo Claro / Modo Oscuro*) y botón de *«Cerrar sesión»*.
   - **Control de Colapso**: Botón superior para alternar entre el sidebar expandido y el *Modo Rail Inteligente* (barra compacta de iconos).

2. **Lienzo Infinito (JointJS Canvas)**:
   - Área de trabajo gráfica donde se renderizan las clases/entidades, atributos, tipos de datos, claves primarias y relaciones UML. Permite desplazamiento libre (paneo), selección múltiple, arrastre de elementos y trazado interactivo de enlaces entre puertos perimetrales.

3. **Barra Flotante Inferior Central de Instrucciones IA (Chat y Voz)**:
   - Píldora interactiva para controlar el lienzo mediante lenguaje natural: entrada de texto, botón de dictado por voz mediante micrófono (con soporte para mantener presionada la barra espaciadora), y botones de *Deshacer* (`↶` / `Ctrl+Z`) y *Rehacer* (`↷` / `Ctrl+Y`).

4. **Botón Flotante y Panel del Agente Senior Colaborativo (Esquina Inferior Derecha)**:
   - Asesor técnico en arquitectura de datos compartido con todo el equipo. Cuenta con un interruptor para alternar entre *IA local* (Ollama / Qwen) y *Google Gemini* (con respaldo local), permitiendo resolver dudas de normalización, cardinalidades y buenas prácticas.

5. **Controles Flotantes de Navegación y Zoom (Esquina Inferior Izquierda)**:
   - Botonera flotante sobre el lienzo para acercar zoom (`+`), alejar zoom (`-`) y restablecer la vista al 100% (`↺`).

---

## Procesos y Actividades de la Pizarra

### 1. Diseñar Entidades y Atributos en el Lienzo
Permite agregar clases, tablas relacionales o entidades intermedias al modelo conceptual.

#### Pasos a seguir:
1. En el sidebar izquierdo, selecciona la pestaña **«Elementos»**.
2. En la sección *«MODELADO DE DATOS»*, haz clic sobre la tarjeta **«Nueva Entidad»** (el elemento se insertará automáticamente en el centro de la pantalla), o arrástrala manteniendo presionado el botón del ratón hasta las coordenadas deseadas en el lienzo (`drag and drop`).
3. Para configurar sus atributos, tipos y reglas:
   - Haz doble clic sobre la entidad en el lienzo (o selecciónala y haz clic derecho para abrir el menú contextual y pulsar **«Propiedades»**).
   - Se abrirá la ventana modal **«Propiedades de la Entidad»**.
4. En la pestaña general del modal:
   - Modifica el **«Nombre de la Entidad»** (se recomienda usar formato `PascalCase` sin espacios, por ejemplo: `Cliente`, `DetalleFactura`).
   - Selecciona el **«Clasificador UML»**: *Clase*, *Entidad persistente* (requerida para persistencia de base de datos) o *Interfaz*.
   - Marca la casilla **«Abstracta»** si la clase no debe instanciarse directamente.
   - Selecciona el **«Estado»**: *Activo*, *Bloqueado* o *Papelera*.
5. En la sección **«Atributos del Modelo»**:
   - Presiona el botón **«+»** para agregar un nuevo atributo.
   - Escribe el nombre del atributo (por ejemplo: `id`, `nombre`, `precio`, `fecha_creacion`).
   - Selecciona el tipo de dato: `string`, `integer`, `long`, `double`, `boolean`, `date`.
   - Marca la casilla **«PK»** si el atributo representa la clave primaria de la tabla.
   - Marca o desmarca la opción **«Nullable»** para permitir o prohibir valores nulos.
   - Para eliminar un atributo no deseado, presiona el icono de papelera a la derecha de la fila.
6. Presiona el botón **«Guardar cambios»**. La entidad se actualizará de inmediato en el lienzo y se sincronizará con todos los colaboradores conectados.

---

### 2. Establecer y Configurar Relaciones entre Entidades
Permite definir las asociaciones, multiplicidades y dependencias estructurales entre dos clases.

#### Pasos a seguir:
1. Pasa el cursor sobre la entidad de origen en el lienzo para visibilizar sus **puertos de conexión perimetrales** (puntos circulares en sus bordes superior, inferior, izquierdo y derecho).
2. Haz clic y mantén presionado el botón principal del ratón sobre uno de los puertos.
3. Arrastra la línea de conexión hacia la entidad de destino hasta situar el cursor sobre uno de sus puertos perimetrales y suelta el botón.
4. Se desplegará inmediatamente el menú flotante interactivo de **Tipo de Relación UML**:
   - **Asociación**: Relación estructural básica entre dos entidades independientes.
   - **Agregación**: Relación "todo-parte" débil (el componente puede existir sin el todo).
   - **Composición**: Relación "todo-parte" fuerte (el ciclo de vida del componente depende del todo).
   - **Herencia / Generalización**: Relación jerárquica de subtipo/superclase.
   - **Implementación**: Realización de una interfaz por parte de una clase.
5. Selecciona el tipo deseado; a continuación se desplegará el menú de **Cardinalidad / Multiplicidad**:
   - Elige la combinación adecuada para los extremos: `1 a 1`, `1 a *`, `* a *`, `0..1 a 1`, etc.
6. Para personalizar roles o navegabilidad:
   - Haz doble clic sobre la línea de relación o abre su menú contextual y presiona **«Propiedades»**.
   - Se abrirá la ventana modal **«Propiedades de la Relación»**.
   - En el campo **«Nombre de la Relación / Rol»**, escribe una descripción (ej. `contiene`, `pertenece_a`, `administra`).
   - Define los roles en los extremos (*Rol origen* y *Rol destino*).
   - Ajusta las casillas de **«Navegable hacia origen»** y **«Navegable hacia destino»**.
   - Presiona **«Guardar cambios»** (o **«Eliminar relación»** si deseas suprimirla).

---

### 3. Modificar, Mover y Eliminar Elementos en el Lienzo

#### Pasos a seguir:
1. **Mover elementos**: Haz clic sobre cualquier entidad y arrástrala por el lienzo. Si otros colaboradores están observando la pantalla, verán el movimiento sincronizado en tiempo real.
2. **Edición rápida inline**: Haz un solo clic sobre el encabezado de una entidad para habilitar el editor flotante directo sobre la figura y modificar su nombre sin necesidad de abrir la ventana modal completa.
3. **Menú contextual rápido y Eliminación**: Haz clic derecho sobre cualquier figura o relación en el lienzo (el Asistente de Ayuda iluminará una entidad como ejemplo cuando consultes cómo eliminarla):
   - **Propiedades**: Abre el formulario completo de atributos o cardinalidades.
   - **Agregar etiqueta**: Permite asociar una nota descriptiva flotante.
   - **Eliminar**: Suprime la entidad o relación seleccionada del diagrama.
   - **Paso a paso para eliminar una entidad**:
     a. Ubica la entidad que deseas eliminar en el lienzo.
     b. Haz clic derecho sobre la figura de la entidad para desplegar su menú contextual.
     c. Selecciona la opción **«Eliminar»** (`btn-eliminar-contextual`). La entidad y sus enlaces se eliminarán inmediatamente.
4. **Deshacer y Rehacer**:
   - Para revertir la última acción gráfica, presiona el botón **«↶»** en la barra inferior o la combinación de teclas `Ctrl + Z`.
   - Para restablecer una acción deshecha, presiona el botón **«↷»** en la barra inferior o la combinación `Ctrl + Y`.

---

### 4. Validar la Consistencia del Modelo Conceptual
Permite someter el diagrama a un motor de auditoría formal para garantizar que cumpla con los estándares de modelado conceptual antes de exportar o generar código.

#### Perfiles de Validación Soportados:
- **UML**: Valida convenciones de nombres, relaciones válidas, cardinalidades coherentes y restricciones formales del estándar OMG UML.
- **Java**: Verifica que los nombres de entidades y atributos sean identificadores válidos en Java (sin espacios, caracteres prohibidos ni palabras reservadas) y que los tipos de datos sean compatibles.
- **JPA**: Audita requisitos estrictos de persistencia relacional ORM (presencia de clave primaria `PK`, relaciones `N:M` con clases intermedias y tipos compatibles con bases de datos).

#### Pasos a seguir:
1. En el sidebar izquierdo, asegúrate de estar en la pestaña **«Elementos»**.
2. Desplázate hacia abajo hasta la sección **«VALIDACIÓN DEL MODELO»**.
3. En el selector desplegable, elige el perfil a auditar: `UML`, `Java` o `JPA`.
4. Haz clic en el botón **«Validar»**.
5. El sistema evaluará el modelo y mostrará la tarjeta de resultado:
   - **Modelo válido**: Indicador verde con el desglose de hallazgos.
   - **Modelo con errores**: Indicador rojo con la lista detallada de observaciones clasificadas en *Errores*, *Advertencias* e *Informativos*.
6. Haz clic sobre cualquier hallazgo de la lista: el sistema desplazará y centrará automáticamente la cámara del lienzo sobre la entidad o relación observada para que puedas corregirla de inmediato.

---

### 5. Generar Código Backend Completo (Spring Boot / Maven)
Transforma el diagrama de clases conceptual confirmado en una aplicación backend completa, desacoplada y lista para producción en **Java 17+ / Spring Boot 3+**, empaquetada en un archivo comprimido `.zip`.

#### Arquitectura del Código Generado:
- **Capa Modelo (`model`)**: Clases `@Entity` y `@Table` con anotaciones JPA completas (`@Id`, `@GeneratedValue`, `@Column`, `@OneToMany`, `@ManyToOne`, `@ManyToMany`).
- **Capa Repositorio (`repository`)**: Interfaces `@Repository` que extienden de `JpaRepository` con operaciones CRUD y búsquedas parametrizadas.
- **Capa Servicio (`service`)**: Clases `@Service` con transaccionalidad `@Transactional` y métodos de lógica de negocio.
- **Capa Controlador (`controller`)**: Controladores REST `@RestController` con endpoints HTTP (`GET`, `POST`, `PUT`, `DELETE`) documentados y listos para consumir desde frontend o Postman.
- **Configuración (`pom.xml`, `application.properties`)**: Configuración Maven completa con dependencias de Spring Boot Starter Web, Spring Boot Starter Data JPA y base de datos PostgreSQL/H2.

#### Condiciones y Requisitos Previos para Poder Generar:
Para que el sistema habilite la generación del backend, deben cumplirse rigurosamente las siguientes condiciones:
1. **Permiso de Usuario**: Rol de *Propietario*, *Editor* o *Visualizador* con acceso al proyecto.
2. **Conexión en Vivo Activa**: El indicador de la cabecera debe estar en verde (**«En vivo»**). Si el WebSocket está desconectado o reconectando, el botón se bloquea.
3. **Estado Guardado y Sincronizado**: El indicador de autoguardado debe mostrar **«Guardado»**. No deben existir guardados en proceso (*«guardando»*) ni fallos de red (*«error»*).
4. **Sin Conflictos de Revisión**: La versión local del cliente debe coincidir exactamente con la revisión canónica almacenada en la base de datos del backend (`conflicto: false`).
5. **Modelo Válido (Reglas JPA / Java)**:
   - Cada clase a persistir debe poseer al menos un atributo marcado como clave primaria (`PK`).
   - Los nombres deben respetar las convenciones de Java (`JAVA_NAMING_CONVENTION`) y no coincidir con palabras reservadas.
   - Los tipos de datos deben ser los soportados (`string`, `integer`, `long`, `double`, `boolean`, `date`).
6. **Formulario Correcto**: Nombre del proyecto en minúsculas y guiones (ej. `sistema-ventas`), paquete base válido con al menos dos segmentos (ej. `com.empresa.ventas`), y jerarquía de capas coherente.

#### Tutorial Paso a Paso:
1. Haz clic en el botón destacado del pie del sidebar: **«Descargar Spring Boot (ZIP)»**.
2. Se abrirá la ventana modal **«Generación Java»**.
3. En el campo **«Nombre del proyecto»**, escribe el identificador para el artefacto Maven (ej. `gestion-inventario`).
4. En el campo **«Paquete base Java»**, escribe el paquete raíz (ej. `com.miempresa.inventario`).
5. En la sección **«Capas»**, activa las capas requeridas:
   - *Modelo*
   - *Repositorio* (requiere Modelo)
   - *Servicio* (requiere Repositorio y Modelo)
   - *Controlador* (requiere Servicio, Repositorio y Modelo)
   *(Al activar una capa superior, el modal marca automáticamente sus dependencias previas).*
6. Verifica que no existan avisos rojos de bloqueo y presiona **«Generar y descargar»**.
7. El sistema compilará la revisión autoritativa y el navegador descargará automáticamente el archivo `.zip`.
8. Descomprime el archivo `.zip`, abre una terminal en la carpeta y pon en marcha la aplicación con:
   ```bash
   mvn clean install
   mvn spring-boot:run
   ```
   La API REST quedará escuchando en `http://localhost:8080/`.

#### Tabla de Resolución de Mensajes de Bloqueo:

| Mensaje en pantalla | Causa principal | Cómo resolverlo |
| :--- | :--- | :--- |
| **«Esperando la confirmación del autoguardado.»** | Hay modificaciones recientes en el lienzo guardándose. | Espera 2 segundos a que el indicador cambie a «Guardado» o presiona «Guardar ahora» dentro del modal. |
| **«El último guardado no fue confirmado por el servidor.»** | Fallo de conexión o microcorte durante el guardado. | Verifica tu conexión a internet o recarga la página. |
| **«Resuelve el conflicto de revisión antes de generar.»** | Otro usuario modificó el diagrama al mismo tiempo. | Espera la sincronización automática o pulsa «Recuperar estado remoto». |
| **«La conexión no permite certificar la revisión confirmada.»** | El WebSocket de tiempo real se desconectó. | Aguarda a que el indicador vuelva a mostrar «En vivo». |
| **«El modelo no es válido para la generación solicitada.»** | Entidades sin clave primaria (PK) o nombres incompatibles. | Ejecuta el validador con perfil JPA y corrige los hallazgos en rojo. |
| **«Cada segmento debe ser Java válido, en minúsculas y no reservado.»** | Paquete base mal formado o con palabras como `class`, `void`. | Usa un formato estándar como `com.empresa.proyecto`. |

---

### 6. Consultar al Agente Senior Colaborativo
El Agente Senior es un asistente de diseño de software e ingeniería de datos integrado en la pizarra que asesora al equipo sobre normalización relacional, arquitectura de datos y modelado UML en tiempo real.

#### Pasos a seguir:
1. En la esquina inferior derecha de la pantalla, haz clic en el botón flotante **«Agente Senior»**.
2. Se desplegará el panel del chat interactivo.
3. *(Opcional)* En la cabecera del chat, utiliza el interruptor **«IA local»**:
   - **Desactivado (por defecto)**: La consulta es procesada por **Google Gemini** con alta capacidad de razonamiento contextual, utilizando el agente local como respaldo ante problemas de conectividad.
   - **Activado**: La consulta es respondida de forma directa por el modelo local (**Ollama / Qwen**) alojado en tu infraestructura sin enviar datos al exterior.
4. En el campo inferior con el placeholder *«Pregúntale al Senior»*, escribe tu duda técnica (por ejemplo: *"¿Es conveniente normalizar la dirección del Cliente en una entidad separada?"* o *"¿Falta alguna clave foránea en la relación Pedido-Producto?"*).
5. Presiona `Enter` o el botón de enviar.
6. La respuesta se mostrará formateada en el chat y quedará sincronizada para todos los colaboradores del proyecto.

---

### 7. Asistente IA de Modelado por Comandos de Voz y Lenguaje Natural
Permite modificar el diagrama de clases sin interactuar con los menús manuales, simplemente dictando o escribiendo instrucciones operativas.

#### Pasos a seguir:
1. Ubica la píldora flotante inferior central de la pantalla.
2. **Para dictar por voz**:
   - Haz clic sobre el icono de micrófono (o mantén presionada la **barra espaciadora** de tu teclado mientras hablas).
   - El anillo pulsante azul indicará que el sistema está escuchando.
   - Pronuncia una instrucción clara, por ejemplo: *"Crea la clase Producto con id, nombre y precio"*, o *"Relaciona Cliente con Factura de uno a muchos"*.
   - Suelta la barra espaciadora o vuelve a hacer clic en el botón de micrófono para enviar.
3. **Para escribir por texto**:
   - Haz clic en el campo de texto de la píldora, escribe la instrucción y presiona `Enter`.
4. El sistema procesará el comando con IA generativa, calculará las modificaciones delta y dibujará automáticamente las entidades o relaciones en el lienzo.

---

### 8. Generar Diagrama desde un Boceto Dibujado a Mano (Boceto IA)
Permite transformar una fotografía o dibujo hecho a mano alzada en una pizarra física o en papel directamente en entidades y relaciones UML en el lienzo digital.

#### Pasos a seguir:
1. En el sidebar izquierdo, haz clic en la pestaña **«Boceto IA»**.
2. En la zona de carga (*dropzone*), haz clic para seleccionar una imagen desde tu equipo o arrastra un archivo en formato **JPG**, **PNG** o **WebP**.
3. Verifica la previsualización del boceto cargado.
4. *(Opcional)* En el campo **«Instrucciones opcionales»**, añade contexto adicional (por ejemplo: *"Ignora el recuadro tachado en la esquina y asegúrate de que Cliente tenga clave primaria id"*).
5. Haz clic en el botón **«Generar Diagrama con IA»**.
6. El modelo de visión artificial analizará la imagen, identificará las clases, atributos y conectores, e insertará los elementos estructurados en tu pizarra colaborativa.

---

### 9. Interoperabilidad: Exportar e Importar XML 2.1 (Enterprise Architect)
Garantiza que el diseño conceptual no quede aislado, permitiendo el intercambio bidireccional con herramientas CASE estándar de la industria mediante el formato OMG UML / XMI 2.1.

#### Exportar a XML:
1. En el pie del sidebar izquierdo, haz clic en el botón **«Exportar XML (EA 2.1)»**.
2. El sistema empaquetará el diagrama actual en un archivo estructurado `.xml`.
3. El archivo se descargará en tu navegador bajo el formato `[CODIGO_PROYECTO]_diagrama_ea.xml`.

#### Importar desde XML:
1. En el pie del sidebar izquierdo, haz clic en el botón **«Importar XML (EA 2.1)»**.
2. Selecciona un archivo `.xml` o `.xmi` exportado previamente desde Enterprise Architect o desde NodoBoard.
3. El sistema procesará las etiquetas XMI, reconstruirá las clases, atributos, multiplicidades y estereotipos, y los colocará ordenadamente en el lienzo de trabajo.

---

### 10. Administrar Colaboradores del Proyecto
Permite al propietario del proyecto invitar nuevos miembros, consultar el estado de las solicitudes y revocar accesos.

#### Pasos a seguir:
1. En la cabecera del sidebar izquierdo, presiona el botón **«Colaboradores»**.
2. Se abrirá la ventana modal **«Colaboradores del Proyecto»**.
3. **Para invitar un nuevo colaborador** *(Solo propietarios)*:
   - En el campo de búsqueda, escribe el nombre de usuario (`username`) o el correo electrónico (`email`) de la persona a invitar.
   - En el menú desplegable de resultados, haz clic sobre el usuario encontrado.
   - Haz clic sobre el icono de carta/sobre que aparece junto al campo.
   - Se abrirá la confirmación: revisa los datos del usuario y presiona **«Enviar invitación»**.
   - El invitado recibirá una notificación en su Dashboard y un correo con el enlace de acceso seguro.
4. **Revisar el equipo del proyecto**:
   - En la lista inferior puedes observar a todos los miembros, identificando al *Propietario*, los colaboradores *Activos* (invitación aceptada) y las invitaciones *Pendientes*.
5. **Reenviar una invitación pendiente**:
   - Si un usuario aún no ha respondido la solicitud, el propietario puede presionar el botón **«Reenviar»** en la fila del colaborador para enviarle un recordatorio.
6. **Eliminar o revocar acceso a un colaborador**:
   - En la fila del colaborador que deseas desvincular, presiona el botón **«Eliminar»**.
   - El botón solicitará confirmación (**«¿Confirmar?»**); haz clic de nuevo para remover al usuario del proyecto de forma inmediata.

---

### 11. Renombrar el Proyecto en Tiempo Real
Permite actualizar el nombre representativo del espacio de trabajo sin salir de la pizarra.

#### Pasos a seguir:
1. Dirígete a la parte superior de la barra lateral izquierda (debajo del logo).
2. Haz clic sobre el nombre actual del proyecto o sobre el icono de lápiz situado a su derecha.
3. El texto se convertirá en un campo editable. Escribe el nuevo nombre deseado (hasta 100 caracteres).
4. Presiona la tecla `Enter` o haz clic fuera del campo (`blur`) para confirmar el cambio.
   *(Para cancelar la edición sin guardar, presiona la tecla `Escape`).*
5. El nuevo título se guardará en la base de datos y se actualizará automáticamente en las pantallas de todos los colaboradores conectados.

---

### 12. Navegación del Lienzo, Paneo y Controles de Zoom
Permite desplazarse con comodidad a lo largo de diagramas extensos.

#### Métodos de Navegación:
- **Desplazamiento / Paneo (Pan)**: Haz clic sobre cualquier zona vacía del lienzo y arrastra el ratón para desplazar la cámara en cualquier dirección.
- **Zoom con rueda del ratón**: Gira la rueda hacia arriba para acercar el lienzo o hacia abajo para alejarlo manteniendo el puntero como punto focal.
- **Controles flotantes de Zoom**:
  - En la esquina inferior izquierda, presiona **«+»** para aumentar el nivel de zoom.
  - Presiona **«-»** para reducir el nivel de zoom.
  - Presiona el porcentaje central (o el botón de reinicio **«↺»**) para restablecer la vista exactamente al **100%**.

---

### 13. Preferencias de Visualización y Navegación Global

#### Colapsar y Expandir el Sidebar (Modo Rail Inteligente):
- Para aprovechar el ancho completo de la pantalla, haz clic en el botón de flecha (`<`) en la esquina superior derecha del sidebar.
- La barra lateral se contraerá en un **Rail Inteligente** ultra compacto mostrando únicamente los iconos de las herramientas y el estado de sincronización.
- Para volver a expandir el sidebar, haz clic sobre el botón de flecha (`>`) o sobre el icono de NodoBoard en el rail.

#### Alternar Modo Oscuro / Modo Claro:
- En la parte inferior del sidebar, presiona el icono de **Luna** (para activar el modo oscuro) o el icono de **Sol** (para activar el modo claro).
- La pizarra adaptará el contraste de fondo, las cuadrículas, las tarjetas y los menús a tus preferencias visuales.

#### Volver al Dashboard o Salir de la Cuenta:
- Para regresar al listado general de proyectos, haz clic en el botón **«Dashboard»** situado en el pie del sidebar.
- Para salir del sistema, presiona el icono de **Cerrar sesión** (`🚪`); tu sesión se cerrará de forma segura y volverás a la pantalla de login.

---

### 14. Control de Sincronización en Tiempo Real y Resolución de Conflictos

La pizarra cuenta con un motor reactivo basado en WebSockets y exclusión mutua que garantiza la integridad del modelo conceptual entre diseñadores concurrentes.

#### Indicadores de Estado en la Cabecera:
1. **Indicador WebSocket**:
   - **«En vivo»** (Punto verde): Conexión activa y certificada en tiempo real. Todos los cambios se emiten y reciben instantáneamente.
   - **«Reconectando…»** (Punto amarillo): Microcorte de red; el sistema está restableciendo el canal de comunicación.
   - **«Desconectado»** (Punto rojo): Sin conexión con el servidor. Se bloquean las operaciones críticas hasta restablecer el enlace.
2. **Indicador de Autoguardado**:
   - **«Guardado»** (Nube con check verde): El estado local coincide con la base de datos central.
   - **«Guardando…»** (Icono giratorio azul): Hay deltas transmitiéndose al servidor.
   - **«Error»** (Círculo rojo): El último guardado no pudo ser confirmado por el servidor.

#### Manejo de Conflictos de Revisión Concurrente:
Si dos diseñadores modifican un elemento simultáneamente o tu navegador pierde temporalmente la conexión, el sistema protegerá tu trabajo:
- Aparecerá una barra de advertencia superior: *«No se confirmó el cambio del diagrama. Se conservaron tus cambios locales y se suspendió el autoguardado»*.
- Para sincronizarte con la versión canónica más reciente, presiona el botón **«Recuperar estado remoto»**. El lienzo adoptará la última revisión confirmada por el equipo sin corromper la base de datos.
