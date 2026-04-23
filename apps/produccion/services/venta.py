from django.db.models import Sum, Count
from apps.produccion.models import Venta


class VentaService:

    @staticmethod
    def resumen():
        return Venta.objects.aggregate(
            total_ventas=Count("id"),
        )

    @staticmethod
    def por_periodo(fecha_inicio, fecha_fin):
        return Venta.objects.filter(fecha__range=(fecha_inicio, fecha_fin))
