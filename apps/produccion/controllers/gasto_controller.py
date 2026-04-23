"""
controllers/gasto_controller.py
Serializer y lógica de negocio para Gastos.
"""
from rest_framework import serializers
from django.db.models import Sum, Count
from apps.produccion.models import Gasto


class GastoSerializer(serializers.ModelSerializer):

    class Meta:
        model  = Gasto
        fields = "__all__"

    def validate_cuui(self, value):
        if value <= 0:
            raise serializers.ValidationError("El CUUI debe ser un número positivo.")
        return value


class GastoController:

    @staticmethod
    def resumen():
        return Gasto.objects.aggregate(
            total_gastado=Sum("costo"),
            total_gramos=Sum("peso"),
            num_compras=Count("id"),
        )

    @staticmethod
    def por_periodo(fecha_inicio, fecha_fin):
        return Gasto.objects.filter(fecha__range=(fecha_inicio, fecha_fin))
