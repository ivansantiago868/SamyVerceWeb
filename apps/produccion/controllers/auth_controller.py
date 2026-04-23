"""
controllers/auth_controller.py
Vistas de autenticación adicionales sobre SimpleJWT:
  - Registro de usuario
  - Logout (revoca el refresh token)
  - Perfil del usuario autenticado
"""
from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password


# ── Serializers ───────────────────────────────────────────────────

class RegistroSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, label="Confirmar contraseña")

    class Meta:
        model  = User
        fields = ("username", "email", "first_name", "last_name", "password", "password2")

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
        return user


class PerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ("id", "username", "email", "first_name", "last_name", "date_joined", "last_login")
        read_only_fields = ("id", "date_joined", "last_login")


# ── Views ─────────────────────────────────────────────────────────

class RegistroView(APIView):
    """
    POST /api/auth/registro/
    Crea un nuevo usuario. No requiere autenticación.

    Body:
    {
        "username": "samy",
        "email": "samy@correo.com",
        "first_name": "Samy",
        "last_name": "Verce",
        "password": "MiPassword123!",
        "password2": "MiPassword123!"
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistroSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        refresh = RefreshToken.for_user(user)

        return Response({
            "mensaje":       f"Usuario '{user.username}' creado exitosamente.",
            "access_token":  str(refresh.access_token),
            "refresh_token": str(refresh),
            "usuario": {
                "id":         user.id,
                "username":   user.username,
                "email":      user.email,
                "first_name": user.first_name,
                "last_name":  user.last_name,
            }
        }, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Revoca el refresh token (lo agrega a la blacklist).
    Requiere autenticación con Bearer token.

    Body:
    {
        "refresh": "<tu_refresh_token>"
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"error": "Se requiere el campo 'refresh' con el refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"mensaje": "Sesión cerrada correctamente."}, status=status.HTTP_200_OK)
        except TokenError:
            return Response(
                {"error": "Token inválido o ya expirado."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PerfilView(APIView):
    """
    GET  /api/auth/perfil/  → Ver datos del usuario autenticado
    PATCH /api/auth/perfil/ → Actualizar nombre, email
    Requiere autenticación con Bearer token.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = PerfilSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = PerfilSerializer(request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)
