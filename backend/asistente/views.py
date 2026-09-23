import os
import json
import base64
import logging
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from google import genai
from google.genai import types
from google.genai.errors import ServerError, APIError

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Actúa como un arquitecto de software y modelador de bases de datos relacionales estricto.
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
   - "cardinalidad_origen": "0..*" (o "1..*" o "*").
   - "cardinalidad_destino": "0..*" (o "1..*" o "*").
   - "clase_asociacion_id": el "id" numérico de la tabla intermedia creada en el paso 1.
¡CRÍTICO!: NUNCA crees dos relaciones separadas y directas hacia la tabla intermedia. En este modelador conceptual, la tabla intermedia NO recibe flechas directas; se vincula exclusivamente a través de "clase_asociacion_id" en la relación principal (lo que hace que la herramienta dibuje automáticamente el conector punteado oficial UML hacia el centro de la relación).
IMPORTANTE: "es_intermedia" DEBE SER FALSE para todas las entidades normales que no sean una tabla intermedia / clase de asociación.

FORMATO DE SALIDA:
Debes responder EXCLUSIVAMENTE con un objeto JSON válido con la siguiente estructura exacta:
{
  "entidades": [
    {
      "id": 1,
      "nombre": "cliente",
      "pos_x": 200,
      "pos_y": 200,
      "es_intermedia": false,
      "atributos": [
        {
          "id": 101,
          "nombre": "id",
          "tipo": "integer",
          "es_clave": true,
          "es_nulo": false,
          "orden": 1
        }
      ]
    },
    {
      "id": 2,
      "nombre": "producto",
      "pos_x": 800,
      "pos_y": 200,
      "es_intermedia": false,
      "atributos": [
        {
          "id": 201,
          "nombre": "id",
          "tipo": "integer",
          "es_clave": true,
          "es_nulo": false,
          "orden": 1
        }
      ]
    },
    {
      "id": 3,
      "nombre": "cliente_producto",
      "pos_x": 500,
      "pos_y": 100,
      "es_intermedia": true,
      "atributos": [
        {
          "id": 301,
          "nombre": "id",
          "tipo": "integer",
          "es_clave": true,
          "es_nulo": false,
          "orden": 1
        },
        {
          "id": 302,
          "nombre": "fecha",
          "tipo": "date",
          "es_clave": false,
          "es_nulo": false,
          "orden": 2
        }
      ]
    }
  ],
  "relaciones": [
    {
      "id": 1,
      "nombre_relacion": "compra",
      "tipo": "asociacion",
      "entidad_origen_id": 1,
      "entidad_destino_id": 2,
      "cardinalidad_origen": "0..*",
      "cardinalidad_destino": "0..*",
      "clase_asociacion_id": 3
    }
  ]
}
"""


class GenerarDiagramaDesdeImagenView(APIView):
    """
    Endpoint para procesar imágenes de diagramas dibujados a mano
    mediante Google Gemini y transformarlos en estructura JSON de entidades y relaciones.
    No persiste datos en la base de datos PostgreSQL.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, *args, **kwargs):
        api_key = getattr(settings, 'GEMINI_API_KEY', None) or os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return Response(
                {"error": "La clave GEMINI_API_KEY no está configurada en las variables de entorno."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        imagen_bytes = None
        mime_type = "image/jpeg"

        # 1. Obtener imagen desde archivo adjunto (multipart/form-data)
        if 'imagen' in request.FILES:
            archivo = request.FILES['imagen']
            mime_type = archivo.content_type or "image/jpeg"
            imagen_bytes = archivo.read()
        elif 'archivo' in request.FILES:
            archivo = request.FILES['archivo']
            mime_type = archivo.content_type or "image/jpeg"
            imagen_bytes = archivo.read()
        # 2. Obtener imagen desde base64 (JSON)
        elif 'imagen_b64' in request.data or 'imagen' in request.data:
            raw_b64 = request.data.get('imagen_b64') or request.data.get('imagen')
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
                    return Response(
                        {"error": f"Formato base64 de la imagen inválido: {str(e)}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        if not imagen_bytes:
            return Response(
                {"error": "Debe enviar una imagen del boceto (campo 'imagen' como archivo o base64)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        instrucciones_extra = (request.data.get('instrucciones') or request.data.get('prompt') or '').strip()
        texto_usuario = "Analiza minuciosamente este boceto de diagrama y extrae todas las entidades, atributos y relaciones en formato JSON según las instrucciones del sistema."
        if instrucciones_extra:
            texto_usuario += f"\n\nInstrucciones adicionales del usuario: {instrucciones_extra}"

        modelo_principal = getattr(settings, 'GEMINI_MODEL', 'gemini-3.8-flash')
        candidatos = [modelo_principal, 'gemini-flash-latest', 'gemini-3.6-flash', 'gemini-3.5-flash-lite', 'gemini-3.5-flash']
        modelos_a_probar = []
        for m in candidatos:
            if m and m not in modelos_a_probar:
                modelos_a_probar.append(m)

        client = genai.Client(api_key=api_key)
        part_imagen = types.Part.from_bytes(data=imagen_bytes, mime_type=mime_type)

        ultimo_error = None
        texto_respuesta = None

        for modelo in modelos_a_probar:
            try:
                response = client.models.generate_content(
                    model=modelo,
                    contents=[part_imagen, texto_usuario],
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        temperature=0.2,
                    )
                )
                if response and response.text:
                    texto_respuesta = response.text
                    break
            except ServerError as se:
                import time
                time.sleep(0.5)
                logger.warning(f"Error de servidor temporal en modelo {modelo}: {se}. Intentando siguiente modelo...")
                ultimo_error = se
            except APIError as ae:
                logger.warning(f"Error de API en modelo {modelo}: {ae}. Intentando siguiente modelo...")
                ultimo_error = ae
            except Exception as e:
                logger.error(f"Error inesperado al invocar modelo {modelo}: {e}")
                ultimo_error = e

        if not texto_respuesta:
            return Response(
                {"error": f"No se pudo obtener respuesta de la IA. Detalle: {str(ultimo_error)}"},
                status=status.HTTP_502_BAD_GATEWAY
            )

        try:
            diagrama_json = json.loads(texto_respuesta)
        except json.JSONDecodeError as jde:
            # Fallback en caso de caracteres adicionales
            inicio = texto_respuesta.find('{')
            fin = texto_respuesta.rfind('}')
            if inicio != -1 and fin != -1 and fin > inicio:
                try:
                    diagrama_json = json.loads(texto_respuesta[inicio:fin+1])
                except Exception:
                    return Response(
                        {"error": "La IA devolvió un formato no interpretable como JSON.", "raw": texto_respuesta},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:
                return Response(
                    {"error": "La respuesta de la IA no contiene una estructura JSON válida.", "raw": texto_respuesta},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        if not isinstance(diagrama_json, dict):
            return Response(
                {"error": "La respuesta procesada no es un objeto JSON.", "raw": diagrama_json},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        entidades = diagrama_json.get('entidades') or []
        relaciones = diagrama_json.get('relaciones') or []

        return Response(
            {
                "entidades": entidades,
                "relaciones": relaciones,
                "total_entidades": len(entidades),
                "total_relaciones": len(relaciones)
            },
            status=status.HTTP_200_OK
        )


SYSTEM_PROMPT_INSTRUCCIONES = """Actúa como un copiloto y asistente interactivo de modelado de bases de datos relacionales y diagramas de clases UML.
El usuario te dará una orden o instrucción breve (mediante voz o texto) para realizar tareas pequeñas y específicas en su diagrama.
Recibirás:
1. "instruccion": la orden del usuario (ej: "crea la tabla cliente con id y nombre", "agrega el campo email a cliente", "relaciona cliente con factura", "elimina la tabla temporal").
2. "contexto_diagrama": lista resumida de entidades existentes (id, nombre, estado: 'activo' o 'bloqueado', atributos) y relaciones actuales (id, entidad_origen_id, entidad_destino_id, nombre_relacion).

Tu objetivo es interpretar la orden con precisión y devolver un delta estructurado de cambios a aplicar en el diagrama, junto con un mensaje conversacional amigable y breve en español.

REGLAS ESTRICTAS DE RESPUESTA:
- Debes responder EXCLUSIVAMENTE con un JSON válido con la siguiente estructura:
{
  "mensaje": "Mensaje conciso confirmando lo que hiciste (ej: 'He creado la entidad Proveedor con sus atributos.')",
  "entidades_a_crear": [
    {
      "nombre": "nombre_entidad",
      "es_intermedia": false,
      "atributos": [
        {
          "nombre": "nombre_campo",
          "tipo": "string",
          "es_clave": true,
          "es_nulo": false,
          "orden": 1
        }
      ]
    }
  ],
  "entidades_a_modificar": [
    {
      "entidad_id": 123,
      "entidad_nombre": "producto",
      "nuevo_nombre": null,
      "atributos_nuevos": [
        {
          "nombre": "nuevo_campo",
          "tipo": "string",
          "es_clave": false,
          "es_nulo": true,
          "orden": 4
        }
      ],
      "atributos_a_modificar": [
        {
          "nombre_original": "precio",
          "nombre": "precio",
          "tipo": "double",
          "es_clave": false,
          "es_nulo": false
        }
      ],
      "atributos_a_eliminar": []
    }
  ],
  "entidades_a_eliminar": [],
  "relaciones_a_crear": [
    {
      "nombre_relacion": "",
      "tipo": "asociacion",
      "entidad_origen_id": 101,
      "entidad_destino_id": null,
      "entidad_origen_nombre": "cliente",
      "entidad_destino_nombre": "pedido",
      "cardinalidad_origen": "",
      "cardinalidad_destino": "",
      "clase_asociacion_nombre": null
    }
  ],
  "relaciones_a_eliminar": []
}

REGLAS DE INTERPRETACIÓN:
1. CONTROL DE EXCLUSIÓN MUTUA (ENTIDADES BLOQUEADAS):
   - Si una entidad existente en "contexto_diagrama" tiene "estado": "bloqueado", significa que otro usuario la está editando.
   - NUNCA agregues ni modifiques atributos a esa entidad en "entidades_a_modificar".
   - NUNCA agregues esa entidad a "entidades_a_eliminar".
   - Si el usuario pide modificar o eliminar una entidad que está bloqueada, NO agregues los cambios en el delta y adviértelo en "mensaje" (ej: "La entidad 'cliente' se encuentra bloqueada por otro usuario y no puede ser modificada ni eliminada en este momento.").
2. Si el usuario pide crear una entidad nueva:
   - "nombre": nombre conceptual en singular (ej: "proveedor", "producto").
   - Si no especificó clave primaria, agrega un campo "id" tipo "integer" con es_clave: true.
   - Si no especificó tipo para algún atributo, infiere el tipo más coherente entre los 6 permitidos: "string", "integer", "long", "double", "boolean", "date".
3. Si el usuario pide modificar una entidad existente o sus atributos:
   - Busca la entidad en "contexto_diagrama" por nombre (ignorando mayúsculas/minúsculas).
   - Verifica que NO esté en estado "bloqueado".
   - Usa su "entidad_id" real en "entidades_a_modificar" y opcionalmente "entidad_nombre".
   a) Si pide EDITAR, MODIFICAR O CAMBIAR un atributo YA EXISTENTE (ej: cambiar su tipo de dato, hacerlo nulo/opcional, cambiar si es clave primaria o cambiar su nombre):
      - ¡CRÍTICO!: NUNCA lo coloques en "atributos_nuevos" porque crearía un atributo duplicado.
      - Agrégalo OBLIGATORIAMENTE a "atributos_a_modificar":
        * "nombre_original": el nombre actual con el que figura el atributo en "contexto_diagrama" (ej: "precio").
        * "nombre": el nuevo nombre (si se renombra) o el mismo nombre (si solo cambia tipo o restricciones).
        * "tipo": el tipo de dato actualizado ("string", "integer", "long", "double", "boolean", "date").
        * "es_clave": true/false según corresponda.
        * "es_nulo": true/false según corresponda.
   b) Si pide AGREGAR un atributo que NO existía previamente en la entidad:
      - Agrégalo a "atributos_nuevos".
      - "orden": debe ser correlativo a partir de la cantidad de atributos que ya tiene esa entidad.
   c) Si pide ELIMINAR un atributo específico de la entidad:
      - Agrega el nombre del atributo a "atributos_a_eliminar" (ej: ["telefono"]).
   d) Si pide RENOMBRAR la entidad:
      - Asigna el nuevo nombre en "nuevo_nombre" (ej: "cliente_empresa").
4. Si el usuario pide relacionar dos entidades:
   - Busca las entidades por nombre en "contexto_diagrama" o en "entidades_a_crear".
   - "tipo": "asociacion" por defecto a menos que se pida "composicion", "agregacion" o "herencia".
   - En "composicion" o "agregacion": "entidad_origen_nombre" DEBE ser la PARTE y "entidad_destino_nombre" DEBE ser el CONTENEDOR / TODO donde se dibuja el rombo.
   - En "herencia": "entidad_origen_nombre" es la subclase (hijo) y "entidad_destino_nombre" es la superclase (padre).
   - Cardinalidades: NO asignes cardinalidades por defecto. Deja "cardinalidad_origen": "" y "cardinalidad_destino": "" (vacías) a menos que el usuario solicite explícitamente multiplicidades (ej. "1 a N", "1 a 1", etc.).
   - Especifica siempre "entidad_origen_nombre" y "entidad_destino_nombre".
5. ÓRDENES COMPUESTAS (CREAR Y RELACIONAR SIMULTÁNEAMENTE):
   - Si el usuario pide crear una entidad (con X atributos) y en el mismo pedido relacionarla con otra (sea existente o también creada):
     a) Agrega la entidad a "entidades_a_crear" con sus atributos completos.
     b) En "relaciones_a_crear", define la relación asignando "entidad_origen_nombre" y "entidad_destino_nombre" con los nombres exactos de ambas tablas (además de colocar el ID numérico en entidad_origen_id o entidad_destino_id si alguna de ellas ya existía en contexto_diagrama).
6. REGLA ESTRICTA PARA RELACIONES DE MUCHOS A MUCHOS (M:M, N:M, "muchos a muchos", "clase de asociación"):
   En el modelado relacional y en esta herramienta CASE, una relación de muchos a muchos NUNCA debe ser una simple línea directa entre las dos entidades. DEBE representarse obligatoriamente mediante una Clase de Asociación (Tabla Intermedia).
   Por lo tanto, cuando el usuario pida relacionar dos entidades con "muchos a muchos", "M:M", "N:M" o "clase de asociación":
   a) En "entidades_a_crear", DEBES crear la entidad intermedia:
      - "nombre": nombre compuesto en minúsculas en formato "<origen>_<destino>" (ej: "estudiante_materia", "cliente_producto") o el nombre conceptual específico que el usuario haya indicado (ej: "inscripcion", "matricula", "detalle_venta").
      - "es_intermedia": true
      - "atributos": incluye al menos la clave primaria obligatoria {"nombre": "id", "tipo": "integer", "es_clave": true, "es_nulo": false, "orden": 1}. Si el usuario pide atributos adicionales (ej. "con fecha y calificacion"), agrégalos a continuación respetando tipos y correlatividad de orden.
   b) En "relaciones_a_crear", crea la relación principal entre las dos entidades:
      - "nombre_relacion": verbo o nombre si lo indicó, o ""
      - "tipo": "asociacion"
      - "entidad_origen_nombre": nombre de la entidad origen
      - "entidad_destino_nombre": nombre de la entidad destino
      - "entidad_origen_id": id de la entidad origen (si ya existía) o null
      - "entidad_destino_id": id de la entidad destino (si ya existía) o null
      - "cardinalidad_origen": "0..*"
      - "cardinalidad_destino": "0..*"
      - "clase_asociacion_nombre": el nombre exacto de la entidad intermedia creada en "entidades_a_crear" (ej: "estudiante_materia").
7. Si el usuario pide eliminar:
   - Busca la entidad en "contexto_diagrama". Si está en estado "bloqueado", no la elimines. Si no está bloqueada, coloca su id en "entidades_a_eliminar" o "relaciones_a_eliminar".
8. Si la instrucción no requiere cambios (ej. un saludo, una duda conceptual o no se entiende):
   - Deja las listas de cambios vacías (`[]`) y responde con un mensaje orientativo y cordial en "mensaje".
"""


class EjecutarInstruccionAsistenteView(APIView):
    """
    Endpoint para procesar comandos/instrucciones breves de modelado en lenguaje natural
    (dictados por voz o escritos en el chat) y devolver un delta de acciones sobre el diagrama.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        api_key = getattr(settings, 'GEMINI_API_KEY', None) or os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return Response(
                {"error": "La clave GEMINI_API_KEY no está configurada en las variables de entorno."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        instruccion = (request.data.get('instruccion') or request.data.get('comando') or '').strip()
        if not instruccion:
            return Response(
                {"error": "Debe proporcionar una instrucción o comando para el asistente."},
                status=status.HTTP_400_BAD_REQUEST
            )

        contexto = request.data.get('contexto_diagrama') or {}
        # Aseguramos que el contexto sea ligero y no contenga basura visual
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

        modelo_principal = getattr(settings, 'GEMINI_MODEL', 'gemini-3.8-flash')
        candidatos = [modelo_principal, 'gemini-flash-latest', 'gemini-3.6-flash', 'gemini-3.5-flash-lite']
        modelos_a_probar = []
        for m in candidatos:
            if m and m not in modelos_a_probar:
                modelos_a_probar.append(m)

        client = genai.Client(api_key=api_key)
        ultimo_error = None
        texto_respuesta = None

        for modelo in modelos_a_probar:
            try:
                response = client.models.generate_content(
                    model=modelo,
                    contents=[prompt_usuario],
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT_INSTRUCCIONES,
                        response_mime_type="application/json",
                        temperature=0.1,
                    )
                )
                if response and response.text:
                    texto_respuesta = response.text
                    break
            except ServerError as se:
                import time
                time.sleep(0.4)
                logger.warning(f"Error de servidor temporal en modelo {modelo}: {se}.")
                ultimo_error = se
            except APIError as ae:
                logger.warning(f"Error de API en modelo {modelo}: {ae}.")
                ultimo_error = ae
            except Exception as e:
                logger.error(f"Error inesperado en modelo {modelo}: {e}")
                ultimo_error = e

        if not texto_respuesta:
            return Response(
                {"error": f"No se pudo procesar la instrucción con la IA. Detalle: {str(ultimo_error)}"},
                status=status.HTTP_502_BAD_GATEWAY
            )

        try:
            delta_json = json.loads(texto_respuesta)
        except json.JSONDecodeError:
            inicio = texto_respuesta.find('{')
            fin = texto_respuesta.rfind('}')
            if inicio != -1 and fin != -1 and fin > inicio:
                try:
                    delta_json = json.loads(texto_respuesta[inicio:fin+1])
                except Exception:
                    return Response(
                        {"error": "Formato de respuesta de la IA inválido.", "raw": texto_respuesta},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:
                return Response(
                    {"error": "La respuesta de la IA no contiene JSON válido.", "raw": texto_respuesta},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        if not isinstance(delta_json, dict):
            return Response(
                {"error": "La respuesta procesada no es un objeto JSON.", "raw": delta_json},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {
                "mensaje": delta_json.get('mensaje') or "Instrucción procesada correctamente.",
                "entidades_a_crear": delta_json.get('entidades_a_crear') or [],
                "entidades_a_modificar": delta_json.get('entidades_a_modificar') or [],
                "entidades_a_eliminar": delta_json.get('entidades_a_eliminar') or [],
                "relaciones_a_crear": delta_json.get('relaciones_a_crear') or [],
                "relaciones_a_eliminar": delta_json.get('relaciones_a_eliminar') or []
            },
            status=status.HTTP_200_OK
        )

