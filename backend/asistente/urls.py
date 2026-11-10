from django.urls import path
from .views import (
    GenerarDiagramaDesdeImagenView,
    EjecutarInstruccionAsistenteView,
    AgenteSeniorConversacionView,
    ConsultarAyudaView,
)

app_name = 'asistente'

urlpatterns = [
    path('generar-diagrama-imagen/', GenerarDiagramaDesdeImagenView.as_view(), name='generar_diagrama_imagen'),
    path('ejecutar-instruccion/', EjecutarInstruccionAsistenteView.as_view(), name='ejecutar_instruccion'),
    path('proyectos/<int:proyecto_id>/agente-senior/', AgenteSeniorConversacionView.as_view(), name='agente_senior_conversacion'),
    path('ayuda/', ConsultarAyudaView.as_view(), name='consultar_ayuda'),
]
