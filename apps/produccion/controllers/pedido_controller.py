"""
controllers/pedido_controller.py
Serializer y lógica de negocio para Pedidos.
"""
from rest_framework import serializers
from django.db.models import Count, Sum
from apps.produccion.models import Pedido


class PedidoSerializer(serializers.ModelSerializer):
    restantes       = serializers.ReadOnlyField()
    peso_total      = serializers.ReadOnlyField()
    precio_total    = serializers.ReadOnlyField()
    cliente_nombre  = serializers.CharField(source="cliente.nombre",    read_only=True)
    pieza_nombre    = serializers.CharField(source="pieza.nombre",      read_only=True)
    material_nombre = serializers.CharField(source="material.producto", read_only=True)
    maquina_nombre  = serializers.CharField(source="maquina.nombre",    read_only=True)

    class Meta:
        model  = Pedido
        fields = "__all__"

    def validate(self, data):
        if data.get("realizados", 0) > data.get("cantidad", 0):
            raise serializers.ValidationError("Los realizados no pueden superar la cantidad total.")
        return data

    def create(self, validated_data):
        validated_data["realizados"] = 0
        return super().create(validated_data)


class PedidoController:

    @staticmethod
    def dashboard():
        qs = Pedido.objects.all()
        return {
            "total_pedidos":    qs.count(),
            "por_estado":       list(qs.values("estado").annotate(total=Count("id"))),
            "por_prioridad":    list(qs.values("prioridad").annotate(total=Count("id"))),
            "ingresos_totales": qs.aggregate(s=Sum("precio_unidad"))["s"] or 0,
        }

    @staticmethod
    def pendientes_por_maquina(maquina_id: int):
        return Pedido.objects.filter(
            maquina_id=maquina_id,
            estado__in=[Pedido.Estado.PENDIENTE, Pedido.Estado.EN_COLA, Pedido.Estado.IMPRIMIENDO],
        )

    @staticmethod
    def cambiar_estado(pedido_id: int, nuevo_estado: str) -> Pedido:
        pedido = Pedido.objects.get(pk=pedido_id)
        pedido.estado = nuevo_estado
        pedido.save(update_fields=["estado"])
        return pedido
