"""
serializers/cliente_portal.py
Serialización de los pedidos que ve un cliente logueado en su portal
(catálogo público). Solo lo que le interesa a un cliente sobre su propio
pedido: qué pidió, cuánto y en qué va — nunca costos ni datos internos.
"""
from rest_framework import serializers
from apps.produccion.models import Pedido


class ClientePedidoSerializer(serializers.ModelSerializer):
    figura       = serializers.CharField(source="figura.nombre", default="", read_only=True)
    imagen       = serializers.SerializerMethodField()
    color        = serializers.CharField(source="color.nombre", default=None, allow_null=True, read_only=True)
    tipo         = serializers.CharField(source="tipo.nombre", default=None, allow_null=True, read_only=True)
    precio_total = serializers.ReadOnlyField()

    class Meta:
        model  = Pedido
        fields = [
            "id", "figura", "imagen", "color", "tipo",
            "cantidad", "precio_total", "estado", "fecha_entrega", "creado_en",
        ]

    def get_imagen(self, obj):
        return obj.figura.primera_imagen_url if obj.figura_id else None
