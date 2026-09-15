from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LoginView, LogoutView, RegisterView, ActivateAccountView, BuscarUsuariosView

app_name = 'usuario'

urlpatterns = [
    path('registro/', RegisterView.as_view(), name='registro'),
    path('activar/', ActivateAccountView.as_view(), name='activar'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('buscar/', BuscarUsuariosView.as_view(), name='buscar'),
]
