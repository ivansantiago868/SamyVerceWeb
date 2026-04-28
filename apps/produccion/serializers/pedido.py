from rest_framework import serializers
from apps.produccion.models import Pedido


class PedidoSerializer(serializers.ModelSerializer):
    restantes      = serializers.ReadOnlyField()
    peso_total     = serializers.ReadOnlyField()
    precio_total   = serializers.ReadOnlyField()
    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True)
    figura_nombre  = serializers.CharField(source="figura.nombre",  read_only=True)
    maquina_nombre = serializers.CharField(source="maquina.nombre", read_only=True)

    class Meta:
        model  = Pedido
        fields = "__all__"
        read_only_fields = ("empresa",)

    def validate(self, data):
        if data.get("realizados", 0) > data.get("cantidad", 0):
            raise serializers.ValidationError("Los realizados no pueden superar la cantidad total.")
        return data

    def create(self, validated_data):
        validated_data["realizados"] = 0
        return super().create(validated_data)
