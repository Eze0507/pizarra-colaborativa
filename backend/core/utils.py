from urllib.parse import urlparse
from django.conf import settings


def get_frontend_url(request=None):
    """
    Determina dinámicamente la URL base del frontend para enlaces en correos electrónicos.

    Prioridad de resolución:
    1. Encabezado 'Origin' de la petición HTTP (en peticiones CORS desde Angular,
       el navegador siempre envía la URL exacta donde está cargado el frontend, ej: 'http://54.20.30.40:4200').
    2. Encabezado 'Referer' de la petición HTTP (extrae esquema y netloc).
    3. Variable FRONTEND_URL en settings / variable de entorno (si fue definida explícitamente).
    4. Host de la petición actual combinada con el puerto externo del frontend (4200 por defecto).
    5. Fallback por defecto a 'http://localhost:4200'.
    """
    if request:
        origin = request.META.get('HTTP_ORIGIN')
        if origin:
            return origin.rstrip('/')

        referer = request.META.get('HTTP_REFERER')
        if referer:
            parsed = urlparse(referer)
            if parsed.scheme and parsed.netloc:
                return f"{parsed.scheme}://{parsed.netloc}".rstrip('/')

    frontend_url = getattr(settings, 'FRONTEND_URL', None)
    if frontend_url:
        return frontend_url.rstrip('/')

    if request:
        host = request.get_host().split(':')[0]
        frontend_port = getattr(settings, 'FRONTEND_PORT', '4200')
        scheme = 'https' if request.is_secure() else 'http'
        return f"{scheme}://{host}:{frontend_port}".rstrip('/')

    return 'http://localhost:4200'
