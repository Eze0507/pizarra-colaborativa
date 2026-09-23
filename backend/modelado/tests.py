from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from modelado.models import Proyecto, Entidad
from usuario.models import UserColaborador

User = get_user_model()


class ProyectoDeleteTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner_user',
            email='owner@example.com',
            password='Password123!'
        )
        self.collaborator = User.objects.create_user(
            username='collab_user',
            email='collab@example.com',
            password='Password123!'
        )
        self.proyecto = Proyecto.objects.create(
            propietario=self.owner,
            nombre='Proyecto para Eliminar',
            descripcion='Descripción de prueba'
        )
        # Asignar colaborador activo
        UserColaborador.objects.create(
            proyecto=self.proyecto,
            usuario=self.collaborator,
            rol=UserColaborador.Rol.EDITOR,
            estado=UserColaborador.Estado.ACTIVO
        )
        # Crear entidad dentro del proyecto
        self.entidad = Entidad.objects.create(
            proyecto=self.proyecto,
            nombre='Usuario'
        )

    def test_owner_can_delete_project(self):
        """El propietario puede eliminar su proyecto satisfactoriamente."""
        self.client.force_authenticate(user=self.owner)
        url = f'/api/modelado/proyectos/{self.proyecto.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Proyecto.objects.filter(id=self.proyecto.id).exists())
        # Verificar eliminación en cascada de la entidad
        self.assertFalse(Entidad.objects.filter(id=self.entidad.id).exists())

    def test_collaborator_cannot_delete_project(self):
        """Un colaborador no puede eliminar el proyecto (recibe 403 Forbidden)."""
        self.client.force_authenticate(user=self.collaborator)
        url = f'/api/modelado/proyectos/{self.proyecto.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Proyecto.objects.filter(id=self.proyecto.id).exists())

    def test_serializer_includes_es_propietario(self):
        """El serializer incluye el campo booleano es_propietario según el usuario autenticado."""
        # Para el propietario
        self.client.force_authenticate(user=self.owner)
        res_owner = self.client.get(f'/api/modelado/proyectos/{self.proyecto.id}/')
        self.assertEqual(res_owner.status_code, status.HTTP_200_OK)
        self.assertTrue(res_owner.data['es_propietario'])

        # Para el colaborador
        self.client.force_authenticate(user=self.collaborator)
        res_collab = self.client.get(f'/api/modelado/proyectos/{self.proyecto.id}/')
        self.assertEqual(res_collab.status_code, status.HTTP_200_OK)
        self.assertFalse(res_collab.data['es_propietario'])
