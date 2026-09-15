from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import (
    CustomTokenObtainPairSerializer,
    LogoutSerializer,
    UserRegisterSerializer,
    ActivateAccountSerializer,
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
            "detail": "Usuario registrado exitosamente. Se ha enviado un correo para activar su cuenta.",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        }, status=status.HTTP_201_CREATED)


class ActivateAccountView(APIView):
    """
    Endpoint para activar la cuenta de usuario mediante el token recibido por correo.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = ActivateAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Cuenta activada exitosamente. Ya puedes iniciar sesión."},
            status=status.HTTP_200_OK
        )




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


class BuscarUsuariosView(APIView):
    """
    Endpoint para buscar usuarios registrados por username o email.
    Excluye al propio usuario autenticado y requiere autenticación.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        from django.db.models import Q
        from django.contrib.auth.models import User
        from modelado.serializers import UserSimpleSerializer

        query = request.query_params.get('q', '').strip()
        if len(query) < 2:
            return Response([], status=status.HTTP_200_OK)

        usuarios = User.objects.filter(is_active=True).filter(
            Q(username__icontains=query) | Q(email__icontains=query)
        ).exclude(id=request.user.id).order_by('username')[:10]

        data = UserSimpleSerializer(usuarios, many=True).data
        return Response(data, status=status.HTTP_200_OK)
