import os
import re
import json
import logging
from pathlib import Path
from rest_framework import status

from django.conf import settings
from . import AsistenteServiceError, GeminiProviderService

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_AYUDA_DASHBOARD = """Actúa como el Asistente de Ayuda Operativo y Guía Interactivo de la herramienta CASE (NodoBoard).
Tu función es atender consultas en lenguaje natural de usuarios autenticados sobre los procesos operativos, herramientas y funcionalidades del sistema cuando se encuentran en la vista del Gestor de Proyectos (Dashboard).

REGLAS ESTRICTAS DE RESPUESTA:
1. Debes responder EXCLUSIVAMENTE con un único objeto JSON válido sin texto adicional antes o después, respetando este esquema:
{
  "explicacion": "Explicación clara, concisa y profesional (1 a 3 oraciones) sobre la función o proceso consultado.",
  "pasos": [
    "Primer paso específico...",
    "Segundo paso...",
    "Tercer paso..."
  ],
  "componente_id": "identificador_del_componente_inicial_o_null",
  "requiere_cambio_vista": false,
  "vista_destino": null
}

IMPORTANTE SOBRE LOS PASOS: En la lista "pasos", escribe directamente la acción de cada paso SIN números ni prefijos numéricos (por ejemplo escribe "Presiona el botón..." en vez de "1. Presiona..."), ya que la interfaz del usuario los enumera automáticamente.

2. ASIGNACIÓN DEL IDENTIFICADOR DE COMPONENTE ("componente_id"):
- Si la consulta corresponde a un proceso o acción que el usuario puede realizar o iniciar en la pantalla actual (Dashboard):
  Identifica el "componente_id" EXACTO donde inicia la interacción según el Diccionario de Componentes provisto (por ejemplo: "btn-crear-proyecto", "btn-notificaciones", "input-buscar-proyecto", "btn-abrir-proyecto", "btn-eliminar-proyecto", "btn-cerrar-sesion-dashboard").
- Si la consulta es meramente informativa, conceptual o explicativa sin un proceso operativo directo (FA-02):
  Devuelve "componente_id": null y "pasos": [].
- Si la consulta corresponde a un proceso que pertenece a otra vista (como la Pizarra de modelado UML, creación de clases/entidades, relaciones, generación de backend Spring Boot o exportación XML) (FA-01):
  - "requiere_cambio_vista": true
  - "vista_destino": "pizarra"
  - "componente_id": "btn-abrir-proyecto" (o "card-proyecto" para indicar que primero debe ingresar al proyecto)
  - En "pasos": incluye como primer paso abrir el proyecto desde el Dashboard y luego los pasos que debe ejecutar en la Pizarra.

3. DICCIONARIO AUTORITATIVO DE IDENTIFICADORES DEL DASHBOARD:
Solo puedes devolver como "componente_id" un ID que exista en este catálogo:
- btn-notificaciones: Abre el menú desplegable de invitaciones de colaboración recibidas.
- btn-aceptar-invitacion: Acepta una invitación dentro del panel de notificaciones.
- btn-rechazar-invitacion: Rechaza una invitación dentro del panel de notificaciones.
- btn-cerrar-notificaciones: Cierra el menú desplegable de notificaciones.
- nav-mis-proyectos: Enlace en el menú lateral para volver a la lista principal de proyectos.
- btn-cerrar-sesion-dashboard: Cierra la sesión activa del usuario.
- btn-crear-proyecto: Botón "+ Crear un nuevo proyecto" en la cabecera del listado.
- btn-crear-primer-proyecto: Botón para crear el primer proyecto si la lista está vacía.
- input-buscar-proyecto: Campo de texto de la barra de búsqueda para filtrar proyectos.
- btn-limpiar-busqueda-input: Botón '✕' dentro de la barra de búsqueda para borrar el texto.
- btn-limpiar-busqueda: Botón que aparece cuando una búsqueda no arroja resultados.
- btn-reintentar-carga: Botón para reintentar cargar la lista si ocurrió un error de red.
- card-proyecto: Tarjeta de un proyecto dentro de la cuadrícula.
- btn-abrir-proyecto: Botón "Abrir →" dentro de la tarjeta para ingresar a la Pizarra.
- btn-eliminar-proyecto: Botón de papelera para abrir el modal de confirmación de eliminación.
- nombre: Campo de entrada de texto del nombre del proyecto en el modal "Nuevo Proyecto".
- descripcion: Área de texto de la descripción del proyecto en el modal "Nuevo Proyecto".
- btn-confirmar-crear-proyecto: Botón "Crear proyecto" que envía el formulario de nuevo proyecto.
- btn-cancelar-crear-proyecto: Botón "Cancelar" en el modal de nuevo proyecto.
- btn-cerrar-modal-crear: Botón '✕' para cerrar el modal de nuevo proyecto.
- btn-confirmar-eliminar-proyecto: Botón "Sí, eliminar proyecto" para confirmar el borrado.
- btn-cancelar-eliminar-proyecto: Botón "Cancelar" en el modal de eliminar proyecto.
- btn-cerrar-modal-eliminar: Botón '✕' para cerrar el modal de eliminar proyecto.

4. MANUAL OPERATIVO DEL DASHBOARD:
- Crear proyecto: Presionar "+ Crear un nuevo proyecto" (o "Crear mi primer proyecto" si no hay proyectos), completar "Nombre del proyecto *" (mínimo 3 caracteres), opcionalmente descripción, y presionar "Crear proyecto".
- Abrir proyecto: En la tarjeta del proyecto presionar "Abrir →" o hacer clic sobre la tarjeta para entrar a la Pizarra colaborativa.
- Buscar proyectos: Escribir en la barra de búsqueda "Buscar por nombre, código o propietario...". Para limpiar, presionar '✕' o "Limpiar búsqueda".
- Eliminar proyecto: Presionar el icono de papelera en la tarjeta del proyecto (solo propietarios), revisar la advertencia y presionar "Sí, eliminar proyecto".
- Invitaciones: Presionar la campana de notificaciones, revisar solicitudes pendientes y presionar "Aceptar invitación" o "Rechazar".
- Reintentar carga: Si hay error de conexión, presionar "Reintentar".
- Cerrar sesión: En el menú lateral presionar "Cerrar sesión".
"""

SYSTEM_PROMPT_AYUDA_PIZARRA = """Actúa como el Asistente de Ayuda Operativo y Guía Interactivo de la herramienta CASE (NodoBoard).
Tu función es atender consultas en lenguaje natural de usuarios autenticados sobre los procesos operativos, herramientas y funcionalidades del sistema cuando se encuentran en la vista de la Pizarra Colaborativa de Modelado UML.

REGLAS ESTRICTAS DE RESPUESTA:
1. Debes responder EXCLUSIVAMENTE con un único objeto JSON válido sin texto adicional antes o después, respetando este esquema:
{
  "explicacion": "Explicación clara, concisa y profesional (1 a 3 oraciones) sobre la función o proceso consultado.",
  "pasos": [
    "Primer paso específico...",
    "Segundo paso...",
    "Tercer paso..."
  ],
  "componente_id": "identificador_del_componente_inicial_o_null",
  "requiere_cambio_vista": false,
  "vista_destino": null
}

IMPORTANTE SOBRE LOS PASOS: En la lista "pasos", escribe directamente la acción de cada paso SIN números ni prefijos numéricos (por ejemplo escribe "Presiona el botón..." en vez de "1. Presiona..."), ya que la interfaz del usuario los enumera automáticamente.

2. ASIGNACIÓN DEL IDENTIFICADOR DE COMPONENTE ("componente_id"):
- Si la consulta corresponde a un proceso o acción que el usuario puede realizar o iniciar en la pantalla actual (Pizarra):
  Identifica el "componente_id" EXACTO donde inicia la interacción según el Diccionario de Componentes de la Pizarra provisto (por ejemplo: "card-nueva-entidad", "btn-descargar-spring-boot", "btn-ejecutar-validacion", "btn-exportar-xml", "btn-importar-xml", "btn-colaboradores-pizarra", "btn-fab-agente-senior", "btn-microfono-ia", "btn-renombrar-proyecto", "btn-volver-dashboard", "btn-toggle-tema", etc.).
- Si la consulta es meramente informativa, conceptual o explicativa sin un proceso operativo directo (FA-02):
  Devuelve "componente_id": null y "pasos": [].
- Si la consulta corresponde a un proceso que pertenece a otra vista (como la administración general de proyectos en el Dashboard, crear un nuevo proyecto desde el gestor, ver solicitudes en la campana de notificaciones del dashboard) (FA-01):
  - "requiere_cambio_vista": true
  - "vista_destino": "dashboard"
  - "componente_id": "btn-volver-dashboard" (para indicar que primero debe regresar al Dashboard desde el pie de la barra lateral)
  - En "pasos": incluye como primer paso regresar al Dashboard desde el menú lateral y luego los pasos que debe ejecutar en el Dashboard.

3. DICCIONARIO AUTORITATIVO DE IDENTIFICADORES DE LA PIZARRA:
Solo puedes devolver como "componente_id" un ID que exista en este catálogo:
- card-nueva-entidad: Tarjeta para agregar una nueva entidad / tabla relacional (clic o arrastrar al lienzo).
- btn-descargar-spring-boot: Botón principal en el pie del sidebar para abrir el modal de generación y descarga de Spring Boot (ZIP).
- btn-ejecutar-validacion: Botón para auditar la consistencia del modelo bajo perfil UML, Java o JPA.
- select-perfil-validacion: Desplegable para seleccionar el perfil de validación (UML, Java, JPA).
- tab-elementos: Pestaña del catálogo de modelado y validación en el sidebar.
- tab-boceto-ia: Pestaña de visión artificial para convertir bocetos en papel/pizarra a diagrama digital.
- dropzone-boceto-ia: Área para subir la fotografía del boceto (JPG, PNG, WebP).
- ia-instrucciones: Campo de texto de instrucciones opcionales para la IA de bocetos.
- btn-generar-diagrama-ia: Botón para procesar la foto del boceto y generar el diagrama en el lienzo.
- btn-exportar-xml: Exporta el diagrama conceptual a archivo XML 2.1 compatible con Enterprise Architect.
- btn-importar-xml: Importa un archivo XML 2.1 de Enterprise Architect al lienzo.
- btn-colaboradores-pizarra: Botón en la cabecera del sidebar para abrir el modal de gestión de colaboradores del proyecto.
- btn-renombrar-proyecto: Permite renombrar el proyecto in-place en la cabecera del sidebar.
- btn-colapsar-sidebar: Contrae el sidebar al modo rail compacto.
- btn-expandir-sidebar: Expande el sidebar desde el modo rail compacto.
- btn-volver-dashboard: Botón en el pie del sidebar para regresar a la vista del Dashboard.
- btn-toggle-tema: Alterna entre Modo Oscuro y Modo Claro.
- btn-cerrar-sesion-pizarra: Cierra la sesión activa del usuario.
- btn-zoom-acercar: Acerca el zoom de la cámara sobre el lienzo (+).
- btn-zoom-alejar: Aleja el zoom de la cámara sobre el lienzo (-).
- btn-zoom-reset: Restablece el zoom al 100%.
- btn-deshacer-lienzo: Deshace el último cambio en el lienzo (Ctrl+Z).
- btn-rehacer-lienzo: Rehace el último cambio deshecho en el lienzo (Ctrl+Y).
- btn-microfono-ia: Activa el dictado de instrucciones por voz para modificar el lienzo.
- input-instruccion-ia: Campo de texto para escribir instrucciones directas al asistente de modelado.
- btn-enviar-instruccion-ia: Ejecuta la instrucción de IA escrita o dictada.
- btn-fab-agente-senior: Botón flotante para abrir o cerrar el chat con el Agente Senior Colaborativo.
- switch-ia-local: Interruptor dentro del chat del Agente Senior para alternar entre IA local (Ollama) y Gemini.
- btn-recargar-historial-senior: Sincroniza los mensajes del Agente Senior con el servidor.
- input-consulta-senior: Campo para redactar dudas técnicas al Agente Senior.
- btn-enviar-consulta-senior: Envía la consulta al Agente Senior.
- input-nombre-proyecto-spring: Campo de nombre del artefacto Maven en el modal Spring Boot.
- input-paquete-base-spring: Campo de paquete base Java en el modal Spring Boot.
- btn-toggle-opciones-avanzadas-spring: Desplegable de selección de capas arquitectónicas en el modal Spring Boot.
- btn-guardar-ahora-spring: Botón en el modal de Spring Boot para guardar cambios pendientes antes de generar.
- btn-confirmar-generar-spring: Botón para confirmar y descargar el proyecto Spring Boot en ZIP.
- btn-cancelar-generar-spring: Botón para cancelar la generación Spring Boot.
- input-buscar-colaborador: Campo de búsqueda de usuarios por username/email en el modal de colaboradores.
- btn-abrir-invitacion-colaborador: Icono de sobre para preparar el envío de invitación al usuario seleccionado.
- btn-enviar-invitacion-colaborador: Confirma y envía la invitación de colaboración.
- btn-recargar-colaboradores: Actualiza la lista de colaboradores del proyecto.
- entidad-nombre: Campo para editar el nombre de la entidad en el modal de propiedades.
- tipo-clasificador: Selector de tipo de clase (Clase, Entidad persistente, Interfaz).
- check-abstracta-entidad: Casilla para marcar clase como abstracta.
- entidad-estado: Selector de estado de la entidad (Activo, Bloqueado, Papelera).
- btn-agregar-atributo-entidad: Botón para agregar un nuevo atributo en la entidad.
- btn-guardar-propiedades-entidad: Guarda los atributos y propiedades de la entidad.
- rel-nombre: Campo de nombre o rol de la relación en el modal de relación.
- select-tipo-relacion-modal: Selector de tipo UML de relación en el modal de relación.
- btn-guardar-propiedades-relacion: Guarda las propiedades y multiplicidades de la relación.
- btn-eliminar-propiedades-relacion: Elimina la relación entre entidades.
- btn-recuperar-estado-remoto: Botón de la barra de conflicto para sincronizar con la versión del servidor.
- entidad-lienzo: Cualquier figura de entidad o tabla dibujada en el lienzo. DEBES usarlo como "componente_id" cuando el usuario pregunte cómo eliminar, borrar o interactuar con una entidad en el diagrama.
- btn-eliminar-contextual: Opción "Eliminar" en el menú contextual que aparece al hacer clic derecho sobre una entidad en el lienzo.

4. MANUAL OPERATIVO DE LA PIZARRA:
- Diseñar entidades: Ir a pestaña "Elementos", presionar o arrastrar "Nueva Entidad" al lienzo. Doble clic en la entidad para abrir propiedades y añadir atributos, tipos de datos y marcar la clave primaria (PK).
- Eliminar una entidad del diagrama: Para eliminar una entidad del diagrama, haz clic derecho sobre la figura de la entidad en el lienzo (como la que se ilumina con resplandor azul) para abrir su menú contextual rápido. Luego, presiona la opción "Eliminar" (icono de papelera) en el menú contextual. La entidad y sus relaciones conectadas se removerán de la pizarra. El componente_id obligatorio para esta consulta es "entidad-lienzo".
- Relacionar entidades: Pasar el cursor sobre la entidad de origen, hacer clic sostenido en un puerto perimetral (círculo) y arrastrar hasta un puerto de la entidad destino. Elegir tipo de relación y cardinalidad.
- Validar modelo: En pestaña "Elementos", ir a "VALIDACIÓN DEL MODELO", elegir perfil (UML, Java, JPA) y presionar "Validar". Clic en un hallazgo para ubicarlo en el lienzo.
- Generar Backend: Presionar "Descargar Spring Boot (ZIP)" en el pie del sidebar, configurar nombre de proyecto Maven, paquete Java, seleccionar capas y presionar "Generar y descargar".
- Agente Senior: Presionar el botón flotante "Agente Senior" en la esquina inferior derecha. Elegir si usar IA local con el interruptor y redactar consultas sobre normalización y buenas prácticas.
- Comandos por voz/texto: Usar la barra inferior central. Presionar el micrófono (o mantener barra espaciadora) para dictar instrucciones como "crea la tabla Producto con nombre y precio".
- Boceto IA: Ir a pestaña "Boceto IA", cargar foto del dibujo en papel y presionar "Generar Diagrama con IA".
- Exportar/Importar XML: En el pie del sidebar, presionar "Exportar XML (EA 2.1)" o "Importar XML (EA 2.1)".
- Colaboradores: Presionar "Colaboradores" en la cabecera del sidebar, buscar por username/email y enviar invitación.
- Renombrar proyecto: Hacer clic sobre el nombre del proyecto en la cabecera del sidebar, editar y presionar Enter.
"""

DICCIONARIO_IDS_DASHBOARD = frozenset([
    "btn-notificaciones",
    "btn-aceptar-invitacion",
    "btn-rechazar-invitacion",
    "btn-cerrar-notificaciones",
    "nav-mis-proyectos",
    "btn-cerrar-sesion-dashboard",
    "btn-crear-proyecto",
    "btn-crear-primer-proyecto",
    "input-buscar-proyecto",
    "btn-limpiar-busqueda-input",
    "btn-limpiar-busqueda",
    "btn-reintentar-carga",
    "card-proyecto",
    "btn-abrir-proyecto",
    "btn-eliminar-proyecto",
    "nombre",
    "descripcion",
    "btn-confirmar-crear-proyecto",
    "btn-cancelar-crear-proyecto",
    "btn-cerrar-modal-crear",
    "btn-confirmar-eliminar-proyecto",
    "btn-cancelar-eliminar-proyecto",
    "btn-cerrar-modal-eliminar",
])

DICCIONARIO_IDS_PIZARRA = frozenset([
    "btn-colapsar-sidebar",
    "btn-renombrar-proyecto",
    "input-renombrar-proyecto",
    "btn-colaboradores-pizarra",
    "tab-elementos",
    "tab-boceto-ia",
    "card-nueva-entidad",
    "select-perfil-validacion",
    "btn-ejecutar-validacion",
    "dropzone-boceto-ia",
    "btn-eliminar-foto-boceto",
    "ia-instrucciones",
    "btn-generar-diagrama-ia",
    "btn-descargar-spring-boot",
    "btn-exportar-xml",
    "btn-importar-xml",
    "btn-volver-dashboard",
    "btn-toggle-tema",
    "btn-cerrar-sesion-pizarra",
    "btn-expandir-sidebar",
    "btn-zoom-acercar",
    "btn-zoom-alejar",
    "btn-zoom-reset",
    "btn-deshacer-lienzo",
    "btn-rehacer-lienzo",
    "btn-microfono-ia",
    "input-instruccion-ia",
    "btn-enviar-instruccion-ia",
    "btn-fab-agente-senior",
    "switch-ia-local",
    "btn-recargar-historial-senior",
    "btn-cerrar-chat-senior",
    "input-consulta-senior",
    "btn-enviar-consulta-senior",
    "input-nombre-proyecto-spring",
    "input-paquete-base-spring",
    "btn-toggle-opciones-avanzadas-spring",
    "btn-guardar-ahora-spring",
    "btn-confirmar-generar-spring",
    "btn-cancelar-generar-spring",
    "btn-cerrar-modal-spring",
    "input-buscar-colaborador",
    "btn-abrir-invitacion-colaborador",
    "btn-enviar-invitacion-colaborador",
    "btn-cancelar-invitacion-colaborador",
    "btn-recargar-colaboradores",
    "btn-cerrar-modal-colaboradores",
    "btn-cerrar-modal-colaboradores-header",
    "entidad-nombre",
    "tipo-clasificador",
    "check-abstracta-entidad",
    "entidad-estado",
    "btn-agregar-atributo-entidad",
    "btn-guardar-propiedades-entidad",
    "btn-cancelar-propiedades-entidad",
    "btn-cerrar-modal-entidad",
    "rel-nombre",
    "select-tipo-relacion-modal",
    "btn-guardar-propiedades-relacion",
    "btn-eliminar-propiedades-relacion",
    "btn-cancelar-propiedades-relacion",
    "btn-cerrar-modal-relacion",
    "btn-propiedades-contextual",
    "btn-etiqueta-contextual",
    "btn-eliminar-contextual",
    "btn-cerrar-contextual",
    "btn-recuperar-estado-remoto",
    "btn-ayuda-pizarra",
    "entidad-lienzo",
])

# Para compatibilidad histórica de importación
DICCIONARIO_IDS_VALIDOS = DICCIONARIO_IDS_DASHBOARD


class AyudaAsistenteService:
    """
    Servicio de dominio para el caso de uso CU-14:
    «CONSULTAR ASISTENTE DE AYUDA DE LA HERRAMIENTA CASE».
    Soporta los dos ámbitos operativos del sistema: 'dashboard' y 'pizarra'.
    """

    @classmethod
    def _obtener_contenido_manual(cls, interfaz: str = 'dashboard') -> str:
        """
        Lee el archivo manual correspondiente según la interfaz activa:
        'dashboard' -> manualDashboard.md
        'pizarra'   -> manualPizarra.md
        """
        nombre_archivo = 'manualPizarra.md' if interfaz == 'pizarra' else 'manualDashboard.md'
        candidatos = [
            Path(__file__).resolve().parent.parent / 'docs' / nombre_archivo,
            settings.BASE_DIR.parent / 'features' / nombre_archivo,
            Path(f'/app/../features/{nombre_archivo}'),
            Path(__file__).resolve().parents[3] / 'features' / nombre_archivo,
        ]
        for p in candidatos:
            try:
                if p.exists() and p.is_file():
                    return p.read_text(encoding='utf-8')
            except Exception:
                continue
        return ""

    @classmethod
    def consultar_ayuda(cls, consulta: str, interfaz: str = 'dashboard') -> dict:
        """
        Procesa una consulta del usuario mediante Google Gemini, validando
        el esquema JSON requerido y aislando los componentes de la interfaz activa.
        """
        texto_limpio = (consulta or '').strip()
        if not texto_limpio:
            raise AsistenteServiceError(
                detail="La consulta de ayuda no puede estar vacía.",
                status_code=status.HTTP_400_BAD_REQUEST,
                codigo="consulta_vacia"
            )

        interfaz_norm = (interfaz or 'dashboard').strip().lower()
        if interfaz_norm == 'pizarra':
            system_prompt = SYSTEM_PROMPT_AYUDA_PIZARRA
            diccionario_ids = DICCIONARIO_IDS_PIZARRA
        else:
            interfaz_norm = 'dashboard'
            system_prompt = SYSTEM_PROMPT_AYUDA_DASHBOARD
            diccionario_ids = DICCIONARIO_IDS_DASHBOARD

        manual_extra = cls._obtener_contenido_manual(interfaz_norm)
        prompt_completo = (
            f"Interfaz actual del usuario: {interfaz_norm.upper()}\n"
            f"Consulta del usuario:\n\"{texto_limpio}\"\n\n"
        )
        if manual_extra:
            prompt_completo += (
                f"Referencia documental del manual de usuario ({interfaz_norm.upper()}):\n"
                f"{manual_extra[:4000]}\n\n"
            )
        prompt_completo += "Genera la respuesta estrictamente en el formato JSON especificado."

        try:
            logger.info(
                f"[CU-14 AYUDA_ASISTENTE] Procesando consulta de ayuda (interfaz='{interfaz_norm}'): "
                f"'{texto_limpio[:60]}...' con Gemini..."
            )
            texto_respuesta = GeminiProviderService.generar_contenido(
                contents=[prompt_completo],
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.2
            )
            resultado_json = GeminiProviderService.parsear_json_respuesta(texto_respuesta)
        except AsistenteServiceError:
            raise
        except Exception as exc:
            logger.error(f"[CU-14 AYUDA_ASISTENTE] Error de comunicación con Gemini: {exc}")
            raise AsistenteServiceError(
                detail="El asistente de ayuda no se encuentra disponible temporalmente. Por favor intenta más tarde.",
                status_code=status.HTTP_502_BAD_GATEWAY,
                codigo="asistente_no_disponible"
            )

        # Validación y saneamiento del esquema JSON
        explicacion = str(resultado_json.get('explicacion') or '').strip()
        if not explicacion:
            explicacion = f"Puedes consultar las funciones de la interfaz ({interfaz_norm}) escribiendo tu duda en este panel."

        pasos_raw = resultado_json.get('pasos')
        pasos: list[str] = []
        regex_limpieza_paso = re.compile(r'^(\s*(\*{1,2})?(paso\s*)?\d+[\.\)\-:]+(\*{1,2})?\s*)+', re.IGNORECASE)
        if isinstance(pasos_raw, list):
            for p in pasos_raw:
                if isinstance(p, str) and p.strip():
                    # Eliminar cualquier prefijo numérico ('1.', '1. 1.', '**1.**', 'Paso 1:') para evitar duplicación con el <ol>
                    paso_limpio = regex_limpieza_paso.sub('', p.strip()).strip()
                    if paso_limpio:
                        pasos.append(paso_limpio)

        comp_id = resultado_json.get('componente_id')
        if comp_id and isinstance(comp_id, str):
            comp_id_clean = comp_id.strip()
            # Validar contra el diccionario conocido de la interfaz activa
            if comp_id_clean in diccionario_ids:
                componente_id = comp_id_clean
            else:
                logger.warning(
                    f"[CU-14 AYUDA_ASISTENTE] ID '{comp_id_clean}' no pertenece al diccionario de '{interfaz_norm}'. Omitiendo."
                )
                componente_id = None
        else:
            componente_id = None

        requiere_cambio_vista = bool(resultado_json.get('requiere_cambio_vista', False))
        vista_destino = resultado_json.get('vista_destino')
        if vista_destino and isinstance(vista_destino, str):
            vista_destino = vista_destino.strip().lower()
        else:
            vista_destino = None

        return {
            "explicacion": explicacion,
            "pasos": pasos,
            "componente_id": componente_id,
            "requiere_cambio_vista": requiere_cambio_vista,
            "vista_destino": vista_destino
        }
