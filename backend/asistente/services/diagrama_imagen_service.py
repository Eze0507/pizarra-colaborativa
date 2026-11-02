import base64
from rest_framework import status
from google.genai import types

from . import AsistenteServiceError, GeminiProviderService


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

        diagrama_json = GeminiProviderService.parsear_json_respuesta(texto_respuesta)
        entidades = diagrama_json.get('entidades') or []
        relaciones = diagrama_json.get('relaciones') or []

        return {
            "entidades": entidades,
            "relaciones": relaciones,
            "total_entidades": len(entidades),
            "total_relaciones": len(relaciones),
        }

