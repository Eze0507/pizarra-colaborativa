from django.urls import path
from .views import (
    ProyectoListCreateView,
    ProyectoDetailView,
    InvitarColaboradorView,
    AceptarInvitacionView,
)

app_name = 'modelado'

urlpatterns = [
    path('proyectos/', ProyectoListCreateView.as_view(), name='proyecto_list_create'),
    path('proyectos/<int:pk>/', ProyectoDetailView.as_view(), name='proyecto_detail'),
    path('proyectos/<int:pk>/invitar/', InvitarColaboradorView.as_view(), name='invitar_colaborador'),
    path('proyectos/aceptar-invitacion/', AceptarInvitacionView.as_view(), name='aceptar_invitacion'),
]
