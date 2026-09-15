"""
Enrutamiento WebSocket para la aplicación modelado.
Equivalente a urls.py pero para conexiones en tiempo real de Channels.
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/pizarra/(?P<proyecto_id>\d+)/$', consumers.PizarraConsumer.as_asgi()),
]
