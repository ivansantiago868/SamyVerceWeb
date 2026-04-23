"""
controllers/variables_fijas_controller.py
Serializer y lógica para el Singleton de Variables Fijas.
"""
from rest_framework import serializers
from apps.produccion.models import VariablesFijas


class VariablesFijasSerializer(serializers.ModelSerializer):

    class Meta:
        model  = VariablesFijas
        fields = "__all__"

    def validate_margen_ganancia(self, value):
        if float(value) >= 1:
            raise serializers.ValidationError("El margen de ganancia debe ser menor a 1 (ej: 0.35 para 35%).")
        return value

    def validate_margen_fallos(self, value):
        if float(value) >= 1:
            raise serializers.ValidationError("El margen de fallos debe ser menor a 1 (ej: 0.10 para 10%).")
        return value


class VariablesFijasController:

    @staticmethod
    def obtener() -> VariablesFijas:
        """Retorna el singleton. Si no existe, lo crea con valores por defecto."""
        obj, _ = VariablesFijas.objects.get_or_create(pk=1)
        return obj
