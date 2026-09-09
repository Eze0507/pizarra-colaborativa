from django.contrib.auth.models import User
from django.core import signing
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Proyecto
from usuario.models import UserColaborador


class ProyectoTests(APITestCase):
    def setUp(self):
        # Usuario propietario
        self.user_owner = User.objects.create_user(
            username="owner_user",
            password="password123",
            email="owner@example.com",
            first_name="Owner",
            last_name="Test",
            is_active=True
        )

        # Usuario colaborador invitado
        self.user_collaborator = User.objects.create_user(
            username="collab_user",
            password="password123",
            email="collab@example.com",
            first_name="Collab",
            last_name="Test",
            is_active=True
        )

        # Usuario tercero sin acceso
        self.user_third = User.objects.create_user(
            username="third_user",
            password="password123",
            email="third@example.com",
            first_name="Third",
            last_name="Test",
            is_active=True
        )

        self.proyectos_url = reverse('modelado:proyecto_list_create')
        self.aceptar_invitacion_url = reverse('modelado:aceptar_invitacion')

    def test_crear_proyecto_autogenera_codigo_y_paquete(self):
        """Verifica que al enviar nombre y descripción se autogeneren el código y paquete_base."""
        self.client.force_authenticate(user=self.user_owner)

        data = {
            "nombre": "Sistema de Ventas",
            "descripcion": "Modelado de datos para ventas e inventario"
        }
        response = self.client.post(self.proyectos_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['codigo'], "PROJ-001")
        self.assertEqual(response.data['nombre'], "Sistema de Ventas")
        self.assertEqual(response.data['descripcion'], "Modelado de datos para ventas e inventario")
        self.assertEqual(response.data['paquete_base'], "com.example.sistemadeventas")
        self.assertEqual(response.data['propietario']['id'], self.user_owner.id)

    def test_crear_proyecto_registra_propietario_en_user_colaborador(self):
        """Verifica que el creador quede registrado como propietario activo en UserColaborador."""
        self.client.force_authenticate(user=self.user_owner)

        data = {"nombre": "Proyecto Alfa", "descripcion": "Alfa desc"}
        response = self.client.post(self.proyectos_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        proyecto_id = response.data['id']
        colaboracion = UserColaborador.objects.filter(
            proyecto_id=proyecto_id,
            usuario=self.user_owner
        ).first()

        self.assertIsNotNone(colaboracion)
        self.assertEqual(colaboracion.rol, UserColaborador.Rol.PROPIETARIO)
        self.assertEqual(colaboracion.estado, UserColaborador.Estado.ACTIVO)

    def test_crear_multiples_proyectos_incrementa_codigo(self):
        """Verifica que el código se autoincremente secuencialmente (PROJ-001, PROJ-002...)."""
        self.client.force_authenticate(user=self.user_owner)

        res1 = self.client.post(self.proyectos_url, {"nombre": "Proyecto 1"})
        res2 = self.client.post(self.proyectos_url, {"nombre": "Proyecto 2"})

        self.assertEqual(res1.data['codigo'], "PROJ-001")
        self.assertEqual(res2.data['codigo'], "PROJ-002")

    def test_listar_proyectos_filtra_por_acceso(self):
        """Verifica que el listado solo muestre proyectos propios o donde es colaborador activo."""
        self.client.force_authenticate(user=self.user_owner)
        res_crear = self.client.post(self.proyectos_url, {"nombre": "Privado Owner"})
        proyecto_id = res_crear.data['id']

        # El propietario ve su proyecto
        res_owner = self.client.get(self.proyectos_url)
        self.assertEqual(len(res_owner.data), 1)

        # El usuario tercero NO ve el proyecto
        self.client.force_authenticate(user=self.user_third)
        res_third = self.client.get(self.proyectos_url)
        self.assertEqual(len(res_third.data), 0)

    def test_invitar_colaborador_exito(self):
        """Verifica que el propietario pueda invitar a un usuario por email o username."""
        self.client.force_authenticate(user=self.user_owner)

        res_crear = self.client.post(self.proyectos_url, {"nombre": "Proyecto Beta"})
        proyecto_id = res_crear.data['id']

        invitar_url = reverse('modelado:invitar_colaborador', kwargs={'pk': proyecto_id})

        # Invitar por email
        data = {"email": self.user_collaborator.email}
        response = self.client.post(invitar_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Invitación enviada exitosamente", response.data['detail'])
        self.assertEqual(response.data['colaborador']['rol'], UserColaborador.Rol.EDITOR)
        self.assertEqual(response.data['colaborador']['estado'], UserColaborador.Estado.PENDIENTE)

        # Verificar en base de datos
        colaboracion = UserColaborador.objects.get(
            proyecto_id=proyecto_id,
            usuario=self.user_collaborator
        )
        self.assertEqual(colaboracion.estado, UserColaborador.Estado.PENDIENTE)
        self.assertEqual(colaboracion.rol, UserColaborador.Rol.EDITOR)

    def test_solo_propietario_puede_invitar(self):
        """Verifica que un usuario que no es propietario reciba 403 Forbidden al intentar invitar."""
        self.client.force_authenticate(user=self.user_owner)
        res_crear = self.client.post(self.proyectos_url, {"nombre": "Proyecto Gamma"})
        proyecto_id = res_crear.data['id']

        # Intentar invitar siendo usuario tercero
        self.client.force_authenticate(user=self.user_third)
        invitar_url = reverse('modelado:invitar_colaborador', kwargs={'pk': proyecto_id})
        response = self.client.post(invitar_url, {"email": self.user_collaborator.email})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_puede_invitar_colaborador_ya_activo(self):
        """Verifica que no se pueda enviar invitación si el colaborador ya está activo."""
        self.client.force_authenticate(user=self.user_owner)
        res_crear = self.client.post(self.proyectos_url, {"nombre": "Proyecto Delta"})
        proyecto = Proyecto.objects.get(id=res_crear.data['id'])

        # Marcar colaborador directamente como activo
        UserColaborador.objects.create(
            usuario=self.user_collaborator,
            proyecto=proyecto,
            rol=UserColaborador.Rol.EDITOR,
            estado=UserColaborador.Estado.ACTIVO
        )

        invitar_url = reverse('modelado:invitar_colaborador', kwargs={'pk': proyecto.id})
        response = self.client.post(invitar_url, {"username": self.user_collaborator.username})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ya es colaborador activo", str(response.data))

    def test_aceptar_invitacion_exito(self):
        """Verifica que un colaborador pueda aceptar la invitación con el token firmado y quedar activo."""
        self.client.force_authenticate(user=self.user_owner)
        res_crear = self.client.post(self.proyectos_url, {"nombre": "Proyecto Epsilon"})
        proyecto_id = res_crear.data['id']

        # Invitar al colaborador
        invitar_url = reverse('modelado:invitar_colaborador', kwargs={'pk': proyecto_id})
        self.client.post(invitar_url, {"email": self.user_collaborator.email})

        colaboracion = UserColaborador.objects.get(
            proyecto_id=proyecto_id,
            usuario=self.user_collaborator
        )
        self.assertEqual(colaboracion.estado, UserColaborador.Estado.PENDIENTE)

        # Generar token firmado
        token = signing.dumps({
            'colaborador_id': colaboracion.id,
            'proyecto_id': proyecto_id,
            'usuario_id': self.user_collaborator.id
        }, salt='project-invitation')

        # Aceptar invitación
        response = self.client.post(self.aceptar_invitacion_url, {"token": token})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("aceptada exitosamente", response.data['detail'])

        # Verificar que pasó a estado activo
        colaboracion.refresh_from_db()
        self.assertEqual(colaboracion.estado, UserColaborador.Estado.ACTIVO)
        self.assertEqual(colaboracion.rol, UserColaborador.Rol.EDITOR)

        # Verificar que ahora el colaborador sí ve el proyecto en su lista
        self.client.force_authenticate(user=self.user_collaborator)
        res_list = self.client.get(self.proyectos_url)
        self.assertEqual(len(res_list.data), 1)
        self.assertEqual(res_list.data[0]['id'], proyecto_id)

    def test_aceptar_invitacion_token_invalido(self):
        """Verifica que un token inválido retorne 400 Bad Request."""
        response = self.client.post(self.aceptar_invitacion_url, {"token": "token-falso"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
