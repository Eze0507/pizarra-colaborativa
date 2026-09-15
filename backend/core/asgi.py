"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Inicializar la aplicación ASGI de Django primero para asegurar que
# el registro de modelos esté cargado antes de importar código de Channels
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from modelado.middleware import JwtAuthMiddlewareStack
import modelado.routing

# Definición del enrutador de protocolos para HTTP y WebSockets
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        JwtAuthMiddlewareStack(
            URLRouter(
                modelado.routing.websocket_urlpatterns
            )
        )
    ),
})

