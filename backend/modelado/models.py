import re
from django.db import models
from django.contrib.auth.models import User


class Proyecto(models.Model):
    codigo = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text="Código identificador correlativo único (ej. PROJ-001)."
    )
    nombre = models.CharField(
        max_length=150,
        help_text="Nombre del proyecto de modelado."
    )
    descripcion = models.TextField(
        blank=True,
        default='',
        help_text="Descripción o propósito del proyecto."
    )
    paquete_base = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text="Paquete base para la generación de código (ej. com.example.proyecto)."
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    propietario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='proyectos_propios',
        help_text="Usuario creador y dueño del proyecto."
    )
    colaboradores = models.ManyToManyField(
        User,
        through='usuario.UserColaborador',
        related_name='proyectos_colaborando',
        blank=True,
        help_text="Colaboradores asignados al proyecto."
    )

    class Meta:
        db_table = 'proyecto'
        ordering = ['-fecha_creacion']
        verbose_name = 'Proyecto'
        verbose_name_plural = 'Proyectos'

    def save(self, *args, **kwargs):
        # 1. Generación automática del código correlativo PROJ-001, PROJ-002, etc.
        if not self.codigo:
            ultimo = Proyecto.objects.order_by('-id').first()
            if ultimo and ultimo.codigo and ultimo.codigo.startswith("PROJ-"):
                try:
                    num_parte = int(ultimo.codigo.replace("PROJ-", ""))
                    siguiente_num = num_parte + 1
                except ValueError:
                    siguiente_num = Proyecto.objects.count() + 1
            else:
                siguiente_num = 1

            candidato = f"PROJ-{siguiente_num:03d}"
            while Proyecto.objects.filter(codigo=candidato).exists():
                siguiente_num += 1
                candidato = f"PROJ-{siguiente_num:03d}"
            self.codigo = candidato

        # 2. Generación automática del paquete base si no fue provisto
        if not self.paquete_base:
            slug = re.sub(r'[^a-zA-Z0-9]+', '', self.nombre.lower()) or 'proyecto'
            self.paquete_base = f"com.example.{slug}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
