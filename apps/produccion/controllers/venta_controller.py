"""
controllers/venta_controller.py
Serializer y lógica de negocio para Ventas.
"""
from rest_framework import serializers
from django.db.models import Sum, Count
from apps.produccion.models import Venta


class VentaSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente.nombre",   read_only=True)
    pedido_str     = serializers.CharField(source="pedido.__str__",   read_only=True)

    class Meta:
        model  = Venta
        fields = "__all__"


class VentaController:

    @staticmethod
    def resumen():
        return Venta.objects.aggregate(
            total_ventas=Count("id"),
            total_unidades=Sum("cantidad"),
        )

    @staticmethod
    def por_cliente(cliente_id: int):
        return Venta.objects.filter(cliente_id=cliente_id).order_by("-fecha")

    @staticmethod
    def por_periodo(fecha_inicio, fecha_fin):
        return Venta.objects.filter(fecha__range=(fecha_inicio, fecha_fin))
