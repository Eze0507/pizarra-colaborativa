from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import (
    CustomTokenObtainPairSerializer,
    LogoutSerializer,
    UserRegisterSerializer,
)


class RegisterView(generics.CreateAPIView):
    """
    Endpoint de registro de nuevo usuario.
    Solicita nombre, apellido, correo, nombre de usuario y contraseña (mínimo 8 caracteres).
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "detail": "Usuario registrado exitosamente.",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        }, status=status.HTTP_201_CREATED)



class LoginView(TokenObtainPairView):
    """
    Endpoint de inicio de sesión.
    Retorna el token de acceso, token de refresco y datos del usuario.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


class LogoutView(APIView):
    """
    Endpoint para cerrar sesión.
    Recibe el token de refresco (refresh) y lo añade a la lista negra (blacklist),
    invalidándolo para futuras solicitudes de renovación.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Sesión cerrada exitosamente. Token invalidado."},
            status=status.HTTP_200_OK
        )
