"""
Middleware ASGI personalizado para autenticación de WebSockets mediante JWT.
Permite autenticar conexiones desde clientes frontend (como Angular) leyendo
el token enviado en los parámetros de consulta (?token=<jwt>).
"""
from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser, User
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def get_user_from_jwt_token(token_string: str):
    """
    Decodifica y valida el token JWT usando SimpleJWT,
    retornando el usuario autenticado o AnonymousUser si el token es inválido o expiró.
    """
    if not token_string:
        return AnonymousUser()

    try:
        access_token = AccessToken(token_string)
        user_id = access_token.get('user_id')
        if not user_id:
            return AnonymousUser()
        return User.objects.get(id=user_id, is_active=True)
    except Exception:
        return AnonymousUser()


class JwtAuthMiddleware(BaseMiddleware):
    """
    Interpola la conexión WebSocket entrante, extrae el token JWT desde
    scope['query_string'] decodificando los bytes, valida la firma y
    asigna el usuario a scope['user'].
    """
    async def __call__(self, scope, receive, send):
        # En el estándar ASGI, scope['query_string'] se recibe como bytes: b'token=...'
        query_bytes = scope.get('query_string', b'')
        if isinstance(query_bytes, (bytes, bytearray)):
            query_string = query_bytes.decode('utf-8')
        else:
            query_string = str(query_bytes)

        # Parsear el parámetro token
        query_params = parse_qs(query_string)
        token_val = query_params.get('token', [None])[0]

        # Soporte alternativo directo por split
        if not token_val and 'token=' in query_string:
            partes = query_string.split('token=')
            if len(partes) > 1:
                token_val = partes[1].split('&')[0]

        if token_val:
            scope['user'] = await get_user_from_jwt_token(token_val.strip())
        else:
            # Si no hay token provisto y no hay usuario autenticado previo
            if 'user' not in scope or not scope['user'].is_authenticated:
                scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)


def JwtAuthMiddlewareStack(inner):
    """Envoltura estándar compatible con las pilas de middleware de Django Channels."""
    return JwtAuthMiddleware(inner)
