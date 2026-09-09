from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Proyecto
from usuario.models import UserColaborador
from .serializers import (
    ProyectoCreateSerializer,
    ProyectoDetailSerializer,
    InvitarColaboradorSerializer,
    AceptarInvitacionSerializer,
)


class ProyectoListCreateView(generics.ListCreateAPIView):
    """
    GET: Lista todos los proyectos donde el usuario es propietario o colaborador activo.
    POST: Crea un nuevo proyecto asignando al usuario autenticado como propietario.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProyectoCreateSerializer
        return ProyectoDetailSerializer

    def get_queryset(self):
        user = self.request.user
        # Proyectos propios o donde es colaborador con estado activo
        return Proyecto.objects.filter(
            Q(propietario=user) |
            Q(colaboradores_detalle__usuario=user, colaboradores_detalle__estado=UserColaborador.Estado.ACTIVO)
        ).distinct()

    def create(self, request, *args, **kwargs):
        serializer = ProyectoCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        proyecto = serializer.save()
        # Retornar la representación detallada completa
        detail_serializer = ProyectoDetailSerializer(proyecto, context={'request': request})
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)


class ProyectoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE para un proyecto específico.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProyectoDetailSerializer

    def get_queryset(self):
        user = self.request.user
        return Proyecto.objects.filter(
            Q(propietario=user) |
            Q(colaboradores_detalle__usuario=user, colaboradores_detalle__estado=UserColaborador.Estado.ACTIVO)
        ).distinct()


class InvitarColaboradorView(APIView):
    """
    Endpoint para invitar a un colaborador al proyecto enviando un correo con enlace firmado.
    Solo el propietario del proyecto puede realizar invitaciones.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        proyecto = get_object_or_404(Proyecto, pk=pk)

        # Validar que el usuario autenticado sea el propietario
        if proyecto.propietario != request.user:
            return Response(
                {"detail": "Solo el propietario del proyecto puede invitar a nuevos colaboradores."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = InvitarColaboradorSerializer(
            data=request.data,
            context={'request': request, 'proyecto': proyecto}
        )
        serializer.is_valid(raise_exception=True)
        colaboracion = serializer.save()

        return Response({
            "detail": f"Invitación enviada exitosamente a {colaboracion.usuario.email}.",
            "colaborador": {
                "id": colaboracion.id,
                "usuario_id": colaboracion.usuario.id,
                "username": colaboracion.usuario.username,
                "email": colaboracion.usuario.email,
                "rol": colaboracion.rol,
                "estado": colaboracion.estado,
            },
            "proyecto": {
                "id": proyecto.id,
                "codigo": proyecto.codigo,
                "nombre": proyecto.nombre,
            }
        }, status=status.HTTP_200_OK)


class AceptarInvitacionView(APIView):
    """
    Endpoint para aceptar una invitación usando el token firmado recibido por correo.
    Actualiza el estado del colaborador a 'activo' con rol 'editor'.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = AceptarInvitacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        colaboracion = serializer.save()

        return Response({
            "detail": f"¡Invitación aceptada exitosamente! Ahora eres editor del proyecto '{colaboracion.proyecto.nombre}'.",
            "proyecto": {
                "id": colaboracion.proyecto.id,
                "codigo": colaboracion.proyecto.codigo,
                "nombre": colaboracion.proyecto.nombre,
            },
            "colaborador": {
                "id": colaboracion.id,
                "username": colaboracion.usuario.username,
                "rol": colaboracion.rol,
                "estado": colaboracion.estado,
            }
        }, status=status.HTTP_200_OK)
