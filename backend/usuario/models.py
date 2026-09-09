from django.db import models
from django.contrib.auth.models import User


class UserColaborador(models.Model):
    class Rol(models.TextChoices):
        PROPIETARIO = 'propietario', 'Propietario'
        EDITOR = 'editor', 'Editor'
        VISUALIZADOR = 'visualizador', 'Visualizador'

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        ACTIVO = 'activo', 'Activo'

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='colaboraciones'
    )
    proyecto = models.ForeignKey(
        'modelado.Proyecto',
        on_delete=models.CASCADE,
        related_name='colaboradores_detalle'
    )
    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.EDITOR
    )
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE
    )
    fecha_ingreso = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_colaborador'
        unique_together = ('usuario', 'proyecto')
        verbose_name = 'Colaborador de Proyecto'
        verbose_name_plural = 'Colaboradores de Proyecto'

    def __str__(self):
        return f"{self.usuario.username} - {self.proyecto_id} ({self.rol} - {self.estado})"
