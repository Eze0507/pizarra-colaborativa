from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
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
        data = super().validate(attrs)

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
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        return user

