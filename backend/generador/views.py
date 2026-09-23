from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from modelado.models import Proyecto
from usuario.models import UserColaborador
from .serializers import ImportarXMLSerializer
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
        user = request.user
        es_propietario = (proyecto.propietario == user)
        if not es_propietario:
            es_colaborador = UserColaborador.objects.filter(
                proyecto=proyecto,
                usuario=user,
                estado=UserColaborador.Estado.ACTIVO
            ).exists()
            if not es_colaborador:
                return Response(
                    {"detail": "No tienes permisos para exportar el diagrama de este proyecto."},
                    status=status.HTTP_403_FORBIDDEN
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

        # Verificación de permisos de edición
        user = request.user
        es_propietario = (proyecto.propietario == user)
        if not es_propietario:
            colaboracion = UserColaborador.objects.filter(
                proyecto=proyecto,
                usuario=user,
                estado=UserColaborador.Estado.ACTIVO
            ).first()
            if not colaboracion or colaboracion.rol not in (UserColaborador.Rol.PROPIETARIO, UserColaborador.Rol.EDITOR):
                return Response(
                    {"detail": "No tienes permisos de edición para importar diagramas en este proyecto."},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = ImportarXMLSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contenido_xml = serializer.validated_data['contenido_xml']
        reemplazar = serializer.validated_data.get('reemplazar_existente', True)

        try:
            importer = XMIImporter(proyecto)
            resultado = importer.importar_xml(contenido_xml, reemplazar_existente=reemplazar)
        except Exception as e:
            return Response(
                {"detail": f"Error al procesar el archivo XML 2.1: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            "detail": "Diagrama XML 2.1 (Enterprise Architect) importado exitosamente.",
            "metricas": resultado
        }, status=status.HTTP_200_OK)
