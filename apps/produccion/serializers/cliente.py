from rest_framework import serializers
from apps.produccion.models import Cliente


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Cliente
        fields = "__all__"
        read_only_fields = ("empresa",)

    def validate_nombre(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("El nombre debe tener al menos 2 caracteres.")
        return value.strip()

    def validate_email(self, value):
        return "" if value and value.upper() == "N/A" else value
