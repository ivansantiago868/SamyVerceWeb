"""
controllers/inventario_controller.py
Serializer y lógica de negocio para el Inventario de Piezas.
"""
from rest_framework import serializers
from apps.produccion.models import InventarioPieza


class InventarioPiezaSerializer(serializers.ModelSerializer):

    class Meta:
        model  = InventarioPieza
        fields = "__all__"


class InventarioController:

    @staticmethod
    def buscar(termino: str):
        return InventarioPieza.objects.filter(nombre__icontains=termino)

    @staticmethod
    def por_rango_precio(precio_min: float, precio_max: float):
        return InventarioPieza.objects.filter(
            precio_venta_sugerido__gte=precio_min,
            precio_venta_sugerido__lte=precio_max,
        )
