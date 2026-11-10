import os
import json
import time
import logging
import urllib.request
import urllib.error

import httpx

from django.conf import settings
from rest_framework import status

from google import genai
from google.genai import types
from google.genai.errors import ServerError, APIError

logger = logging.getLogger(__name__)


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


class OllamaProviderService:
    """
    Servicio auxiliar para invocar un modelo de IA local ejecutándose en Ollama
    (por ejemplo qwen2.5:3b en 0.0.0.0:11434 / host.docker.internal:11434).
    Usa streaming interno (stream=True) para evitar timeouts de socket cuando
    el modelo local se ejecuta en CPU.
    """

    TIMEOUT_PING_SEGUNDOS = 3
    TIMEOUT_LECTURA_STREAM_SEGUNDOS = 120

    @staticmethod
    def obtener_urls_candidatas() -> list[str]:
        url_config = (
            getattr(settings, 'OLLAMA_BASE_URL', None)
            or os.environ.get('OLLAMA_BASE_URL')
            or 'http://host.docker.internal:11434'
        ).rstrip('/')

        candidatas = [
            url_config,
            'http://host.docker.internal:11434',
            'http://127.0.0.1:11434',
            'http://0.0.0.0:11434',
        ]
        urls = []
        for u in candidatas:
            if u and u not in urls:
                urls.append(u)
        return urls

    @staticmethod
    def obtener_modelo_local() -> str:
        return (
            getattr(settings, 'OLLAMA_MODEL', None)
            or os.environ.get('OLLAMA_MODEL')
            or 'qwen2.5:3b'
        )

    @classmethod
    def detectar_url_activa(cls) -> str | None:
        for base_url in cls.obtener_urls_candidatas():
            try:
                req = urllib.request.Request(f"{base_url}/api/tags", method="GET")
                with urllib.request.urlopen(req, timeout=cls.TIMEOUT_PING_SEGUNDOS) as resp:
                    if resp.status == 200:
                        return base_url
            except Exception:
                continue
        return None

    @classmethod
    def generar_contenido(
        cls,
        prompt: str,
        system_instruction: str,
        temperature: float = 0.3,
        modelo: str | None = None
    ) -> str:
        modelo_efectivo = modelo or cls.obtener_modelo_local()
        base_url = cls.detectar_url_activa()
        if not base_url:
            raise AsistenteServiceError(
                detail=f"El motor local Ollama ({modelo_efectivo}) no es alcanzable en el puerto 11434.",
                status_code=status.HTTP_502_BAD_GATEWAY,
                codigo="ollama_no_alcanzable"
            )

        endpoint = f"{base_url}/api/chat"
        payload = {
            "model": modelo_efectivo,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_ctx": 4096,
                "num_predict": 700,
            },
        }
        body_bytes = json.dumps(payload).encode('utf-8')

        try:
            logger.info(
                f"[OLLAMA_LOCAL] Enviando petición al modelo local '{modelo_efectivo}' "
                f"en {endpoint} (prompt={len(prompt)} chars)..."
            )
            t0 = time.time()
            req = urllib.request.Request(
                endpoint,
                data=body_bytes,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            fragmentos: list[str] = []
            with urllib.request.urlopen(req, timeout=cls.TIMEOUT_LECTURA_STREAM_SEGUNDOS) as resp:
                for raw_line in resp:
                    line = raw_line.decode('utf-8', errors='replace').strip()
                    if not line:
                        continue
                    chunk = json.loads(line)
                    pieza = (
                        (chunk.get('message') or {}).get('content')
                        or chunk.get('response')
                        or ''
                    )
                    if pieza:
                        fragmentos.append(pieza)
                    if chunk.get('done'):
                        break

            texto_final = "".join(fragmentos).strip()
            if texto_final:
                duracion = round(time.time() - t0, 2)
                logger.info(
                    f"[OLLAMA_LOCAL] Respuesta recibida exitosamente de '{modelo_efectivo}' "
                    f"en {duracion}s ({len(texto_final)} chars)."
                )
                return texto_final
        except Exception as exc:
            logger.warning(f"[OLLAMA_LOCAL] Error durante generación en {endpoint} ({modelo_efectivo}): {exc}")
            raise AsistenteServiceError(
                detail=f"El modelo local Ollama ({modelo_efectivo}) falló: {exc}",
                status_code=status.HTTP_502_BAD_GATEWAY,
                codigo="ollama_no_disponible"
            )

        raise AsistenteServiceError(
            detail=f"El modelo local Ollama ({modelo_efectivo}) devolvió una respuesta vacía.",
            status_code=status.HTTP_502_BAD_GATEWAY,
            codigo="ollama_respuesta_vacia"
        )


class GeminiProviderService:
    """
    Servicio auxiliar compartido para invocar a Google Gemini utilizando la
    misma GEMINI_API_KEY configurada en el proyecto y manejo de fallback de modelos.
    """

    # Timeout por intento de modelo en milisegundos (40 segundos para evitar 504 DEADLINE_EXCEEDED prematuro)
    TIMEOUT_MODELO_MS = 40000

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
            'gemini-3.7-flash',
            'gemini-3.6-flash',
            'gemini-3.5-flash',
            'gemini-3.5-flash-lite',
            'gemini-3.1-flash-lite',
            'gemini-flash-lite-latest',
            'gemini-flash-latest',
        ]
        modelos_a_probar = []
        for m in candidatos:
            if m and m not in modelos_a_probar:
                modelos_a_probar.append(m)
        return modelos_a_probar

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

    @classmethod
    def generar_chat_con_metadatos(
        cls,
        turnos: list[dict],
        system_instruction: str,
        temperature: float = 0.2
    ) -> dict:
        """
        Ejecuta una conversación del Agente Senior conservando el modelo Gemini
        que produjo la respuesta. Este método es adicional: ``generar_contenido``
        mantiene su contrato histórico de retorno ``str`` para los demás flujos.
        """
        contenidos = []
        for turno in turnos:
            role = turno.get('role')
            content = str(turno.get('content') or '').strip()
            if not content:
                continue
            if role not in {'user', 'model'}:
                raise ValueError(f"Rol Gemini no soportado: {role!r}")
            contenidos.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=content)]
            ))

        if not contenidos or contenidos[-1].role != 'user':
            raise ValueError("La conversación Gemini debe finalizar con un turno de usuario.")

        api_key = cls.obtener_api_key()
        http_opts = types.HttpOptions(timeout=cls.TIMEOUT_MODELO_MS)
        client = genai.Client(api_key=api_key, http_options=http_opts)
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            http_options=http_opts,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )

        inicio_total = time.perf_counter()
        intentos = []
        for numero_intento, modelo in enumerate(cls.obtener_modelos_candidatos(), start=1):
            inicio_intento = time.perf_counter()
            try:
                logger.info(
                    "[GEMINI_AGENTE_SENIOR] Intento %s con modelo '%s'.",
                    numero_intento,
                    modelo,
                )
                response = client.models.generate_content(
                    model=modelo,
                    contents=contenidos,
                    config=config,
                )
                texto = (getattr(response, 'text', None) or '').strip()
                duracion_intento_ms = round((time.perf_counter() - inicio_intento) * 1000)
                if texto:
                    intentos.append({
                        "model": modelo,
                        "status": "success",
                        "duration_ms": duracion_intento_ms,
                    })
                    return {
                        "text": texto,
                        "provider": "gemini",
                        "model": modelo,
                        "duration_ms": round((time.perf_counter() - inicio_total) * 1000),
                        "attempts": intentos,
                    }

                intentos.append({
                    "model": modelo,
                    "status": "empty_response",
                    "duration_ms": duracion_intento_ms,
                })
                logger.warning(
                    "[GEMINI_AGENTE_SENIOR] El modelo '%s' devolvió una respuesta vacía.",
                    modelo,
                )
            except ServerError as exc:
                intentos.append({
                    "model": modelo,
                    "status": "server_error",
                    "code": getattr(exc, 'code', None),
                    "duration_ms": round((time.perf_counter() - inicio_intento) * 1000),
                })
                logger.warning(
                    "[GEMINI_AGENTE_SENIOR] Error temporal del modelo '%s' (código=%s).",
                    modelo,
                    getattr(exc, 'code', None),
                )
                time.sleep(0.4)
            except APIError as exc:
                intentos.append({
                    "model": modelo,
                    "status": "api_error",
                    "code": getattr(exc, 'code', None),
                    "duration_ms": round((time.perf_counter() - inicio_intento) * 1000),
                })
                logger.warning(
                    "[GEMINI_AGENTE_SENIOR] Error de API del modelo '%s' (código=%s).",
                    modelo,
                    getattr(exc, 'code', None),
                )
            except (TimeoutError, ConnectionError, httpx.TransportError) as exc:
                intentos.append({
                    "model": modelo,
                    "status": type(exc).__name__,
                    "duration_ms": round((time.perf_counter() - inicio_intento) * 1000),
                })
                logger.warning(
                    "[GEMINI_AGENTE_SENIOR] Fallo de conexión con el modelo '%s' (%s).",
                    modelo,
                    type(exc).__name__,
                )

        raise AsistenteServiceError(
            detail="Gemini no se encuentra disponible temporalmente.",
            status_code=status.HTTP_502_BAD_GATEWAY,
            codigo="gemini_no_disponible",
        )

    @staticmethod
    def parsear_json_respuesta(texto_respuesta: str) -> dict:
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


from .diagrama_imagen_service import DiagramaImagenService  # noqa: E402
from .instruccion_asistente_service import InstruccionAsistenteService  # noqa: E402
from .agente_senior_service import AgenteSeniorService  # noqa: E402

__all__ = [
    'AsistenteServiceError',
    'OllamaProviderService',
    'GeminiProviderService',
    'DiagramaImagenService',
    'InstruccionAsistenteService',
    'AgenteSeniorService',
]
