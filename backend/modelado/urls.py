from django.urls import path
from .views import (
    ProyectoListCreateView,
    ProyectoDetailView,
    InvitarColaboradorView,
    AceptarInvitacionView,
    DiagramaCargaInicialView,
    ProyectoColaboradoresListView,
    ColaboradorReenviarInvitacionView,
    ColaboradorEliminarView,
    InvitacionesPendientesListView,
    AceptarInvitacionDirectaView,
    RechazarInvitacionDirectaView,
)

app_name = 'modelado'

urlpatterns = [
    path('proyectos/', ProyectoListCreateView.as_view(), name='proyecto_list_create'),
    path('proyectos/<int:pk>/', ProyectoDetailView.as_view(), name='proyecto_detail'),
    path('proyectos/<int:pk>/diagrama/', DiagramaCargaInicialView.as_view(), name='diagrama_carga_inicial'),
    path('proyectos/<int:pk>/invitar/', InvitarColaboradorView.as_view(), name='invitar_colaborador'),
    path('proyectos/aceptar-invitacion/', AceptarInvitacionView.as_view(), name='aceptar_invitacion'),
    path('proyectos/<int:pk>/colaboradores/', ProyectoColaboradoresListView.as_view(), name='proyecto_colaboradores_list'),
    path('proyectos/<int:pk>/colaboradores/<int:colaborador_id>/reenviar/', ColaboradorReenviarInvitacionView.as_view(), name='colaborador_reenviar_invitacion'),
    path('proyectos/<int:pk>/colaboradores/<int:colaborador_id>/', ColaboradorEliminarView.as_view(), name='colaborador_eliminar'),
    path('invitaciones/', InvitacionesPendientesListView.as_view(), name='invitaciones_pendientes_list'),
    path('invitaciones/<int:pk>/aceptar/', AceptarInvitacionDirectaView.as_view(), name='aceptar_invitacion_directa'),
    path('invitaciones/<int:pk>/rechazar/', RechazarInvitacionDirectaView.as_view(), name='rechazar_invitacion_directa'),
]
