from rest_framework import serializers
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
