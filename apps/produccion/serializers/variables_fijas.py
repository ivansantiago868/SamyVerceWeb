from rest_framework import serializers
from apps.produccion.models import VariablesFijas


class VariablesFijasSerializer(serializers.ModelSerializer):
    class Meta:
        model  = VariablesFijas
        fields = "__all__"
        read_only_fields = ("empresa",)

    def validate_margen_ganancia(self, value):
        if float(value) >= 1:
            raise serializers.ValidationError("Debe ser menor a 1 (ej: 0.35 para 35%).")
        return value

    def validate_margen_fallos(self, value):
        if float(value) >= 1:
            raise serializers.ValidationError("Debe ser menor a 1 (ej: 0.10 para 10%).")
        return value
