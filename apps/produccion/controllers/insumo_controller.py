"""
controllers/insumo_controller.py
Serializer y lógica de negocio para Insumos.
"""
from rest_framework import serializers
from apps.produccion.models import Insumo

UMBRAL_STOCK_CRITICO_GRAMOS = 100


class InsumoSerializer(serializers.ModelSerializer):
    diferencia       = serializers.ReadOnlyField()
    stock_disponible = serializers.ReadOnlyField()

    class Meta:
        model  = Insumo
        fields = "__all__"


class InsumoController:

    @staticmethod
    def stock_critico():
        """Insumos con menos de 100 g disponibles."""
        return Insumo.objects.filter(cantidad_final__lte=UMBRAL_STOCK_CRITICO_GRAMOS)

    @staticmethod
    def descontar_stock(insumo_id: int, gramos: float) -> Insumo:
        """Descuenta gramos del stock final de un insumo."""
        insumo = Insumo.objects.select_for_update().get(pk=insumo_id)
        if float(insumo.cantidad_final) < gramos:
            raise ValueError(f"Stock insuficiente: disponible {insumo.cantidad_final}g, requerido {gramos}g.")
        insumo.cantidad_final = float(insumo.cantidad_final) - gramos
        insumo.save(update_fields=["cantidad_final"])
        return insumo
