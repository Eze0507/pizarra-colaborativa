import json
from rest_framework import status

from . import AsistenteServiceError, GeminiProviderService


SYSTEM_PROMPT_INSTRUCCIONES = """Actúa como un copiloto y asistente interactivo de modelado de bases de datos relacionales y diagramas de clases UML.
El usuario te dará una orden o instrucción breve (mediante voz o texto) para realizar tareas pequeñas y específicas en su diagrama.
Recibirás:
1. "instruccion": la orden del usuario (ej: "crea la tabla cliente con id y nombre", "agrega el campo email a cliente", "relaciona cliente con factura", "elimina la tabla temporal").
2. "contexto_diagrama": lista resumida de entidades existentes (id, nombre, estado: 'activo' o 'bloqueado', atributos) y relaciones actuales (id, entidad_origen_id, entidad_destino_id, nombre_relacion, cardinalidad_origen, cardinalidad_destino).

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
   - Cardinalidades: conserva las cardinalidades de relaciones existentes incluidas en "contexto_diagrama". Para relaciones nuevas, NO asignes cardinalidades por defecto: deja "cardinalidad_origen": "" y "cardinalidad_destino": "" a menos que se soliciten explícitamente.
5. ÓRDENES COMPUESTAS (CREAR Y RELACIONAR SIMULTÁNEAMENTE):
   - Agrega la entidad a "entidades_a_crear" y define la relación en "relaciones_a_crear".
6. REGLA ESTRICTA PARA RELACIONES DE MUCHOS A MUCHOS (M:M, N:M, "muchos a muchos", "clase de asociación"):
   - Crea la entidad intermedia en "entidades_a_crear" con "es_intermedia": true y vincúlala en "relaciones_a_crear" mediante "clase_asociacion_nombre" con cardinalidades "0..*".
7. Si el usuario pide eliminar:
   - Si no está bloqueada, coloca su id en "entidades_a_eliminar" o "relaciones_a_eliminar".
8. Si la instrucción no requiere cambios:
   - Deja las listas de cambios vacías (`[]`) y responde en "mensaje".
"""


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
                    "nombre": rel.get('nombre_relacion'),
                    "cardinalidad_origen": rel.get('cardinalidad_origen') or '',
                    "cardinalidad_destino": rel.get('cardinalidad_destino') or ''
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

        delta_json = GeminiProviderService.parsear_json_respuesta(texto_respuesta)

        return {
            "mensaje": delta_json.get('mensaje') or "Instrucción procesada correctamente.",
            "entidades_a_crear": delta_json.get('entidades_a_crear') or [],
            "entidades_a_modificar": delta_json.get('entidades_a_modificar') or [],
            "entidades_a_eliminar": delta_json.get('entidades_a_eliminar') or [],
            "relaciones_a_crear": delta_json.get('relaciones_a_crear') or [],
            "relaciones_a_eliminar": delta_json.get('relaciones_a_eliminar') or [],
        }

