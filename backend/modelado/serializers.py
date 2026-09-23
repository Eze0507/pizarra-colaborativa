from django.conf import settings
from django.contrib.auth.models import User
from django.core import signing
from django.core.mail import send_mail
from rest_framework import serializers

from .models import Proyecto, Entidad, Atributo, Relacion
from usuario.models import UserColaborador


class UserSimpleSerializer(serializers.ModelSerializer):
    """
    Serializer básico de usuario para mostrar información resumida.
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')


class ColaboradorDetalleSerializer(serializers.ModelSerializer):
    """
    Serializer para los colaboradores dentro de un proyecto.
    """
    usuario = UserSimpleSerializer(read_only=True)

    class Meta:
        model = UserColaborador
        fields = ('id', 'usuario', 'rol', 'estado', 'fecha_ingreso')


class ProyectoDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado de Proyecto con propietario y lista de colaboradores.
    """
    propietario = UserSimpleSerializer(read_only=True)
    colaboradores_detalle = ColaboradorDetalleSerializer(many=True, read_only=True)
    es_propietario = serializers.SerializerMethodField()

    class Meta:
        model = Proyecto
        fields = (
            'id',
            'codigo',
            'nombre',
            'descripcion',
            'paquete_base',
            'datos_diagrama',
            'fecha_creacion',
            'fecha_actualizacion',
            'propietario',
            'colaboradores_detalle',
            'es_propietario',
        )

    def get_es_propietario(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.propietario_id == request.user.id
        return False


class ProyectoCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para la creación de proyectos.
    Solo solicita 'nombre' y 'descripcion', los demás atributos se generan automáticamente.
    """
    propietario = UserSimpleSerializer(read_only=True)

    class Meta:
        model = Proyecto
        fields = (
            'id',
            'codigo',
            'nombre',
            'descripcion',
            'paquete_base',
            'fecha_creacion',
            'fecha_actualizacion',
            'propietario',
        )
        read_only_fields = ('id', 'codigo', 'paquete_base', 'fecha_creacion', 'fecha_actualizacion', 'propietario')

    def create(self, validated_data):
        request = self.context.get('request')
        propietario = request.user

        # 1. Crear el proyecto (save() del modelo autogenera codigo y paquete_base)
        proyecto = Proyecto.objects.create(
            propietario=propietario,
            nombre=validated_data['nombre'].strip(),
            descripcion=validated_data.get('descripcion', '').strip()
        )

        # 2. Registrar al creador como propietario en UserColaborador con estado activo
        UserColaborador.objects.create(
            usuario=propietario,
            proyecto=proyecto,
            rol=UserColaborador.Rol.PROPIETARIO,
            estado=UserColaborador.Estado.ACTIVO
        )

        return proyecto


class InvitarColaboradorSerializer(serializers.Serializer):
    """
    Serializer para invitar a un usuario a colaborar en un proyecto.
    Recibe email o username del colaborador.
    """
    email = serializers.EmailField(required=False, allow_blank=True)
    username = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        email = attrs.get('email', '').strip()
        username = attrs.get('username', '').strip()

        if not email and not username:
            raise serializers.ValidationError(
                "Debe proporcionar al menos un correo electrónico o nombre de usuario para invitar."
            )

        # Buscar usuario destino
        target_user = None
        if email:
            target_user = User.objects.filter(email__iexact=email).first()
        elif username:
            target_user = User.objects.filter(username__iexact=username).first()

        if not target_user:
            identificador = email or username
            raise serializers.ValidationError(
                f"No se encontró ningún usuario registrado con '{identificador}'."
            )

        proyecto = self.context.get('proyecto')
        request_user = self.context.get('request').user

        # Verificar que el solicitante sea el propietario
        if proyecto.propietario != request_user:
            raise serializers.ValidationError(
                "Solo el propietario del proyecto puede invitar a nuevos colaboradores."
            )

        # Verificar que no se invite a sí mismo
        if target_user == proyecto.propietario:
            raise serializers.ValidationError(
                "El propietario del proyecto ya es colaborador principal."
            )

        # Verificar si ya es colaborador activo
        colaboracion_existente = UserColaborador.objects.filter(
            usuario=target_user,
            proyecto=proyecto
        ).first()

        if colaboracion_existente and colaboracion_existente.estado == UserColaborador.Estado.ACTIVO:
            raise serializers.ValidationError(
                f"El usuario '{target_user.username}' ya es colaborador activo de este proyecto."
            )

        attrs['target_user'] = target_user
        attrs['colaboracion_existente'] = colaboracion_existente
        return attrs

    def save(self, **kwargs):
        target_user = self.validated_data['target_user']
        colaboracion = self.validated_data.get('colaboracion_existente')
        proyecto = self.context.get('proyecto')

        if not colaboracion:
            colaboracion = UserColaborador.objects.create(
                usuario=target_user,
                proyecto=proyecto,
                rol=UserColaborador.Rol.EDITOR,
                estado=UserColaborador.Estado.PENDIENTE
            )
        else:
            # Si ya existía pero estaba pendiente, actualizamos rol y garantizamos pendiente
            colaboracion.rol = UserColaborador.Rol.EDITOR
            colaboracion.estado = UserColaborador.Estado.PENDIENTE
            colaboracion.save()

        # Generar token firmado para la invitación (48 horas de validez)
        token = signing.dumps({
            'colaborador_id': colaboracion.id,
            'proyecto_id': proyecto.id,
            'usuario_id': target_user.id
        }, salt='project-invitation')

        invitation_url = f"http://localhost:4200/invitacion/{token}"

        # Enviar correo mediante Gmail SMTP
        subject = f"Invitación para colaborar en el proyecto {proyecto.nombre}"
        nombre_destinatario = target_user.first_name or target_user.username
        message = (
            f"Hola {nombre_destinatario},\n\n"
            f"{proyecto.propietario.username} te ha invitado a colaborar como editor en el proyecto "
            f"\"{proyecto.nombre}\" ({proyecto.codigo}) dentro de la Herramienta CASE de Diseño de Datos.\n\n"
            f"Para aceptar la invitación y comenzar a editar en conjunto, haz clic en el siguiente enlace:\n"
            f"{invitation_url}\n\n"
            f"Este enlace expirará en 48 horas."
        )

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[target_user.email],
                fail_silently=False
            )
        except Exception as e:
            print(f"[EMAIL_INVITE_LOG] Error enviando correo de invitación a {target_user.email}: {e}")
            print(f"[INVITATION_LINK] {invitation_url}")

        return colaboracion


class AceptarInvitacionSerializer(serializers.Serializer):
    """
    Serializer para aceptar una invitación y activar al colaborador como editor.
    """
    token = serializers.CharField(required=True)

    def validate(self, attrs):
        token = attrs.get('token')

        try:
            # Válido por 48 horas (172800 segundos)
            data = signing.loads(token, salt='project-invitation', max_age=172800)
            colaborador_id = data.get('colaborador_id')
            proyecto_id = data.get('proyecto_id')
            usuario_id = data.get('usuario_id')
        except signing.SignatureExpired:
            raise serializers.ValidationError(
                {'detail': 'La invitación ha expirado. Solicite una nueva invitación al propietario.'}
            )
        except signing.BadSignature:
            raise serializers.ValidationError(
                {'detail': 'El token de invitación es inválido o ha sido modificado.'}
            )

        colaboracion = UserColaborador.objects.filter(
            id=colaborador_id,
            proyecto_id=proyecto_id,
            usuario_id=usuario_id
        ).select_related('proyecto', 'usuario').first()

        if not colaboracion:
            raise serializers.ValidationError(
                {'detail': 'La invitación no corresponde a ningún colaborador registrado.'}
            )

        attrs['colaboracion'] = colaboracion
        return attrs

    def save(self, **kwargs):
        colaboracion = self.validated_data['colaboracion']
        colaboracion.estado = UserColaborador.Estado.ACTIVO
        colaboracion.rol = UserColaborador.Rol.EDITOR
        colaboracion.save()
        return colaboracion


class AtributoDiagramaSerializer(serializers.ModelSerializer):
    """
    Serializer para atributos de entidades UML en la carga inicial de la pizarra.
    """
    class Meta:
        model = Atributo
        fields = ('id', 'nombre', 'tipo', 'es_clave', 'es_nulo', 'orden')


class EntidadDiagramaSerializer(serializers.ModelSerializer):
    """
    Serializer para entidades UML con sus atributos anidados en orden secuencial.
    No incluye 'alto' ya que este se calcula dinámicamente en el frontend según sus atributos.
    """
    atributos = AtributoDiagramaSerializer(many=True, read_only=True)

    class Meta:
        model = Entidad
        fields = ('id', 'nombre', 'estado', 'coord_x', 'coord_y', 'ancho', 'es_intermedia', 'atributos')


class RelacionDiagramaSerializer(serializers.ModelSerializer):
    """
    Serializer para relaciones UML entre entidades con cardinalidades de origen y destino.
    """
    entidad_origen_id = serializers.IntegerField(source='entidad_origen.id')
    entidad_destino_id = serializers.IntegerField(source='entidad_destino.id')
    clase_asociacion_id = serializers.IntegerField(source='clase_asociacion.id', allow_null=True, read_only=True)

    class Meta:
        model = Relacion
        fields = (
            'id',
            'nombre_relacion',
            'tipo',
            'entidad_origen_id',
            'entidad_destino_id',
            'clase_asociacion_id',
            'cardinalidad_origen',
            'cardinalidad_destino',
            'puerto_origen',
            'puerto_destino'
        )


class InvitacionPendienteSerializer(serializers.ModelSerializer):
    """
    Serializer para consultar las invitaciones pendientes recibidas por un usuario.
    """
    proyecto = serializers.SerializerMethodField()

    class Meta:
        model = UserColaborador
        fields = ('id', 'proyecto', 'rol', 'estado', 'fecha_ingreso')

    def get_proyecto(self, obj):
        return {
            'id': obj.proyecto.id,
            'codigo': obj.proyecto.codigo,
            'nombre': obj.proyecto.nombre,
            'descripcion': obj.proyecto.descripcion,
            'propietario': UserSimpleSerializer(obj.proyecto.propietario).data
        }

