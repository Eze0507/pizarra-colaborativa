from django.urls import path
from .views import GenerarDiagramaDesdeImagenView, EjecutarInstruccionAsistenteView

app_name = 'asistente'

urlpatterns = [
    path('generar-diagrama-imagen/', GenerarDiagramaDesdeImagenView.as_view(), name='generar_diagrama_imagen'),
    path('ejecutar-instruccion/', EjecutarInstruccionAsistenteView.as_view(), name='ejecutar_instruccion'),
]
