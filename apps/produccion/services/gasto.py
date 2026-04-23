from django.db.models import Sum, Count
from apps.produccion.models import Gasto


class GastoService:

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
