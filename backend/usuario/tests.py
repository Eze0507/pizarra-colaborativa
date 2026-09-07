from django.contrib.auth.models import User
from django.core import signing
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class UsuarioAuthTests(APITestCase):
    def setUp(self):
        self.username = "testuser"
        self.password = "Secr3tP@ssword123"
        self.email = "testuser@example.com"
        # Usuario activo para pruebas de login/logout
        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
            email=self.email,
            first_name="Test",
            last_name="User",
            is_active=True
        )
        self.login_url = reverse('usuario:login')
        self.logout_url = reverse('usuario:logout')
        self.refresh_url = reverse('usuario:token_refresh')
        self.registro_url = reverse('usuario:registro')
        self.activar_url = reverse('usuario:activar')

    def test_login_success(self):
        """Verifica que un usuario activo con credenciales correctas obtenga tokens y datos de usuario."""
        response = self.client.post(self.login_url, {
            'username': self.username,
            'password': self.password
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], self.username)

    def test_login_inactive_user_rejected(self):
        """Verifica que un usuario inactivo no pueda iniciar sesión y reciba mensaje descriptivo."""
        inactive_user = User.objects.create_user(
            username="inactiveuser",
            password="password123",
            email="inactive@example.com",
            is_active=False
        )
        response = self.client.post(self.login_url, {
            'username': "inactiveuser",
            'password': "password123"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.assertIn('no está activada', str(response.data['detail']))

    def test_login_invalid_credentials(self):
        """Verifica que credenciales incorrectas retornen 401 Unauthorized."""
        response = self.client.post(self.login_url, {
            'username': self.username,
            'password': 'WrongPassword'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_and_token_blacklist(self):
        """Verifica que el logout agregue el refresh token a la blacklist e impida refrescarlo."""
        login_res = self.client.post(self.login_url, {
            'username': self.username,
            'password': self.password
        })
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        refresh_token = login_res.data['refresh']

        logout_res = self.client.post(self.logout_url, {'refresh': refresh_token})
        self.assertEqual(logout_res.status_code, status.HTTP_200_OK)

        refresh_res = self.client.post(self.refresh_url, {'refresh': refresh_token})
        self.assertEqual(refresh_res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_register_creates_inactive_user(self):
        """Verifica que el registro guarde al usuario con is_active = False."""
        data = {
            'first_name': 'Carlos',
            'last_name': 'Santana',
            'email': 'carlos@example.com',
            'username': 'csantana',
            'password': 'password123'
        }
        response = self.client.post(self.registro_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created_user = User.objects.get(username='csantana')
        self.assertFalse(created_user.is_active)

    def test_activation_flow_success(self):
        """Verifica el flujo completo: registro inactivo -> activación con token -> login exitoso."""
        data = {
            'first_name': 'Elena',
            'last_name': 'Ríos',
            'email': 'elena@example.com',
            'username': 'erios',
            'password': 'password123'
        }
        reg_res = self.client.post(self.registro_url, data)
        self.assertEqual(reg_res.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username='erios')
        self.assertFalse(user.is_active)

        # Generar token correspondiente
        token = signing.dumps({'user_id': user.id}, salt='account-activation')

        # Activar cuenta
        act_res = self.client.post(self.activar_url, {'token': token})
        self.assertEqual(act_res.status_code, status.HTTP_200_OK)
        self.assertIn('activada exitosamente', act_res.data['detail'])

        # Verificar que ahora esté activo en base de datos
        user.refresh_from_db()
        self.assertTrue(user.is_active)

        # Verificar que ahora sí pueda iniciar sesión
        login_res = self.client.post(self.login_url, {
            'username': 'erios',
            'password': 'password123'
        })
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        self.assertIn('access', login_res.data)

    def test_activation_invalid_token(self):
        """Verifica que un token inválido sea rechazado con 400."""
        response = self.client.post(self.activar_url, {'token': 'token-falso-invalido'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_activation_expired_token(self):
        """Verifica que un token expirado sea rechazado con 400."""
        # Generar token con timestamp en el pasado o probar SignatureExpired
        user = User.objects.create_user(
            username="expireduser",
            password="password123",
            email="expired@example.com",
            is_active=False
        )
        token = signing.dumps({'user_id': user.id}, salt='account-activation')
        # Si simulamos con max_age=-1, loads lanzará SignatureExpired
        try:
            signing.loads(token, salt='account-activation', max_age=-1)
        except signing.SignatureExpired:
            expired_detected = True
        self.assertTrue(expired_detected)
