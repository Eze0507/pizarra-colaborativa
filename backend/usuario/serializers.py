from django.conf import settings
from django.contrib.auth.models import User
from django.core import signing
from django.core.mail import send_mail
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from core.utils import get_frontend_url
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken, TokenError


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personalizado para TokenObtainPair que incluye
    información adicional del usuario tanto en el payload del JWT
    como en la respuesta JSON.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Reclamaciones personalizadas en el token
        token['username'] = user.username
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name

        return token

    def validate(self, attrs):
        try:
            data = super().validate(attrs)
        except Exception as e:
            username = attrs.get(self.username_field)
            password = attrs.get('password')
            user = User.objects.filter(username=username).first()
            if user and user.check_password(password) and not user.is_active:
                raise serializers.ValidationError({
                    'detail': 'Tu cuenta no está activada. Por favor revisa tu correo electrónico para activarla.'
                })
            raise e

        # Datos adicionales del usuario en la respuesta JSON
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
        }

        return data


class LogoutSerializer(serializers.Serializer):
    """
    Serializer para validar y procesar el cierre de sesión mediante
    la inclusión del refresh token en la lista negra (blacklist).
    """
    refresh = serializers.CharField(
        required=True,
        help_text="Token de refresco que se agregará a la lista negra."
    )

    def validate(self, attrs):
        self.token = attrs.get('refresh')
        return attrs

    def save(self, **kwargs):
        try:
            token = RefreshToken(self.token)
            token.blacklist()
        except TokenError as e:
            raise serializers.ValidationError({
                'refresh': f'El token es inválido o ya ha sido revocado: {str(e)}'
            })


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Serializer para el registro de nuevos usuarios con validación de contraseña
    de al menos 8 caracteres (única restricción requerida) y campos requeridos:
    nombre (first_name), apellido (last_name), correo (email),
    nombre de usuario (username) y contraseña (password).
    """
    first_name = serializers.CharField(
        required=True,
        allow_blank=False,
        error_messages={
            'required': 'El nombre es obligatorio.',
            'blank': 'El nombre no puede estar vacío.'
        }
    )
    last_name = serializers.CharField(
        required=True,
        allow_blank=False,
        error_messages={
            'required': 'El apellido es obligatorio.',
            'blank': 'El apellido no puede estar vacío.'
        }
    )
    email = serializers.EmailField(
        required=True,
        allow_blank=False,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message='Ya existe un usuario con este correo electrónico.'
            )
        ],
        error_messages={
            'required': 'El correo electrónico es obligatorio.',
            'blank': 'El correo electrónico no puede estar vacío.',
            'invalid': 'Ingrese un correo electrónico válido.'
        }
    )
    username = serializers.CharField(
        required=True,
        allow_blank=False,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message='Ya existe un usuario con este nombre de usuario.'
            )
        ],
        error_messages={
            'required': 'El nombre de usuario es obligatorio.',
            'blank': 'El nombre de usuario no puede estar vacío.'
        }
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        allow_blank=False,
        style={'input_type': 'password'},
        error_messages={
            'required': 'La contraseña es obligatoria.',
            'blank': 'La contraseña no puede estar vacía.'
        }
    )

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'password')

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                'La contraseña debe tener al menos 8 caracteres.'
            )
        return value

    def create(self, validated_data):
        # 1. Crear el usuario en estado inactivo
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            is_active=False
        )

        # 2. Generar token temporal firmado (24h de vigencia)
        request = self.context.get('request')
        base_url = get_frontend_url(request)
        activation_url = f"{base_url}/activar/{token}"

        # 3. Enviar correo de verificación por Gmail
        subject = "¡Gracias por registrarte en nuestra Herramienta CASE!"
        message = (
            f"¡Gracias por registrarte en nuestra Herramienta CASE!\n\n"
            f"Haz clic aquí para activar tu cuenta:\n"
            f"{activation_url}\n\n"
            f"Este enlace de activación expirará en 24 horas."
        )

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False
            )
        except Exception as e:
            # Imprimir en consola en caso de fallo para permitir pruebas locales
            print(f"[EMAIL_LOG] No se pudo enviar el correo por SMTP a {user.email}: {e}")
            print(f"[ACTIVATION_LINK] {activation_url}")

        return user


class ActivateAccountSerializer(serializers.Serializer):
    """
    Serializer para validar el token de activación y activar la cuenta de usuario.
    """
    token = serializers.CharField(
        required=True,
        help_text="Token criptográfico de activación enviado por correo."
    )

    def validate(self, attrs):
        token = attrs.get('token')

        try:
            # Token válido por 24 horas (86400 segundos)
            data = signing.loads(token, salt='account-activation', max_age=86400)
            user_id = data.get('user_id')
        except signing.SignatureExpired:
            raise serializers.ValidationError(
                {'detail': 'El enlace de activación ha expirado. Por favor solicite un nuevo registro.'}
            )
        except signing.BadSignature:
            raise serializers.ValidationError(
                {'detail': 'El token de activación es inválido o está corrupto.'}
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {'detail': 'El usuario asociado al token no fue encontrado.'}
            )

        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        if not user.is_active:
            user.is_active = True
            user.save()
        return user


