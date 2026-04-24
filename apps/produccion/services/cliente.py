from apps.produccion.models import Cliente


class ClienteService:

    @staticmethod
    def buscar(termino: str):
        return Cliente.objects.filter(nombre__icontains=termino)

    @staticmethod
    def obtener_con_pedidos(cliente_id: int):
        return Cliente.objects.prefetch_related("pedido_set").get(pk=cliente_id)
