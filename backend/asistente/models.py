from django.db import models
from django.contrib.auth.models import User


class Conversacion(models.Model):
    """
    Representa la conversación compartida con el Agente Senior Colaborativo
    dentro de un proyecto. Relación 0..1 a 1 con Proyecto.
    """
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha en la que se creó la conversación o se envió la primera consulta."
    )
    proyecto = models.OneToOneField(
        'modelado.Proyecto',
        on_delete=models.CASCADE,
        related_name='conversacion',
        help_text="Proyecto al que pertenece la conversación (un proyecto tiene 0 o 1 conversación)."
    )

    class Meta:
        db_table = 'conversacion'
        verbose_name = 'Conversación'
        verbose_name_plural = 'Conversaciones'

    def __str__(self):
        return f"Conversación de {self.proyecto.codigo} ({self.proyecto.nombre})"


class Mensaje(models.Model):
    """
    Representa cada mensaje dentro de la conversación del proyecto:
    tanto las consultas realizadas por los usuarios ('USER') como las
    respuestas generadas por el Agente Senior ('AGENT').
    """
    class Estado(models.TextChoices):
        RESPONDIDO = 'respondido', 'Respondido'
        PROCESANDO = 'procesando', 'Procesando'
        EN_COLA = 'en_cola', 'En cola'
        ERROR = 'error', 'Error'

    class Rol(models.TextChoices):
        USER = 'USER', 'Usuario'
        AGENT = 'AGENT', 'Agente Senior'

    fecha_envio = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha en la que se registró el mensaje en la base de datos."
    )
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PROCESANDO,
        help_text="Estado del mensaje (respondido, procesando, en_cola, error)."
    )
    rol = models.CharField(
        max_length=10,
        choices=Rol.choices,
        default=Rol.USER,
        help_text="Rol del autor del mensaje ('USER' para consultas de usuarios, 'AGENT' para respuestas del agente)."
    )
    contenido = models.TextField(
        help_text="Contenido del mensaje, consulta del usuario o respuesta del agente."
    )
    pregunta = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='respuestas',
        db_column='pregunta_id',
        help_text="Relación recursiva: vincula la respuesta del agente con la pregunta del usuario que la generó."
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mensajes_agente_senior',
        help_text="Usuario que realizó la consulta (nulo cuando el mensaje es una respuesta del agente)."
    )
    conversacion = models.ForeignKey(
        Conversacion,
        on_delete=models.CASCADE,
        related_name='mensajes',
        help_text="Conversación a la que pertenece el mensaje."
    )

    class Meta:
        db_table = 'mensaje'
        ordering = ['fecha_envio', 'id']
        verbose_name = 'Mensaje'
        verbose_name_plural = 'Mensajes'

    def __str__(self):
        autor = self.usuario.username if self.usuario else self.rol
        return f"[{self.rol} - {self.estado}] {autor}: {self.contenido[:40]}"
