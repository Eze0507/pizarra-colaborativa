from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Proyecto, Entidad
from usuario.models import UserColaborador
from .serializers import (
    ProyectoCreateSerializer,
    ProyectoDetailSerializer,
    InvitarColaboradorSerializer,
    AceptarInvitacionSerializer,
    EntidadDiagramaSerializer,
    RelacionDiagramaSerializer,
    ColaboradorDetalleSerializer,
    InvitacionPendienteSerializer,
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

    def perform_destroy(self, instance):
        if instance.propietario != self.request.user:
            raise PermissionDenied("Solo el propietario puede eliminar este proyecto.")
        instance.delete()


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


class DiagramaCargaInicialView(APIView):
    """
    Endpoint para la carga inicial de la pizarra virtual (diseñado para JointJS y Yjs).
    Retorna:
    - proyecto: Metadatos del proyecto y snapshot de estado del lienzo (datos_diagrama).
    - entidades: Listado de entidades activas con atributos ordenados (sin 'alto', computado en cliente).
    - relaciones: Listado de relaciones conceptuales con cardinalidades de origen y destino.
    - permisos: Identificación de si el usuario es propietario o qué rol posee.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        # 1. Obtener proyecto con prefetch optimizado para evitar consultas N+1
        proyecto = get_object_or_404(
            Proyecto.objects.prefetch_related('entidades__atributos', 'relaciones'),
            pk=pk
        )

        user = request.user
        es_propietario = (proyecto.propietario == user)
        rol_usuario = 'propietario' if es_propietario else None

        # 2. Verificar permisos de acceso
        if not es_propietario:
            colaboracion = UserColaborador.objects.filter(
                proyecto=proyecto,
                usuario=user,
                estado=UserColaborador.Estado.ACTIVO
            ).first()

            if not colaboracion:
                return Response(
                    {"detail": "No tienes permiso para acceder al diagrama de este proyecto."},
                    status=status.HTTP_403_FORBIDDEN
                )
            rol_usuario = colaboracion.rol

        # 3. Filtrar entidades activas (excluyendo papelera)
        entidades_qs = proyecto.entidades.exclude(estado=Entidad.Estado.PAPELERA).order_by('id')
        entidades_data = EntidadDiagramaSerializer(entidades_qs, many=True).data

        # 4. Filtrar relaciones entre entidades existentes
        relaciones_qs = proyecto.relaciones.filter(
            entidad_origen__in=entidades_qs,
            entidad_destino__in=entidades_qs
        ).order_by('id')
        relaciones_data = RelacionDiagramaSerializer(relaciones_qs, many=True).data

        # 5. Armar respuesta estructurada compatible con JointJS y Yjs
        return Response({
            "proyecto": {
                "id": proyecto.id,
                "codigo": proyecto.codigo,
                "nombre": proyecto.nombre,
                "descripcion": proyecto.descripcion,
                "paquete_base": proyecto.paquete_base,
                "datos_diagrama": proyecto.datos_diagrama or {},
                "propietario": {
                    "id": proyecto.propietario.id,
                    "username": proyecto.propietario.username,
                    "email": proyecto.propietario.email,
                },
                "es_propietario": es_propietario,
                "rol_usuario": rol_usuario,
                "fecha_actualizacion": proyecto.fecha_actualizacion,
            },
            "entidades": entidades_data,
            "relaciones": relaciones_data,
        }, status=status.HTTP_200_OK)


class ProyectoColaboradoresListView(APIView):
    """
    Endpoint para obtener la lista de colaboradores asociados a un proyecto.
    Accesible para el propietario o colaboradores activos.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        proyecto = get_object_or_404(Proyecto, pk=pk)

        # Validar permisos: Propietario o colaborador activo
        es_propietario = (proyecto.propietario == request.user)
        if not es_propietario:
            tiene_acceso = UserColaborador.objects.filter(
                proyecto=proyecto,
                usuario=request.user,
                estado=UserColaborador.Estado.ACTIVO
            ).exists()
            if not tiene_acceso:
                return Response(
                    {"detail": "No tienes permiso para consultar los colaboradores de este proyecto."},
                    status=status.HTTP_403_FORBIDDEN
                )

        colaboradores = proyecto.colaboradores_detalle.all().select_related('usuario').order_by('fecha_ingreso')
        data = ColaboradorDetalleSerializer(colaboradores, many=True).data
        return Response(data, status=status.HTTP_200_OK)


class ColaboradorReenviarInvitacionView(APIView):
    """
    Endpoint para reenviar el correo de invitación a un colaborador en estado pendiente.
    Solo el propietario del proyecto puede ejecutar esta acción.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, colaborador_id, *args, **kwargs):
        from django.conf import settings
        from django.core import signing
        from django.core.mail import send_mail
        from core.utils import get_frontend_url

        proyecto = get_object_or_404(Proyecto, pk=pk)

        if proyecto.propietario != request.user:
            return Response(
                {"detail": "Solo el propietario del proyecto puede reenviar invitaciones."},
                status=status.HTTP_403_FORBIDDEN
            )

        colaboracion = get_object_or_404(UserColaborador, pk=colaborador_id, proyecto=proyecto)

        if colaboracion.estado != UserColaborador.Estado.PENDIENTE:
            return Response(
                {"detail": f"El colaborador '{colaboracion.usuario.username}' ya está activo en el proyecto."},
                status=status.HTTP_400_BAD_REQUEST
            )

        target_user = colaboracion.usuario
        token = signing.dumps({
            'colaborador_id': colaboracion.id,
            'proyecto_id': proyecto.id,
            'usuario_id': target_user.id
        }, salt='project-invitation')

        base_url = get_frontend_url(request)
        invitation_url = f"{base_url}/invitacion/{token}"

        subject = f"Invitación para colaborar en el proyecto {proyecto.nombre}"
        nombre_destinatario = target_user.first_name or target_user.username
        message = (
            f"Hola {nombre_destinatario},\n\n"
            f"{proyecto.propietario.username} te ha reenviado la invitación para colaborar como editor en el proyecto "
            f"\"{proyecto.nombre}\" ({proyecto.codigo}) dentro de la Herramienta CASE de Diseño de Datos.\n\n"
            f"Para aceptar la invitación y comenzar a diseñar en conjunto, haz clic en el siguiente enlace:\n"
            f"{invitation_url}\n\n"
            f"Este enlace expirará en 48 horas."
        )

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[target_user.email],
                fail_silently=False
            )
        except Exception as e:
            print(f"[EMAIL_REINVITE_LOG] Error reenviando correo a {target_user.email}: {e}")
            print(f"[INVITATION_LINK] {invitation_url}")

        return Response({
            "detail": f"Invitación reenviada exitosamente a {target_user.email}."
        }, status=status.HTTP_200_OK)


class ColaboradorEliminarView(APIView):
    """
    Endpoint para eliminar a un colaborador del proyecto (o cancelar invitación pendiente).
    Solo el propietario puede eliminar colaboradores, y no puede eliminarse a sí mismo.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk, colaborador_id, *args, **kwargs):
        proyecto = get_object_or_404(Proyecto, pk=pk)

        if proyecto.propietario != request.user:
            return Response(
                {"detail": "Solo el propietario del proyecto puede eliminar colaboradores."},
                status=status.HTTP_403_FORBIDDEN
            )

        colaboracion = get_object_or_404(UserColaborador, pk=colaborador_id, proyecto=proyecto)

        if colaboracion.rol == UserColaborador.Rol.PROPIETARIO or colaboracion.usuario == proyecto.propietario:
            return Response(
                {"detail": "No se puede eliminar al propietario del proyecto."},
                status=status.HTTP_400_BAD_REQUEST
            )

        username = colaboracion.usuario.username
        colaboracion.delete()

        return Response({
            "detail": f"Colaborador '{username}' eliminado exitosamente del proyecto."
        }, status=status.HTTP_200_OK)


class InvitacionesPendientesListView(generics.ListAPIView):
    """
    Endpoint para listar las invitaciones pendientes recibidas por el usuario autenticado.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InvitacionPendienteSerializer

    def get_queryset(self):
        return UserColaborador.objects.filter(
            usuario=self.request.user,
            estado=UserColaborador.Estado.PENDIENTE
        ).select_related('proyecto', 'proyecto__propietario').order_by('-fecha_ingreso')


class AceptarInvitacionDirectaView(APIView):
    """
    Endpoint para aceptar una invitación directamente desde la plataforma (sin usar token de correo).
    Actualiza el estado a 'activo' con rol 'editor'.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        colaboracion = get_object_or_404(
            UserColaborador.objects.select_related('proyecto', 'usuario'),
            pk=pk,
            usuario=request.user
        )

        if colaboracion.estado == UserColaborador.Estado.ACTIVO:
            return Response(
                {"detail": f"Ya eres colaborador activo del proyecto '{colaboracion.proyecto.nombre}'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        colaboracion.estado = UserColaborador.Estado.ACTIVO
        colaboracion.rol = UserColaborador.Rol.EDITOR
        colaboracion.save()

        return Response({
            "detail": f"¡Invitación aceptada! Ahora eres editor del proyecto '{colaboracion.proyecto.nombre}'.",
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


class RechazarInvitacionDirectaView(APIView):
    """
    Endpoint para rechazar una invitación pendiente recibida.
    Elimina el registro de UserColaborador.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        colaboracion = get_object_or_404(
            UserColaborador.objects.select_related('proyecto'),
            pk=pk,
            usuario=request.user
        )

        if colaboracion.estado != UserColaborador.Estado.PENDIENTE:
            return Response(
                {"detail": "Solo se pueden rechazar invitaciones en estado pendiente."},
                status=status.HTTP_400_BAD_REQUEST
            )

        nombre_proyecto = colaboracion.proyecto.nombre
        colaboracion.delete()

        return Response({
            "detail": f"Has rechazado la invitación al proyecto '{nombre_proyecto}'."
        }, status=status.HTTP_200_OK)

