import os
import json
import time
import logging

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
    'GeminiProviderService',
    'DiagramaImagenService',
    'InstruccionAsistenteService',
    'AgenteSeniorService',
]
