from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Conversacion, Mensaje


class UsuarioMensajeSerializer(serializers.ModelSerializer):
    """
    Serializer resumido del usuario que envió la consulta al Agente Senior.
    """
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'nombre_completo')

    def get_nombre_completo(self, obj: User) -> str:
        full_name = f"{obj.first_name or ''} {obj.last_name or ''}".strip()
        return full_name or obj.username


class MensajeSerializer(serializers.ModelSerializer):
    """
    Serializer para los mensajes de la conversación (tanto USER como AGENT).
    Incluye la posición en la cola cuando el mensaje se encuentra en estado 'en_cola'.
    """
    usuario = UsuarioMensajeSerializer(read_only=True)
    pregunta_id = serializers.IntegerField(read_only=True, allow_null=True)
    conversacion_id = serializers.IntegerField(read_only=True)
    posicion_cola = serializers.SerializerMethodField()

    class Meta:
        model = Mensaje
        fields = (
            'id',
            'conversacion_id',
            'fecha_envio',
            'estado',
            'rol',
            'contenido',
            'pregunta_id',
            'usuario',
            'posicion_cola',
        )

    def get_posicion_cola(self, obj: Mensaje) -> int | None:
        if obj.estado != Mensaje.Estado.EN_COLA:
            return None
        posiciones = self.context.get('posiciones_cola') or {}
        if str(obj.id) in posiciones:
            return posiciones[str(obj.id)]
        if obj.id in posiciones:
            return posiciones[obj.id]
        return None


class ConversacionSerializer(serializers.ModelSerializer):
    """
    Serializer de la conversación de un proyecto con su listado de mensajes.
    """
    proyecto_id = serializers.IntegerField(read_only=True)
    mensajes = serializers.SerializerMethodField()

    class Meta:
        model = Conversacion
        fields = ('id', 'proyecto_id', 'fecha_creacion', 'mensajes')

    def get_mensajes(self, obj: Conversacion):
        qs = obj.mensajes.select_related('usuario').order_by('fecha_envio', 'id')
        return MensajeSerializer(qs, many=True, context=self.context).data


class EnviarConsultaAgenteSeniorSerializer(serializers.Serializer):
    """
    Serializer de entrada para recibir una consulta destinada al Agente Senior Colaborativo.
    """
    contenido = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
        help_text="Texto de la consulta para el Agente Senior."
    )
    mensaje = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
        help_text="Alias opcional para el texto de la consulta."
    )
    contexto_diagrama = serializers.DictField(
        required=False,
        allow_null=True,
        default=None,
        help_text="Contexto opcional en memoria del lienzo actual (entidades, atributos y relaciones)."
    )
    usar_ia_local = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Si es True, la consulta es respondida por el agente local; si es False, usa Gemini con respaldo en el agente local."
    )


class ConsultarAyudaSerializer(serializers.Serializer):
    """
    Serializer de entrada para el CU-14: Consultar Asistente de Ayuda de la herramienta CASE.
    """
    consulta = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=600,
        help_text="Consulta en lenguaje natural sobre una funcionalidad, herramienta o proceso."
    )
    interfaz = serializers.CharField(
        required=False,
        default='dashboard',
        max_length=50,
        help_text="Identificador de la interfaz activa del usuario (ej: 'dashboard', 'pizarra')."
    )


