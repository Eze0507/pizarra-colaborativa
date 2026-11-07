from django.urls import path
from .views import ExportarDiagramaXMLView, GenerarSpringBootView, ImportarDiagramaXMLView

app_name = 'generador'

urlpatterns = [
    path('proyectos/<int:proyecto_id>/exportar-xml/', ExportarDiagramaXMLView.as_view(), name='exportar_xml'),
    path('proyectos/<int:proyecto_id>/importar-xml/', ImportarDiagramaXMLView.as_view(), name='importar_xml'),
    path(
        'proyectos/<int:proyecto_id>/spring-boot/',
        GenerarSpringBootView.as_view(),
        name='generar_spring_boot',
    ),
]
