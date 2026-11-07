from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from modelado.models import Proyecto
from modelado.permissions import ProjectAction, require_project_action
from modelado.consistency import (
    InvalidExpectedRevision,
    StaleRevision,
    lock_project_for_write,
)
from modelado.realtime import notificar_evento_proyecto_sync
from django.db import transaction
from .serializers import GenerarSpringBootSerializer, ImportarXMLSerializer
from .services.spring_contract import (
    GenerationLimitError,
    GenerationValidationError,
    capture_generation_contract,
)
from .services.spring_generator import InvalidGenerationInput, generate_spring_boot_base
from .services.java_model_generator import JavaGenerationError
from .services.jpa_model_generator import JpaGenerationError
from .services.crud_generator import CrudGenerationError
from .services.xmi_exporter import XMIExporter
from .services.xmi_importer import XMIImporter


class ExportarDiagramaXMLView(APIView):
    """
    Endpoint para exportar el diagrama de clases conceptual a formato XML 2.1 (OMG UML / XMI 2.1)
    compatible con Enterprise Architect.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, proyecto_id: int, *args, **kwargs):
        proyecto = get_object_or_404(
            Proyecto.objects.prefetch_related('entidades__atributos', 'relaciones'),
            pk=proyecto_id
        )

        # Verificación de permisos de acceso al proyecto
        require_project_action(
            request.user, proyecto, ProjectAction.EXPORT,
            "No tienes permisos para exportar el diagrama de este proyecto."
        )

        exporter = XMIExporter(proyecto)
        contenido_xml = exporter.exportar_xml()

        nombre_archivo = f"{proyecto.codigo or f'proyecto_{proyecto.id}'}_diagrama_ea.xml"
        response = HttpResponse(contenido_xml, content_type='application/xml; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        return response


class ImportarDiagramaXMLView(APIView):
    """
    Endpoint para importar un archivo XML 2.1 (OMG UML / XMI 2.1) generado por Enterprise Architect
    e incorporarlo al diagrama conceptual del proyecto.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, proyecto_id: int, *args, **kwargs):
        proyecto = get_object_or_404(Proyecto, pk=proyecto_id)

        require_project_action(
            request.user, proyecto, ProjectAction.IMPORT,
            "No tienes permisos de edición para importar diagramas en este proyecto."
        )

        serializer = ImportarXMLSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contenido_xml = serializer.validated_data['contenido_xml']
        reemplazar = serializer.validated_data.get('reemplazar_existente', True)

        try:
            with transaction.atomic():
                proyecto = lock_project_for_write(
                    proyecto_id, serializer.validated_data["expected_revision"]
                )
                require_project_action(
                    request.user, proyecto, ProjectAction.IMPORT,
                    "No tienes permisos de edición para importar diagramas en este proyecto."
                )
                importer = XMIImporter(proyecto)
                resultado = importer.importar_xml(contenido_xml, reemplazar_existente=reemplazar)
                proyecto.refresh_from_db(fields=["revision"])
                proyecto.revision += 1
                proyecto.save(update_fields=["revision", "fecha_actualizacion"])
                revision = proyecto.revision
                transaction.on_commit(lambda: notificar_evento_proyecto_sync(
                    proyecto.id, "diagram.updated",
                    {"proyecto_id": proyecto.id, "revision": revision, "usuario_id": request.user.id},
                ))
        except StaleRevision as e:
            return Response(
                {"code": e.code, "message": str(e), "current_revision": e.current_revision},
                status=status.HTTP_409_CONFLICT,
            )
        except Exception as e:
            return Response(
                {"detail": f"Error al procesar el archivo XML 2.1: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            "detail": "Diagrama XML 2.1 (Enterprise Architect) importado exitosamente.",
            "metricas": resultado,
            "revision": revision,
        }, status=status.HTTP_200_OK)


class GenerarSpringBootView(APIView):
    """Genera el proyecto Maven base desde una captura UML confirmada."""

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request, proyecto_id: int, *args, **kwargs):
        # Esta comprobación temprana evita revelar el contrato de entrada a un
        # usuario que no puede exportar. La autorización se repite bajo el
        # bloqueo usado para crear la captura.
        proyecto = get_object_or_404(Proyecto, pk=proyecto_id)
        require_project_action(
            request.user,
            proyecto,
            ProjectAction.EXPORT,
            "No tienes permisos para generar código desde este proyecto.",
        )

        serializer = GenerarSpringBootSerializer(data=request.data)
        if not serializer.is_valid():
            invalid_options = "CRUD_INVALID_OPTION_COMBINATION" in str(serializer.errors)
            return Response(
                {
                    "code": (
                        "CRUD_INVALID_OPTION_COMBINATION"
                        if invalid_options
                        else "invalid_generation_request"
                    ),
                    "message": (
                        "Las opciones de generación no respetan sus dependencias."
                        if invalid_options
                        else "La solicitud de generación contiene datos inválidos."
                    ),
                    "details": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        try:
            capture = capture_generation_contract(
                project_id=proyecto_id,
                expected_revision=data["expected_revision"],
                user=request.user,
                model_enabled=data["opciones"]["modelo"],
                crud_enabled=any(
                    data["opciones"][name]
                    for name in ("repositorio", "servicio", "controlador")
                ),
            )
            generated = generate_spring_boot_base(
                capture,
                project_name=data["nombre_proyecto"],
                base_package=data["paquete_base"],
                options=data["opciones"],
            )
        except InvalidExpectedRevision as exc:
            return Response(
                {"code": exc.code, "message": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except StaleRevision as exc:
            return Response(
                {
                    "code": exc.code,
                    "message": "El diagrama cambió.",
                    "current_revision": exc.current_revision,
                },
                status=status.HTTP_409_CONFLICT,
            )
        except GenerationValidationError as exc:
            return Response(
                {"code": exc.code, "message": str(exc), "details": exc.details},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except (
            GenerationLimitError,
            InvalidGenerationInput,
            JavaGenerationError,
            JpaGenerationError,
            CrudGenerationError,
        ) as exc:
            return Response(
                {
                    "code": exc.code,
                    "message": str(exc),
                    "details": exc.details,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        response = HttpResponse(generated.content, content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="{generated.filename}"'
        response["Cache-Control"] = "no-store"
        response["Content-Length"] = str(len(generated.content))
        return response
