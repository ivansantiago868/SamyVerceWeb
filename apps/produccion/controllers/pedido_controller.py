"""
controllers/pedido_controller.py
Lógica de negocio para Pedidos (el serializer vive en serializers/pedido.py).
"""
from django.db.models import Count, Sum
from apps.produccion.models import Pedido


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
