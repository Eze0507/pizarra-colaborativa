from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Proyecto, Entidad
from usuario.models import UserColaborador
from .permissions import (
    ProjectAction,
    accessible_projects,
    get_project_role,
    require_project_action,
)
from .realtime import notificar_evento_proyecto_sync, notificar_revocacion_acceso_sync
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
from .validation import PROFILES, UMLValidator
from .consistency import (
    InvalidExpectedRevision,
    StaleRevision,
    lock_project_for_write,
    read_authoritative_state,
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
        return accessible_projects(self.request.user)

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

    def get_object(self):
        proyecto = get_object_or_404(Proyecto, pk=self.kwargs['pk'])
        action = {
            'GET': ProjectAction.READ,
            'HEAD': ProjectAction.READ,
            'OPTIONS': ProjectAction.READ,
            'PUT': ProjectAction.WRITE,
            'PATCH': ProjectAction.WRITE,
            'DELETE': ProjectAction.DELETE,
        }.get(self.request.method, ProjectAction.READ)
        require_project_action(self.request.user, proyecto, action)
        return proyecto

    def perform_destroy(self, instance):
        require_project_action(
            self.request.user,
            instance,
            ProjectAction.DELETE,
            "Solo el propietario puede eliminar este proyecto.",
        )
        instance.delete()

    def update(self, request, *args, **kwargs):
        current = self.get_object()
        if "datos_diagrama" in request.data:
            return Response(
                {"code": "snapshot_write_forbidden", "message": "Use el escritor autoritativo del diagrama."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        expected = request.data.get("expected_revision")
        payload = request.data.copy()
        payload.pop("expected_revision", None)
        if not payload:
            return Response(
                {"code": "empty_write", "message": "No se proporcionaron campos modificables."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            with transaction.atomic():
                project = lock_project_for_write(current.id, expected)
                require_project_action(request.user, project, ProjectAction.WRITE)
                serializer = self.get_serializer(
                    project, data=payload, partial=kwargs.get("partial", False)
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
                project.revision += 1
                project.save(update_fields=["revision", "fecha_actualizacion"])
                transaction.on_commit(lambda: notificar_evento_proyecto_sync(
                    project.id, "diagram.updated",
                    {"proyecto_id": project.id, "revision": project.revision, "usuario_id": request.user.id},
                ))
                data = self.get_serializer(project).data
        except InvalidExpectedRevision as exc:
            return Response(
                {"code": exc.code, "message": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except StaleRevision as exc:
            return Response(
                {"code": exc.code, "message": str(exc), "current_revision": exc.current_revision},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(data)


class InvitarColaboradorView(APIView):
    """
    Endpoint para invitar a un colaborador al proyecto enviando un correo con enlace firmado.
    Solo el propietario del proyecto puede realizar invitaciones.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        proyecto = get_object_or_404(Proyecto, pk=pk)

        require_project_action(
            request.user, proyecto, ProjectAction.MANAGE,
            "Solo el propietario del proyecto puede invitar a nuevos colaboradores."
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
        proyecto = get_object_or_404(Proyecto, pk=pk)

        user = request.user
        require_project_action(
            user, proyecto, ProjectAction.READ,
            "No tienes permiso para acceder al diagrama de este proyecto."
        )
        rol_usuario = get_project_role(user, proyecto)
        es_propietario = rol_usuario == UserColaborador.Rol.PROPIETARIO

        state = read_authoritative_state(pk)
        proyecto = state.project

        # 5. Armar respuesta estructurada compatible con JointJS y Yjs
        return Response({
            "proyecto": {
                "id": proyecto.id,
                "codigo": proyecto.codigo,
                "nombre": proyecto.nombre,
                "descripcion": proyecto.descripcion,
                "paquete_base": proyecto.paquete_base,
                "datos_diagrama": state.visual_snapshot,
                "revision": state.revision,
                "propietario": {
                    "id": proyecto.propietario.id,
                    "username": proyecto.propietario.username,
                    "email": proyecto.propietario.email,
                },
                "es_propietario": es_propietario,
                "rol_usuario": rol_usuario,
                "fecha_actualizacion": proyecto.fecha_actualizacion,
            },
            "entidades": state.entities,
            "relaciones": state.relations,
        }, status=status.HTTP_200_OK)


class ProyectoValidacionView(APIView):
    """Valida en modo lectura el modelo ORM guardado de un proyecto."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        proyecto = get_object_or_404(Proyecto, pk=pk)
        require_project_action(
            request.user, proyecto, ProjectAction.READ,
            "No tienes permiso para validar este proyecto.",
        )
        perfil = request.query_params.get("perfil", "uml").lower()
        if perfil not in PROFILES:
            return Response(
                {"detail": "Perfil inválido. Use uml, java o jpa."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        state = read_authoritative_state(pk)
        result = UMLValidator(state.model, perfil).validate()
        result["revision"] = state.revision
        return Response(result, status=status.HTTP_200_OK)


class ProyectoColaboradoresListView(APIView):
    """
    Endpoint para obtener la lista de colaboradores asociados a un proyecto.
    Accesible para el propietario o colaboradores activos.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        proyecto = get_object_or_404(Proyecto, pk=pk)

        require_project_action(
            request.user, proyecto, ProjectAction.READ,
            "No tienes permiso para consultar los colaboradores de este proyecto."
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

        require_project_action(
            request.user, proyecto, ProjectAction.MANAGE,
            "Solo el propietario del proyecto puede reenviar invitaciones."
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

        require_project_action(
            request.user, proyecto, ProjectAction.MANAGE,
            "Solo el propietario del proyecto puede eliminar colaboradores."
        )

        colaboracion = get_object_or_404(UserColaborador, pk=colaborador_id, proyecto=proyecto)

        if colaboracion.rol == UserColaborador.Rol.PROPIETARIO or colaboracion.usuario == proyecto.propietario:
            return Response(
                {"detail": "No se puede eliminar al propietario del proyecto."},
                status=status.HTTP_400_BAD_REQUEST
            )

        username = colaboracion.usuario.username
        usuario_id = colaboracion.usuario_id
        with transaction.atomic():
            colaboracion.delete()
            transaction.on_commit(
                lambda: notificar_revocacion_acceso_sync(proyecto.id, usuario_id)
            )

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

