import os
import json
import time
import base64
import logging
import threading
from datetime import timedelta

from django.conf import settings
from django.db import transaction, close_old_connections
from django.utils import timezone
from rest_framework import status

from google import genai
from google.genai import types
from google.genai.errors import ServerError, APIError

from modelado.models import Proyecto, Entidad
from modelado.realtime import notificar_evento_proyecto_sync
from usuario.models import UserColaborador
from .models import Conversacion, Mensaje
from .serializers import MensajeSerializer, ConversacionSerializer

logger = logging.getLogger(__name__)

# Límite máximo de caracteres para una consulta al Agente Senior (FE-03)
MAX_CARACTERES_CONSULTA = 2000

# Capacidad máxima de la cola por proyecto (Requisito Especial 1 / FA-01 / FE-04)
MAX_EN_PROCESAMIENTO = 1
MAX_EN_COLA_ESPERA = 2

# Ventana de mensajes recientes del historial inyectados en el contexto (línea 112 features.md)
ULTIMOS_MENSAJES_HISTORIAL = 20

# Tiempo máximo para considerar huérfano un mensaje en procesamiento tras un reinicio abrupto
TIMEOUT_MENSAJE_HUERFANO_SEGUNDOS = 180


class AsistenteServiceError(Exception):
    """
    Excepción de dominio para errores controlados dentro de los servicios de la app asistente.
    """
    def __init__(
        self,
        detail: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        codigo: str = 'error_validacion',
        extra: dict | None = None
    ):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code
        self.codigo = codigo
        self.extra = extra or {}

    def to_dict(self) -> dict:
        payload = {
            "detail": self.detail,
            "error": self.detail,
            "codigo": self.codigo,
        }
        payload.update(self.extra)
        return payload


# =====================================================================
# PROMPTS DEL SISTEMA
# =====================================================================

SYSTEM_PROMPT_AGENTE_SENIOR = """Actúa como un Arquitecto de Datos y Asesor Senior Colaborativo especializado en diseño conceptual de bases de datos relacionales y modelado UML (diagramas de clases).
Estás participando en una sesión colaborativa en tiempo real donde el propietario del proyecto y sus colaboradores te consultan dudas, piden revisiones de su diagrama, sugerencias de mejora o explicaciones sobre modelado de datos.

REGLAS ESTRICTAS DE TU ROL (AGENTE SENIOR COLABORATIVO):
1. Rol puramente asesor y consultivo:
   - Tu función es orientar, explicar conceptos, revisar el diseño actual del diagrama UML, detectar malas prácticas (problemas de normalización, ausencia de claves primarias, tipos de datos inadecuados, relaciones Muchos a Muchos sin clase de asociación/tabla intermedia, cardinalidades ambiguas) y proponer mejoras concretas.
   - NO modificas directamente el lienzo por tu cuenta; guías a los diseñadores y les explicas qué cambios realizar o por qué.
2. Identificación personalizada y colaborativa:
   - Dirígete cordialmente por su nombre o username al usuario que realiza la consulta actual (indicado en el bloque "USUARIO QUE REALIZA LA CONSULTA").
   - Ten en cuenta que tu respuesta será leída en tiempo real por todos los colaboradores del proyecto.
3. Uso estricto del contexto dinámico:
   - Basa siempre tus análisis y recomendaciones en el estado vigente del diagrama proporcionado (entidades, atributos con sus tipos y claves, y relaciones con sus cardinalidades y clases de asociación), así como en los participantes del proyecto y los últimos mensajes del historial de la conversación.
4. Claridad y formato:
   - Responde siempre en español, de forma estructurada, clara, profesional y concisa.
   - Usa listas con viñetas o numeradas cuando sugieras atributos, relaciones o mejoras de diseño.
   - Recuerda que en esta herramienta CASE los tipos de datos válidos para atributos son: `string`, `integer`, `long`, `double`, `boolean`, `date`, y las relaciones Muchos a Muchos (`N:M`) se modelan mediante una Clase de Asociación (`es_intermedia: true`).
"""


SYSTEM_PROMPT_IMAGEN = """Actúa como un arquitecto de software y modelador de bases de datos relacionales estricto.
Tu tarea es analizar la fotografía o boceto de un diagrama de clases / entidad-relación dibujado a mano.
Identifica con precisión:
1. Todas las entidades (clases o tablas) y su posición espacial aproximada dentro de la imagen.
2. Todos los atributos de cada entidad.
3. Todas las relaciones entre entidades, su tipo y sus cardinalidades.

REGLAS ESTRICTAS DE MODELADO Y TIPADO:
- Cada entidad debe tener:
  * "id": un identificador entero correlativo único (1, 2, 3...)
  * "nombre": nombre conceptual en singular (ej. "cliente", "factura", "producto")
  * "pos_x": número entero entre 0 y 1000 que indica la posición horizontal aproximada del centro de la caja de la entidad en la imagen (0 = borde izquierdo, 500 = centro, 1000 = borde derecho).
  * "pos_y": número entero entre 0 y 1000 que indica la posición vertical aproximada del centro de la caja de la entidad en la imagen (0 = borde superior, 500 = centro, 1000 = borde inferior).
  * "es_intermedia": booleano (true si surge de una relación N:M o clase de asociación, false de lo contrario)
  * "atributos": lista de atributos de la entidad.
- Cada atributo debe tener:
  * "id": un entero único (ej. 101, 102...)
  * "nombre": nombre del campo (ej. "id", "razon_social", "precio")
  * "tipo": DEBE SER ESTRICTAMENTE uno de los siguientes 6 tipos válidos:
    - "string"
    - "integer"
    - "long"
    - "double"
    - "boolean"
    - "date"
    (Si en el dibujo ves varchar, texto o char usa "string". Si ves int o serial usa "integer". Si ves float, decimal, numeric usa "double". Si ves timestamp o datetime usa "date").
  * "es_clave": booleano (true si es clave primaria / identificador, false de lo contrario)
  * "es_nulo": booleano (true si admite nulos, false de lo contrario)
  * "orden": entero secuencial que inicia en 1 (1, 2, 3...)
- Cada relación debe tener:
  * "id": un identificador entero correlativo único (1, 2, 3...)
  * "nombre_relacion": verbo o nombre de la relación si está visible (ej. "emite", "contiene"), o "" si no tiene nombre.
  * "tipo": DEBE SER ESTRICTAMENTE uno de los siguientes:
    - "asociacion"
    - "agregacion"
    - "composicion"
    - "herencia"
  * "entidad_origen_id": entero que coincide con el "id" de la entidad origen (en "agregacion" y "composicion", DEBE ser la PARTE; en "herencia", DEBE ser la subclase / hijo).
  * "entidad_destino_id": entero que coincide con el "id" de la entidad destino (en "agregacion" y "composicion", DEBE ser el CONTENEDOR / TODO donde se dibuja el rombo; en "herencia", DEBE ser la superclase / padre).
  * "cardinalidad_origen": multiplicidad en el origen si está escrita en el boceto (ej. "1", "*", "0..1", "1..*", "0..*"). Si en el boceto NO hay ninguna multiplicidad o número escrito en este extremo, DEBES poner "" (cadena vacía). NUNCA inventes o asumas multiplicidades por defecto.
  * "cardinalidad_destino": multiplicidad en el destino si está escrita en el boceto (ej. "1", "*", "0..1", "1..*", "0..*"). Si en el boceto NO hay ninguna multiplicidad o número escrito en este extremo, DEBES poner "" (cadena vacía). NUNCA inventes o asumas multiplicidades por defecto.
  * "clase_asociacion_id": entero o null. Si la relación es Muchos a Muchos (M:M) o Clase de Asociación, aquí colocas el "id" de la tabla intermedia que creaste en "entidades". Si es una relación regular (1:N, 1:1), coloca null.

REGLA ESTRICTA PARA RELACIONES DE MUCHOS A MUCHOS (M:M) Y CLASES DE ASOCIACIÓN:
Toda relación de Muchos a Muchos (M:M, N:M) o Clase de Asociación (sea que en el boceto veas una relación N:M entre dos tablas, o una tabla intermedia conectada con línea punteada al centro de la relación, o una tabla puente entre dos entidades):
1. En "entidades":
   - Para las tablas principales o regulares: "es_intermedia": false.
   - Para la tabla intermedia o clase de asociación: "es_intermedia": true (OBLIGATORIO).
   - "nombre": nombre de la clase de asociación o tabla intermedia (ej. "estudiante_materia", "inscripcion", "detalle_venta").
   - "pos_x", "pos_y": posición aproximada de la caja en el dibujo.
   - "atributos": atributos de la tabla intermedia (incluyendo "id" como clave primaria obligatoria).
2. En "relaciones", define una ÚNICA relación de tipo 'asociacion' directamente entre las dos tablas principales:
   - "entidad_origen_id": id de la primera tabla principal.
   - "entidad_destino_id": id de la segunda tabla principal.
   - "cardinalidad_origen": multiplicidad si está escrita explícitamente en el boceto (ej. "1", "*", "0..1", "1..*", "0..*"). Si en el boceto NO hay multiplicidad o números dibujados en este extremo, DEBES poner "" (cadena vacía). ¡ESTRICTAMENTE PROHIBIDO inventar o poner "0..*" por defecto si no está dibujado en la imagen!
   - "cardinalidad_destino": multiplicidad si está escrita explícitamente en el boceto (ej. "1", "*", "0..1", "1..*", "0..*"). Si en el boceto NO hay multiplicidad o números dibujados en este extremo, DEBES poner "" (cadena vacía). ¡ESTRICTAMENTE PROHIBIDO inventar o poner "0..*" por defecto si no está dibujado en la imagen!
   - "clase_asociacion_id": el "id" numérico de la tabla intermedia creada en el paso 1.
¡CRÍTICO!: NUNCA crees dos relaciones separadas y directas hacia la tabla intermedia. En este modelador conceptual, la tabla intermedia NO recibe flechas directas; se vincula exclusivamente a través de "clase_asociacion_id" en la relación principal (lo que hace que la herramienta dibuje automáticamente el conector punteado oficial UML hacia el centro de la relación).
IMPORTANTE: "es_intermedia" DEBE SER FALSE para todas las entidades normales que no sean una tabla intermedia / clase de asociación.

FORMATO DE SALIDA:
Debes responder EXCLUSIVAMENTE con un objeto JSON válido con la estructura de "entidades" y "relaciones".
"""


SYSTEM_PROMPT_INSTRUCCIONES = """Actúa como un copiloto y asistente interactivo de modelado de bases de datos relacionales y diagramas de clases UML.
El usuario te dará una orden o instrucción breve (mediante voz o texto) para realizar tareas pequeñas y específicas en su diagrama.
Recibirás:
1. "instruccion": la orden del usuario (ej: "crea la tabla cliente con id y nombre", "agrega el campo email a cliente", "relaciona cliente con factura", "elimina la tabla temporal").
2. "contexto_diagrama": lista resumida de entidades existentes (id, nombre, estado: 'activo' o 'bloqueado', atributos) y relaciones actuales (id, entidad_origen_id, entidad_destino_id, nombre_relacion).

Tu objetivo es interpretar la orden con precisión y devolver un delta estructurado de cambios a aplicar en el diagrama, junto con un mensaje conversacional amigable y breve en español.

REGLAS ESTRICTAS DE RESPUESTA:
- Debes responder EXCLUSIVAMENTE con un JSON válido con las claves:
  "mensaje", "entidades_a_crear", "entidades_a_modificar", "entidades_a_eliminar", "relaciones_a_crear", "relaciones_a_eliminar".

REGLAS DE INTERPRETACIÓN:
1. CONTROL DE EXCLUSIÓN MUTUA (ENTIDADES BLOQUEADAS):
   - Si una entidad existente en "contexto_diagrama" tiene "estado": "bloqueado", significa que otro usuario la está editando.
   - NUNCA agregues ni modifiques atributos a esa entidad en "entidades_a_modificar".
   - NUNCA agregues esa entidad a "entidades_a_eliminar".
   - Si el usuario pide modificar o eliminar una entidad que está bloqueada, NO agregues los cambios en el delta y adviértelo en "mensaje".
2. Si el usuario pide crear una entidad nueva:
   - "nombre": nombre conceptual en singular (ej: "proveedor", "producto").
   - Si no especificó clave primaria, agrega un campo "id" tipo "integer" con es_clave: true.
   - Si no especificó tipo para algún atributo, infiere el tipo más coherente entre los 6 permitidos: "string", "integer", "long", "double", "boolean", "date".
3. Si el usuario pide modificar una entidad existente o sus atributos:
   - Busca la entidad en "contexto_diagrama" por nombre (ignorando mayúsculas/minúsculas).
   - Verifica que NO esté en estado "bloqueado".
   - Usa su "entidad_id" real en "entidades_a_modificar" y opcionalmente "entidad_nombre".
   a) Si pide EDITAR, MODIFICAR O CAMBIAR un atributo YA EXISTENTE:
      - NUNCA lo coloques en "atributos_nuevos". Agrégalo OBLIGATORIAMENTE a "atributos_a_modificar" con "nombre_original", "nombre", "tipo", "es_clave", "es_nulo".
   b) Si pide AGREGAR un atributo que NO existía previamente en la entidad:
      - Agrégalo a "atributos_nuevos" con "orden" correlativo.
   c) Si pide ELIMINAR un atributo específico de la entidad:
      - Agrega el nombre del atributo a "atributos_a_eliminar".
   d) Si pide RENOMBRAR la entidad:
      - Asigna el nuevo nombre en "nuevo_nombre".
4. Si el usuario pide relacionar dos entidades:
   - Busca las entidades por nombre en "contexto_diagrama" o en "entidades_a_crear".
   - "tipo": "asociacion" por defecto a menos que se pida "composicion", "agregacion" o "herencia".
   - En "composicion" o "agregacion": "entidad_origen_nombre" DEBE ser la PARTE y "entidad_destino_nombre" DEBE ser el CONTENEDOR / TODO.
   - En "herencia": "entidad_origen_nombre" es la subclase (hijo) y "entidad_destino_nombre" es la superclase (padre).
   - Cardinalidades: NO asignes cardinalidades por defecto. Deja "cardinalidad_origen": "" y "cardinalidad_destino": "" a menos que se soliciten explícitamente.
5. ÓRDENES COMPUESTAS (CREAR Y RELACIONAR SIMULTÁNEAMENTE):
   - Agrega la entidad a "entidades_a_crear" y define la relación en "relaciones_a_crear".
6. REGLA ESTRICTA PARA RELACIONES DE MUCHOS A MUCHOS (M:M, N:M, "muchos a muchos", "clase de asociación"):
   - Crea la entidad intermedia en "entidades_a_crear" con "es_intermedia": true y vincúlala en "relaciones_a_crear" mediante "clase_asociacion_nombre" con cardinalidades "0..*".
7. Si el usuario pide eliminar:
   - Si no está bloqueada, coloca su id en "entidades_a_eliminar" o "relaciones_a_eliminar".
8. Si la instrucción no requiere cambios:
   - Deja las listas de cambios vacías (`[]`) y responde en "mensaje".
"""


# =====================================================================
# CLIENTE COMPARTIDO DE GOOGLE GEMINI
# =====================================================================

class GeminiProviderService:
    """
    Servicio auxiliar compartido para invocar a Google Gemini utilizando la
    misma GEMINI_API_KEY configurada en el proyecto y manejo de fallback de modelos.
    """

    @staticmethod
    def obtener_api_key() -> str:
        api_key = getattr(settings, 'GEMINI_API_KEY', None) or os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise AsistenteServiceError(
                detail="La clave GEMINI_API_KEY no está configurada en las variables de entorno.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                codigo="api_key_faltante"
            )
        return api_key

    @staticmethod
    def obtener_modelos_candidatos() -> list[str]:
        modelo_principal = getattr(settings, 'GEMINI_MODEL', 'gemini-3.8-flash')
        candidatos = [
            modelo_principal,
            'gemini-flash-latest',
            'gemini-2.5-flash',
            'gemini-2.0-flash',
            'gemini-3.6-flash',
            'gemini-3.5-flash-lite',
            'gemini-3.5-flash',
        ]
        modelos_a_probar = []
        for m in candidatos:
            if m and m not in modelos_a_probar:
                modelos_a_probar.append(m)
        return modelos_a_probar

    # Timeout por intento de modelo en milisegundos (15 segundos)
    TIMEOUT_MODELO_MS = 15000

    @classmethod
    def generar_contenido(
        cls,
        contents: list,
        system_instruction: str,
        response_mime_type: str | None = None,
        temperature: float = 0.2
    ) -> str:
        api_key = cls.obtener_api_key()
        http_opts = types.HttpOptions(timeout=cls.TIMEOUT_MODELO_MS)
        client = genai.Client(api_key=api_key, http_options=http_opts)
        modelos_a_probar = cls.obtener_modelos_candidatos()

        config_kwargs = {
            "system_instruction": system_instruction,
            "temperature": temperature,
            "http_options": http_opts,
            "automatic_function_calling": types.AutomaticFunctionCallingConfig(disable=True),
        }
        if response_mime_type:
            config_kwargs["response_mime_type"] = response_mime_type

        ultimo_error = None
        for modelo in modelos_a_probar:
            try:
                response = client.models.generate_content(
                    model=modelo,
                    contents=contents,
                    config=types.GenerateContentConfig(**config_kwargs)
                )
                if response and response.text:
                    return response.text.strip()
            except ServerError as se:
                time.sleep(0.4)
                logger.warning(f"Error de servidor temporal en modelo {modelo}: {se}. Intentando siguiente modelo...")
                ultimo_error = se
            except APIError as ae:
                logger.warning(f"Error de API en modelo {modelo}: {ae}. Intentando siguiente modelo...")
                ultimo_error = ae
            except Exception as e:
                logger.warning(f"Timeout o error en modelo {modelo}: {e}. Intentando siguiente modelo...")
                ultimo_error = e

        raise AsistenteServiceError(
            detail=f"El proveedor de IA no se encuentra disponible temporalmente. Detalle: {str(ultimo_error)}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            codigo="ia_no_disponible"
        )


# =====================================================================
# SERVICIO PRINCIPAL: INTERACTUAR CON AGENTE SENIOR COLABORATIVO
# =====================================================================

class AgenteSeniorService:
    """
    Servicio de dominio para el caso de uso «INTERACTUAR CON AGENTE SENIOR COLABORATIVO».
    Implementa:
    - Control de acceso para Propietario y Colaboradores activos (FE-05).
    - Validación de consultas no vacías y límite de caracteres (FE-03).
    - Cola secuencial FIFO acotada por proyecto: 1 en procesamiento y hasta 2 en espera (FA-01, FE-04).
    - Procesamiento en segundo plano resiliente ante desconexión del usuario iniciador (FA-02, FE-02).
    - Recopilación de contexto dinámico al momento de procesar: usuario, participantes, diagrama UML
      (entidades, atributos y relaciones) y los últimos 20 mensajes registrados en la conversación.
    - Reversión/descarte automático de la consulta en caso de fallo del proveedor de IA para
      mantener intacto el historial y no bloquear la cola (FE-01 y Postcondición de Fallo).
    - Sincronización en tiempo real por WebSockets a todos los colaboradores conectados.
    """

    # Locks y estado de workers activos en memoria por proyecto
    _locks_por_proyecto: dict[int, threading.Lock] = {}
    _workers_activos: set[int] = set()
    _global_lock = threading.Lock()

    # Caché ligero del último contexto del diagrama enviado desde el cliente por proyecto
    _contexto_diagrama_reciente: dict[int, dict] = {}

    @classmethod
    def _obtener_lock_proyecto(cls, proyecto_id: int) -> threading.Lock:
        with cls._global_lock:
            if proyecto_id not in cls._locks_por_proyecto:
                cls._locks_por_proyecto[proyecto_id] = threading.Lock()
            return cls._locks_por_proyecto[proyecto_id]

    @classmethod
    def verificar_acceso_proyecto(cls, proyecto_id: int, user) -> tuple[Proyecto, str]:
        """
        Verifica las precondiciones y FE-05:
        - El usuario debe estar autenticado.
        - El proyecto debe existir.
        - El usuario debe ser propietario o colaborador activo autorizado del proyecto.
        Retorna (proyecto, rol_en_proyecto).
        """
        if not user or not user.is_authenticated:
            raise AsistenteServiceError(
                detail="Debes iniciar sesión para interactuar con el Agente Senior.",
                status_code=status.HTTP_401_UNAUTHORIZED,
                codigo="no_autenticado"
            )

        proyecto = Proyecto.objects.select_related('propietario').filter(pk=proyecto_id).first()
        if not proyecto:
            raise AsistenteServiceError(
                detail="El proyecto solicitado no existe o no se encuentra disponible.",
                status_code=status.HTTP_404_NOT_FOUND,
                codigo="proyecto_no_encontrado"
            )

        if proyecto.propietario_id == user.id:
            return proyecto, 'Propietario'

        colaboracion = UserColaborador.objects.filter(
            proyecto=proyecto,
            usuario=user,
            estado=UserColaborador.Estado.ACTIVO
        ).first()

        if not colaboracion:
            # FE-05: Usuario sin permisos o revocado durante la sesión
            raise AsistenteServiceError(
                detail="No cuentas con permisos activos en este proyecto para interactuar con el Agente Senior.",
                status_code=status.HTTP_403_FORBIDDEN,
                codigo="sin_permisos_proyecto"
            )

        return proyecto, 'Colaborador'

    @classmethod
    def validar_contenido_consulta(cls, contenido: str | None) -> str:
        """
        FE-03: Valida que la consulta no esté vacía ni supere la longitud máxima permitida.
        """
        texto_limpio = (contenido or '').strip()
        if not texto_limpio:
            raise AsistenteServiceError(
                detail="La consulta no puede estar vacía. Por favor escribe una pregunta o solicitud válida.",
                status_code=status.HTTP_400_BAD_REQUEST,
                codigo="consulta_vacia"
            )

        if len(texto_limpio) > MAX_CARACTERES_CONSULTA:
            raise AsistenteServiceError(
                detail=(
                    f"La consulta excede el límite máximo permitido de {MAX_CARACTERES_CONSULTA} caracteres "
                    f"(actual: {len(texto_limpio)}). Por favor ajusta tu mensaje."
                ),
                status_code=status.HTTP_400_BAD_REQUEST,
                codigo="consulta_excede_limite",
                extra={"max_caracteres": MAX_CARACTERES_CONSULTA, "longitud_actual": len(texto_limpio)}
            )

        return texto_limpio

    @classmethod
    def _limpiar_mensajes_huerfanos(cls, conversacion: Conversacion) -> None:
        """
        Si algún mensaje quedó en estado 'procesando' o 'en_cola' por más de
        TIMEOUT_MENSAJE_HUERFANO_SEGUNDOS sin worker activo (ej. reinicio del servidor),
        se descarta para evitar que la cola quede bloqueada.
        """
        proyecto_id = conversacion.proyecto_id
        with cls._global_lock:
            worker_activo = proyecto_id in cls._workers_activos

        if worker_activo:
            return

        limite_tiempo = timezone.now() - timedelta(seconds=TIMEOUT_MENSAJE_HUERFANO_SEGUNDOS)
        huerfanos = conversacion.mensajes.filter(
            estado__in=[Mensaje.Estado.PROCESANDO, Mensaje.Estado.EN_COLA],
            fecha_envio__lt=limite_tiempo
        )
        if huerfanos.exists():
            huerfanos.delete()

    @classmethod
    def calcular_estado_cola(cls, conversacion: Conversacion | None) -> dict:
        """
        Calcula el estado vigente de la cola del Agente Senior para un proyecto:
        - procesando: bool
        - mensaje_procesando_id: int | None
        - usuario_procesando: str | None
        - en_cola_count: int (0..2)
        - max_en_cola: int (2)
        - cola_llena: bool
        - posiciones_cola: dict[str, int] (mapeo de mensaje_id -> posición 1 o 2)
        """
        if not conversacion:
            return {
                "procesando": False,
                "mensaje_procesando_id": None,
                "usuario_procesando": None,
                "en_cola_count": 0,
                "max_en_cola": MAX_EN_COLA_ESPERA,
                "cola_llena": False,
                "posiciones_cola": {},
            }

        msg_procesando = (
            conversacion.mensajes
            .select_related('usuario')
            .filter(estado=Mensaje.Estado.PROCESANDO)
            .order_by('fecha_envio', 'id')
            .first()
        )
        msgs_en_cola = list(
            conversacion.mensajes
            .filter(estado=Mensaje.Estado.EN_COLA)
            .order_by('fecha_envio', 'id')
            .values_list('id', flat=True)
        )

        posiciones_cola = {
            str(msg_id): idx + 1
            for idx, msg_id in enumerate(msgs_en_cola)
        }
        en_cola_count = len(msgs_en_cola)
        esta_procesando = msg_procesando is not None
        cola_llena = esta_procesando and (en_cola_count >= MAX_EN_COLA_ESPERA)

        return {
            "procesando": esta_procesando,
            "mensaje_procesando_id": msg_procesando.id if msg_procesando else None,
            "usuario_procesando": (
                msg_procesando.usuario.username
                if msg_procesando and msg_procesando.usuario
                else None
            ),
            "en_cola_count": en_cola_count,
            "max_en_cola": MAX_EN_COLA_ESPERA,
            "cola_llena": cola_llena,
            "posiciones_cola": posiciones_cola,
        }

    @classmethod
    def obtener_historial_proyecto(cls, proyecto_id: int, user) -> dict:
        """
        Flujo Principal Pasos 1 y 2:
        Valida el acceso del usuario al proyecto y retorna el historial completo de la conversación
        junto con el estado actual de la cola del Agente Senior.
        """
        proyecto, rol_usuario = cls.verificar_acceso_proyecto(proyecto_id, user)
        conversacion = Conversacion.objects.filter(proyecto=proyecto).first()

        if conversacion:
            cls._limpiar_mensajes_huerfanos(conversacion)
            estado_cola = cls.calcular_estado_cola(conversacion)
            # Si había mensajes pendientes sin worker activo, aseguramos que el worker arranque
            if estado_cola["procesando"] or estado_cola["en_cola_count"] > 0:
                cls._asegurar_worker_proyecto(proyecto.id)
            conversacion_data = ConversacionSerializer(
                conversacion,
                context={'posiciones_cola': estado_cola['posiciones_cola']}
            ).data
            mensajes_data = conversacion_data['mensajes']
            conversacion_id = conversacion.id
            fecha_creacion = conversacion.fecha_creacion
        else:
            estado_cola = cls.calcular_estado_cola(None)
            mensajes_data = []
            conversacion_id = None
            fecha_creacion = None

        return {
            "proyecto_id": proyecto.id,
            "proyecto_nombre": proyecto.nombre,
            "rol_usuario_actual": rol_usuario,
            "conversacion_id": conversacion_id,
            "fecha_creacion": fecha_creacion,
            "mensajes": mensajes_data,
            "estado_cola": estado_cola,
            "max_caracteres": MAX_CARACTERES_CONSULTA,
        }

    @classmethod
    def enviar_consulta(
        cls,
        proyecto_id: int,
        user,
        contenido: str | None,
        contexto_diagrama: dict | None = None
    ) -> dict:
        """
        Flujo Principal Pasos 3–5, FA-01 Pasos 1–3 y Excepciones FE-03, FE-04, FE-05:
        1. Verifica permisos activos del usuario en el proyecto (FE-05).
        2. Valida que la consulta no sea vacía ni supere el límite de caracteres (FE-03).
        3. Verifica el estado de la cola del proyecto con bloqueo transaccional:
           - Si el agente está libre -> registra el mensaje en estado 'procesando'.
           - Si el agente está ocupado y hay < 2 en cola -> registra el mensaje en estado 'en_cola' (FA-01).
           - Si ya hay 2 en cola -> rechaza el envío informando que la cola está llena (FE-04).
        4. Notifica en tiempo real por WebSocket a todos los colaboradores conectados.
        5. Dispara el worker secuencial en segundo plano para procesar la cola con Gemini.
        """
        # 1. Validar permisos en el proyecto (FE-05)
        cls.verificar_acceso_proyecto(proyecto_id, user)

        # 2. Validar longitud y contenido del mensaje (FE-03)
        contenido_limpio = cls.validar_contenido_consulta(contenido)

        # Guardar contexto en memoria si el cliente lo proporcionó
        if isinstance(contexto_diagrama, dict) and contexto_diagrama:
            cls._contexto_diagrama_reciente[proyecto_id] = contexto_diagrama

        # 3. Sección crítica transaccional para gestionar la cola FIFO del proyecto
        with transaction.atomic():
            proyecto_locked = Proyecto.objects.select_for_update().get(pk=proyecto_id)
            conversacion, _ = Conversacion.objects.get_or_create(proyecto=proyecto_locked)

            cls._limpiar_mensajes_huerfanos(conversacion)

            en_procesamiento_count = conversacion.mensajes.filter(
                estado=Mensaje.Estado.PROCESANDO
            ).count()
            en_cola_count = conversacion.mensajes.filter(
                estado=Mensaje.Estado.EN_COLA
            ).count()

            # FE-04: Cola de espera llena (1 en procesamiento + 2 en espera)
            if en_procesamiento_count >= MAX_EN_PROCESAMIENTO and en_cola_count >= MAX_EN_COLA_ESPERA:
                estado_cola_actual = cls.calcular_estado_cola(conversacion)
                raise AsistenteServiceError(
                    detail=(
                        "La cola de espera del Agente Senior ha alcanzado el límite máximo de "
                        f"{MAX_EN_COLA_ESPERA} consultas en espera. Por favor aguarda a que se libere un espacio."
                    ),
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    codigo="cola_espera_llena",
                    extra={"estado_cola": estado_cola_actual}
                )

            # Determinar estado inicial: «Procesando» (Paso 4) o «En cola» (FA-01 Paso 2)
            if en_procesamiento_count == 0 and en_cola_count == 0:
                estado_inicial = Mensaje.Estado.PROCESANDO
            else:
                estado_inicial = Mensaje.Estado.EN_COLA

            mensaje_usuario = Mensaje.objects.create(
                conversacion=conversacion,
                usuario=user,
                pregunta=None,
                rol=Mensaje.Rol.USER,
                estado=estado_inicial,
                contenido=contenido_limpio
            )

            estado_cola = cls.calcular_estado_cola(conversacion)
            mensaje_serializado = MensajeSerializer(
                mensaje_usuario,
                context={'posiciones_cola': estado_cola['posiciones_cola']}
            ).data

        # 4. Mostrar el mensaje y el estado del agente/cola a todos los colaboradores conectados (Paso 5 / FA-01 Paso 3)
        cls._emitir_evento_ws(
            proyecto_id,
            "agente_senior_mensaje_creado",
            {
                "proyecto_id": proyecto_id,
                "conversacion_id": conversacion.id,
                "mensaje": mensaje_serializado,
                "estado_cola": estado_cola,
            }
        )

        # 5. Asegurar que el worker secuencial del proyecto esté ejecutándose en segundo plano
        cls._asegurar_worker_proyecto(proyecto_id)

        return {
            "conversacion_id": conversacion.id,
            "mensaje": mensaje_serializado,
            "estado_cola": estado_cola,
        }

    @classmethod
    def _asegurar_worker_proyecto(cls, proyecto_id: int) -> None:
        """
        Inicia un hilo daemon por proyecto si no hay uno procesando activamente la cola.
        El hilo se ejecuta de manera independiente de la conexión del cliente, garantizando
        FA-02 y FE-02 (continúa procesando aunque el usuario iniciador pierda su conexión).
        """
        with cls._global_lock:
            if proyecto_id in cls._workers_activos:
                return
            cls._workers_activos.add(proyecto_id)

        hilo = threading.Thread(
            target=cls._ejecutar_worker_cola,
            args=(proyecto_id,),
            name=f"AgenteSeniorWorker-Proj-{proyecto_id}",
            daemon=True
        )
        hilo.start()

    @classmethod
    def _ejecutar_worker_cola(cls, proyecto_id: int) -> None:
        """
        Procesa secuencialmente (FIFO) todas las consultas pendientes del proyecto:
        1. Toma la consulta en estado 'procesando' o promueve la siguiente 'en_cola' a 'procesando' (FA-01 Paso 4).
        2. Recopila el contexto vigente del proyecto en ese preciso instante (Paso 6 / FA-01 Paso 5).
        3. Invoca al proveedor externo de IA (Google Gemini) (Pasos 7 y 8).
        4. En caso de éxito: registra la respuesta ('AGENT') vinculada a 'pregunta_id', actualiza la pregunta
           a 'respondido' y transmite a todos los colaboradores por WebSocket (Pasos 9 y 10).
        5. En caso de fallo (FE-01 y Postcondición de Fallo): registra el error interno, notifica a los
           colaboradores que el agente no está disponible temporalmente y descarta/revierte la consulta
           fallida para mantener intacto el historial y no bloquear la cola.
        """
        close_old_connections()
        lock_proyecto = cls._obtener_lock_proyecto(proyecto_id)

        try:
            with lock_proyecto:
                while True:
                    close_old_connections()
                    mensaje_actual = None
                    conversacion = None
                    fue_promovido_de_cola = False

                    with transaction.atomic():
                        proyecto = Proyecto.objects.select_for_update().filter(pk=proyecto_id).first()
                        if not proyecto:
                            break
                        conversacion = Conversacion.objects.filter(proyecto=proyecto).first()
                        if not conversacion:
                            break

                        # Buscar primero si ya hay un mensaje marcado como PROCESANDO
                        mensaje_actual = (
                            conversacion.mensajes
                            .select_related('usuario')
                            .filter(estado=Mensaje.Estado.PROCESANDO)
                            .order_by('fecha_envio', 'id')
                            .first()
                        )

                        # FA-01 Paso 4: Si no hay ninguno en PROCESANDO, tomar el siguiente en espera (FIFO)
                        if not mensaje_actual:
                            siguiente_en_cola = (
                                conversacion.mensajes
                                .select_related('usuario')
                                .filter(estado=Mensaje.Estado.EN_COLA)
                                .order_by('fecha_envio', 'id')
                                .first()
                            )
                            if not siguiente_en_cola:
                                # No quedan más consultas por procesar en la cola
                                break

                            siguiente_en_cola.estado = Mensaje.Estado.PROCESANDO
                            siguiente_en_cola.save(update_fields=['estado'])
                            mensaje_actual = siguiente_en_cola
                            fue_promovido_de_cola = True

                        estado_cola = cls.calcular_estado_cola(conversacion)
                        mensaje_actual_data = MensajeSerializer(
                            mensaje_actual,
                            context={'posiciones_cola': estado_cola['posiciones_cola']}
                        ).data

                    # Si el mensaje acaba de pasar de 'en_cola' a 'procesando', notificar a todos por WS
                    if fue_promovido_de_cola:
                        cls._emitir_evento_ws(
                            proyecto_id,
                            "agente_senior_estado_actualizado",
                            {
                                "proyecto_id": proyecto_id,
                                "conversacion_id": conversacion.id,
                                "mensaje": mensaje_actual_data,
                                "estado_cola": estado_cola,
                            }
                        )

                    # Paso 6 / FA-01 Paso 5: Recopilar el contexto vigente en este instante
                    try:
                        prompt_contextualizado = cls.construir_prompt_con_contexto(
                            proyecto_id=proyecto_id,
                            conversacion_id=conversacion.id,
                            mensaje_pregunta=mensaje_actual
                        )

                        # Paso 7 y 8: Enviar la consulta y el contexto al proveedor externo de IA
                        texto_respuesta = GeminiProviderService.generar_contenido(
                            contents=[prompt_contextualizado],
                            system_instruction=SYSTEM_PROMPT_AGENTE_SENIOR,
                            response_mime_type=None,
                            temperature=0.3
                        )

                        # Paso 9: Registrar la respuesta generada en el historial y actualizar la consulta a «Respondido»
                        with transaction.atomic():
                            conversacion_ref = Conversacion.objects.select_for_update().get(pk=conversacion.id)
                            pregunta_ref = Mensaje.objects.select_related('usuario').filter(pk=mensaje_actual.id).first()

                            if pregunta_ref:
                                pregunta_ref.estado = Mensaje.Estado.RESPONDIDO
                                pregunta_ref.save(update_fields=['estado'])

                                respuesta_agente = Mensaje.objects.create(
                                    conversacion=conversacion_ref,
                                    usuario=None,
                                    pregunta=pregunta_ref,
                                    rol=Mensaje.Rol.AGENT,
                                    estado=Mensaje.Estado.RESPONDIDO,
                                    contenido=texto_respuesta
                                )

                                # Verificar si hay siguiente mensaje en cola para promoverlo en la misma transición
                                siguiente_cola = (
                                    conversacion_ref.mensajes
                                    .select_related('usuario')
                                    .filter(estado=Mensaje.Estado.EN_COLA)
                                    .order_by('fecha_envio', 'id')
                                    .first()
                                )
                                mensaje_promovido_data = None
                                if siguiente_cola:
                                    siguiente_cola.estado = Mensaje.Estado.PROCESANDO
                                    siguiente_cola.save(update_fields=['estado'])

                                estado_cola_post = cls.calcular_estado_cola(conversacion_ref)
                                pregunta_serializada = MensajeSerializer(
                                    pregunta_ref,
                                    context={'posiciones_cola': estado_cola_post['posiciones_cola']}
                                ).data
                                respuesta_serializada = MensajeSerializer(
                                    respuesta_agente,
                                    context={'posiciones_cola': estado_cola_post['posiciones_cola']}
                                ).data
                                if siguiente_cola:
                                    mensaje_promovido_data = MensajeSerializer(
                                        siguiente_cola,
                                        context={'posiciones_cola': estado_cola_post['posiciones_cola']}
                                    ).data

                        # Paso 10: Mostrar la respuesta a todos los colaboradores conectados y actualizar la cola
                        cls._emitir_evento_ws(
                            proyecto_id,
                            "agente_senior_respuesta",
                            {
                                "proyecto_id": proyecto_id,
                                "conversacion_id": conversacion.id,
                                "pregunta": pregunta_serializada,
                                "respuesta": respuesta_serializada,
                                "siguiente_procesando": mensaje_promovido_data,
                                "estado_cola": estado_cola_post,
                            }
                        )

                    except Exception as exc:
                        # FE-01: Falla de comunicación con el proveedor de IA
                        logger.error(
                            f"[AGENTE_SENIOR_ERROR] Error procesando consulta #{mensaje_actual.id} "
                            f"en proyecto #{proyecto_id}: {exc}"
                        )

                        # Postcondición de Fallo (Pasos 1 y 2):
                        # 1. El estado del historial se mantiene intacto, conservando únicamente los mensajes
                        #    hasta antes del intento fallido.
                        # 2. Se descarta la consulta que no pudo ser procesada, revirtiendo su estado para
                        #    garantizar que no bloquee las interacciones futuras ni la cola de mensajes.
                        pregunta_fallida_id = mensaje_actual.id
                        contenido_fallido = mensaje_actual.contenido
                        autor_id = mensaje_actual.usuario_id
                        autor_username = mensaje_actual.usuario.username if mensaje_actual.usuario else None

                        with transaction.atomic():
                            conversacion_ref = Conversacion.objects.select_for_update().get(pk=conversacion.id)
                            Mensaje.objects.filter(pk=pregunta_fallida_id).update(estado=Mensaje.Estado.ERROR)
                            Mensaje.objects.filter(pk=pregunta_fallida_id).delete()

                            # Promover el siguiente en cola si existía
                            siguiente_cola = (
                                conversacion_ref.mensajes
                                .select_related('usuario')
                                .filter(estado=Mensaje.Estado.EN_COLA)
                                .order_by('fecha_envio', 'id')
                                .first()
                            )
                            mensaje_promovido_data = None
                            if siguiente_cola:
                                siguiente_cola.estado = Mensaje.Estado.PROCESANDO
                                siguiente_cola.save(update_fields=['estado'])

                            estado_cola_err = cls.calcular_estado_cola(conversacion_ref)
                            if siguiente_cola:
                                mensaje_promovido_data = MensajeSerializer(
                                    siguiente_cola,
                                    context={'posiciones_cola': estado_cola_err['posiciones_cola']}
                                ).data

                        # FE-01 Pasos 3 y 4: Mostrar mensaje a los colaboradores indicando que el agente no
                        # está disponible temporalmente y permitir al usuario intentar enviar la consulta nuevamente
                        cls._emitir_evento_ws(
                            proyecto_id,
                            "agente_senior_error",
                            {
                                "proyecto_id": proyecto_id,
                                "conversacion_id": conversacion.id,
                                "pregunta_descartada_id": pregunta_fallida_id,
                                "contenido_original": contenido_fallido,
                                "usuario_id": autor_id,
                                "username": autor_username,
                                "estado": Mensaje.Estado.ERROR,
                                "mensaje_error": (
                                    "El Agente Senior no está disponible temporalmente. "
                                    "Tu consulta no fue cobrada al historial; por favor intenta enviarla nuevamente."
                                ),
                                "siguiente_procesando": mensaje_promovido_data,
                                "estado_cola": estado_cola_err,
                            }
                        )
        finally:
            with cls._global_lock:
                cls._workers_activos.discard(proyecto_id)
            close_old_connections()

    @classmethod
    def construir_prompt_con_contexto(
        cls,
        proyecto_id: int,
        conversacion_id: int,
        mensaje_pregunta: Mensaje
    ) -> str:
        """
        Ensambla el contexto dinámico del proyecto (Requisito Especial 2 y líneas 108–113 de features.md):
        1. Usuario quien envió el mensaje (nombre, username, rol en el proyecto).
        2. Participantes del proyecto (propietario y colaboradores activos).
        3. Información vigente del diagrama: entidades, atributos y relaciones.
        4. Los últimos 20 mensajes registrados de esa conversación (preguntas USER y respuestas AGENT).
        """
        proyecto = (
            Proyecto.objects
            .select_related('propietario')
            .prefetch_related('entidades__atributos', 'relaciones__entidad_origen', 'relaciones__entidad_destino', 'relaciones__clase_asociacion')
            .get(pk=proyecto_id)
        )

        # 1. Información del usuario que realiza la consulta
        usuario_autor = mensaje_pregunta.usuario
        if usuario_autor:
            nombre_completo = f"{usuario_autor.first_name or ''} {usuario_autor.last_name or ''}".strip() or usuario_autor.username
            es_prop = (proyecto.propietario_id == usuario_autor.id)
            rol_en_proyecto = "Propietario del Proyecto" if es_prop else "Colaborador (Editor)"
            info_usuario_consulta = {
                "id": usuario_autor.id,
                "username": usuario_autor.username,
                "nombre_completo": nombre_completo,
                "rol_en_proyecto": rol_en_proyecto,
            }
        else:
            info_usuario_consulta = {
                "username": "Colaborador",
                "nombre_completo": "Colaborador",
                "rol_en_proyecto": "Colaborador",
            }

        # 2. Participantes activos del proyecto
        colaboradores_activos = (
            UserColaborador.objects
            .filter(proyecto=proyecto, estado=UserColaborador.Estado.ACTIVO)
            .select_related('usuario')
        )
        participantes = [
            {
                "username": proyecto.propietario.username,
                "nombre": f"{proyecto.propietario.first_name or ''} {proyecto.propietario.last_name or ''}".strip() or proyecto.propietario.username,
                "rol": "Propietario",
            }
        ]
        for col in colaboradores_activos:
            if col.usuario_id != proyecto.propietario_id:
                participantes.append({
                    "username": col.usuario.username,
                    "nombre": f"{col.usuario.first_name or ''} {col.usuario.last_name or ''}".strip() or col.usuario.username,
                    "rol": "Colaborador",
                })

        # 3. Información del diagrama: entidades, atributos y relaciones
        info_diagrama = cls._recopilar_contexto_diagrama(proyecto)

        # 4. Últimos 20 mensajes registrados en la conversación (preguntas y respuestas previas)
        ultimos_mensajes_qs = (
            Mensaje.objects
            .filter(
                conversacion_id=conversacion_id,
                estado=Mensaje.Estado.RESPONDIDO
            )
            .exclude(pk=mensaje_pregunta.pk)
            .select_related('usuario')
            .order_by('-fecha_envio', '-id')[:ULTIMOS_MENSAJES_HISTORIAL]
        )
        ultimos_mensajes = list(reversed(list(ultimos_mensajes_qs)))

        historial_formateado = []
        for m in ultimos_mensajes:
            if m.rol == Mensaje.Rol.USER:
                autor_nombre = m.usuario.username if m.usuario else "Usuario"
                historial_formateado.append({
                    "id": m.id,
                    "rol": "USER",
                    "usuario": autor_nombre,
                    "fecha_envio": m.fecha_envio.isoformat(),
                    "contenido": m.contenido,
                })
            else:
                historial_formateado.append({
                    "id": m.id,
                    "rol": "AGENT",
                    "pregunta_id": m.pregunta_id,
                    "fecha_envio": m.fecha_envio.isoformat(),
                    "contenido": m.contenido,
                })

        contexto_completo = {
            "proyecto": {
                "id": proyecto.id,
                "codigo": proyecto.codigo,
                "nombre": proyecto.nombre,
                "descripcion": proyecto.descripcion,
                "paquete_base": proyecto.paquete_base,
            },
            "usuario_que_envia_mensaje": info_usuario_consulta,
            "participantes_proyecto": participantes,
            "diagrama_uml": info_diagrama,
            "ultimos_20_mensajes_conversacion": historial_formateado,
        }

        prompt = (
            "=== CONTEXTO ACTUAL DEL PROYECTO Y CONVERSACIÓN COMPARTIDA ===\n"
            f"{json.dumps(contexto_completo, ensure_ascii=False, indent=2)}\n\n"
            "=== CONSULTA ACTUAL DEL USUARIO ===\n"
            f"Usuario: {info_usuario_consulta['nombre_completo']} (@{info_usuario_consulta['username']}) "
            f"[{info_usuario_consulta['rol_en_proyecto']}]\n"
            f"Consulta: \"{mensaje_pregunta.contenido}\"\n\n"
            "Responde como el Agente Senior Colaborativo del proyecto:"
        )
        return prompt

    @classmethod
    def _recopilar_contexto_diagrama(cls, proyecto: Proyecto) -> dict:
        """
        Extrae todas las entidades, atributos y relaciones vigentes del proyecto.
        Si la base de datos relacional tiene entidades, las utiliza; y si hay elementos
        recientes enviados por el cliente en memoria aún pendientes de snapshot, los incorpora.
        """
        entidades_qs = proyecto.entidades.exclude(estado=Entidad.Estado.PAPELERA).order_by('id')
        entidades_lista = []
        mapa_nombres_entidades = {}

        for ent in entidades_qs:
            mapa_nombres_entidades[ent.id] = ent.nombre
            atributos_lista = [
                {
                    "nombre": attr.nombre,
                    "tipo": attr.tipo,
                    "es_clave": attr.es_clave,
                    "es_nulo": attr.es_nulo,
                    "orden": attr.orden,
                }
                for attr in ent.atributos.all().order_by('orden', 'id')
            ]
            entidades_lista.append({
                "id": ent.id,
                "nombre": ent.nombre,
                "es_intermedia": ent.es_intermedia,
                "estado": ent.estado,
                "atributos": atributos_lista,
            })

        relaciones_qs = proyecto.relaciones.filter(
            entidad_origen__in=entidades_qs,
            entidad_destino__in=entidades_qs
        ).order_by('id')

        relaciones_lista = []
        for rel in relaciones_qs:
            relaciones_lista.append({
                "id": rel.id,
                "nombre_relacion": rel.nombre_relacion,
                "tipo": rel.tipo,
                "entidad_origen": rel.entidad_origen.nombre,
                "entidad_destino": rel.entidad_destino.nombre,
                "cardinalidad_origen": rel.cardinalidad_origen,
                "cardinalidad_destino": rel.cardinalidad_destino,
                "clase_asociacion": rel.clase_asociacion.nombre if rel.clase_asociacion else None,
            })

        # Si el cliente envió contexto en memoria con cambios recientes que aún no pasaron por el debounce
        contexto_mem = cls._contexto_diagrama_reciente.get(proyecto.id)
        if isinstance(contexto_mem, dict) and contexto_mem.get('entidades'):
            entidades_mem = contexto_mem.get('entidades') or []
            relaciones_mem = contexto_mem.get('relaciones') or []
            if len(entidades_mem) != len(entidades_lista) or not entidades_lista:
                mapa_mem = {}
                entidades_lista = []
                for e in entidades_mem:
                    if not isinstance(e, dict):
                        continue
                    eid = e.get('id')
                    enombre = e.get('nombre')
                    if eid is not None and enombre:
                        mapa_mem[eid] = enombre
                    entidades_lista.append({
                        "id": eid,
                        "nombre": enombre,
                        "es_intermedia": bool(e.get('es_intermedia', False)),
                        "estado": e.get('estado') or 'activo',
                        "atributos": [
                            {
                                "nombre": a.get('nombre'),
                                "tipo": a.get('tipo'),
                                "es_clave": bool(a.get('es_clave', False)),
                                "es_nulo": bool(a.get('es_nulo', False)),
                            }
                            for a in (e.get('atributos') or [])
                            if isinstance(a, dict) and a.get('nombre')
                        ],
                    })
                if isinstance(relaciones_mem, list):
                    relaciones_lista = []
                    for r in relaciones_mem:
                        if not isinstance(r, dict):
                            continue
                        orig_id = r.get('entidad_origen_id') or r.get('origen_id')
                        dest_id = r.get('entidad_destino_id') or r.get('destino_id')
                        relaciones_lista.append({
                            "id": r.get('id'),
                            "nombre_relacion": r.get('nombre_relacion') or r.get('nombre') or '',
                            "tipo": r.get('tipo') or 'asociacion',
                            "entidad_origen": mapa_mem.get(orig_id, str(orig_id)),
                            "entidad_destino": mapa_mem.get(dest_id, str(dest_id)),
                            "cardinalidad_origen": r.get('cardinalidad_origen') or '',
                            "cardinalidad_destino": r.get('cardinalidad_destino') or '',
                            "clase_asociacion_id": r.get('clase_asociacion_id'),
                        })

        return {
            "total_entidades": len(entidades_lista),
            "total_relaciones": len(relaciones_lista),
            "entidades": entidades_lista,
            "relaciones": relaciones_lista,
        }

    @classmethod
    def _emitir_evento_ws(cls, proyecto_id: int, tipo_evento: str, payload: dict) -> None:
        """
        Envía eventos en tiempo real a través del canal Redis del proyecto hacia todos los
        colaboradores conectados al WebSocket de la pizarra.
        """
        try:
            notificar_evento_proyecto_sync(proyecto_id, tipo_evento, payload)
        except Exception as e:
            logger.warning(f"No se pudo emitir evento WS '{tipo_evento}' en proyecto {proyecto_id}: {e}")


# =====================================================================
# SERVICIOS EXISTENTES DE ASISTENTE (BOCETO IMAGEN Y COPILOTO COMANDOS)
# =====================================================================

class DiagramaImagenService:
    """
    Servicio para procesar imágenes de diagramas dibujados a mano mediante Google Gemini
    y transformarlos en estructura JSON de entidades y relaciones.
    """

    @classmethod
    def generar_desde_request(cls, files: dict, data: dict) -> dict:
        imagen_bytes = None
        mime_type = "image/jpeg"

        if 'imagen' in files:
            archivo = files['imagen']
            mime_type = archivo.content_type or "image/jpeg"
            imagen_bytes = archivo.read()
        elif 'archivo' in files:
            archivo = files['archivo']
            mime_type = archivo.content_type or "image/jpeg"
            imagen_bytes = archivo.read()
        elif 'imagen_b64' in data or 'imagen' in data:
            raw_b64 = data.get('imagen_b64') or data.get('imagen')
            if isinstance(raw_b64, str):
                if 'base64,' in raw_b64:
                    encabezado, data_b64 = raw_b64.split('base64,', 1)
                    if 'data:' in encabezado and ';' in encabezado:
                        mime_type = encabezado.replace('data:', '').replace(';', '').strip()
                else:
                    data_b64 = raw_b64
                try:
                    imagen_bytes = base64.b64decode(data_b64)
                except Exception as e:
                    raise AsistenteServiceError(
                        detail=f"Formato base64 de la imagen inválido: {str(e)}",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

        if not imagen_bytes:
            raise AsistenteServiceError(
                detail="Debe enviar una imagen del boceto (campo 'imagen' como archivo o base64).",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        instrucciones_extra = (data.get('instrucciones') or data.get('prompt') or '').strip()
        texto_usuario = (
            "Analiza minuciosamente este boceto de diagrama y extrae todas las entidades, "
            "atributos y relaciones en formato JSON según las instrucciones del sistema."
        )
        if instrucciones_extra:
            texto_usuario += f"\n\nInstrucciones adicionales del usuario: {instrucciones_extra}"

        part_imagen = types.Part.from_bytes(data=imagen_bytes, mime_type=mime_type)
        texto_respuesta = GeminiProviderService.generar_contenido(
            contents=[part_imagen, texto_usuario],
            system_instruction=SYSTEM_PROMPT_IMAGEN,
            response_mime_type="application/json",
            temperature=0.2
        )

        diagrama_json = cls._parsear_json_respuesta(texto_respuesta)
        entidades = diagrama_json.get('entidades') or []
        relaciones = diagrama_json.get('relaciones') or []

        return {
            "entidades": entidades,
            "relaciones": relaciones,
            "total_entidades": len(entidades),
            "total_relaciones": len(relaciones),
        }

    @staticmethod
    def _parsear_json_respuesta(texto_respuesta: str) -> dict:
        try:
            parsed = json.loads(texto_respuesta)
        except json.JSONDecodeError:
            inicio = texto_respuesta.find('{')
            fin = texto_respuesta.rfind('}')
            if inicio != -1 and fin != -1 and fin > inicio:
                try:
                    parsed = json.loads(texto_respuesta[inicio:fin + 1])
                except Exception:
                    raise AsistenteServiceError(
                        detail="La IA devolvió un formato no interpretable como JSON.",
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        extra={"raw": texto_respuesta}
                    )
            else:
                raise AsistenteServiceError(
                    detail="La respuesta de la IA no contiene una estructura JSON válida.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    extra={"raw": texto_respuesta}
                )

        if not isinstance(parsed, dict):
            raise AsistenteServiceError(
                detail="La respuesta procesada no es un objeto JSON.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                extra={"raw": parsed}
            )
        return parsed


class InstruccionAsistenteService:
    """
    Servicio para procesar comandos/instrucciones breves de modelado en lenguaje natural
    y devolver un delta de acciones sobre el diagrama.
    """

    @classmethod
    def ejecutar_instruccion(cls, data: dict) -> dict:
        instruccion = (data.get('instruccion') or data.get('comando') or '').strip()
        if not instruccion:
            raise AsistenteServiceError(
                detail="Debe proporcionar una instrucción o comando para el asistente.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        contexto = data.get('contexto_diagrama') or {}
        contexto_limpio = {
            "entidades": [
                {
                    "id": ent.get('id'),
                    "nombre": ent.get('nombre'),
                    "estado": ent.get('estado') or 'activo',
                    "atributos": [
                        {
                            "nombre": a.get('nombre'),
                            "tipo": a.get('tipo'),
                            "es_clave": a.get('es_clave', False),
                            "es_nulo": a.get('es_nulo', False)
                        }
                        for a in (ent.get('atributos') or [])
                        if isinstance(a, dict) and a.get('nombre')
                    ]
                }
                for ent in (contexto.get('entidades') or [])
                if isinstance(ent, dict) and ent.get('id') is not None
            ],
            "relaciones": [
                {
                    "id": rel.get('id'),
                    "origen_id": rel.get('entidad_origen_id'),
                    "destino_id": rel.get('entidad_destino_id'),
                    "tipo": rel.get('tipo'),
                    "nombre": rel.get('nombre_relacion')
                }
                for rel in (contexto.get('relaciones') or [])
                if isinstance(rel, dict) and rel.get('id') is not None
            ]
        }

        prompt_usuario = (
            f"Instrucción del usuario:\n\"{instruccion}\"\n\n"
            f"Contexto actual del diagrama (entidades y relaciones existentes):\n"
            f"{json.dumps(contexto_limpio, ensure_ascii=False)}"
        )

        texto_respuesta = GeminiProviderService.generar_contenido(
            contents=[prompt_usuario],
            system_instruction=SYSTEM_PROMPT_INSTRUCCIONES,
            response_mime_type="application/json",
            temperature=0.1
        )

        delta_json = DiagramaImagenService._parsear_json_respuesta(texto_respuesta)

        return {
            "mensaje": delta_json.get('mensaje') or "Instrucción procesada correctamente.",
            "entidades_a_crear": delta_json.get('entidades_a_crear') or [],
            "entidades_a_modificar": delta_json.get('entidades_a_modificar') or [],
            "entidades_a_eliminar": delta_json.get('entidades_a_eliminar') or [],
            "relaciones_a_crear": delta_json.get('relaciones_a_crear') or [],
            "relaciones_a_eliminar": delta_json.get('relaciones_a_eliminar') or [],
        }

