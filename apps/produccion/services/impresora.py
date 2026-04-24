from apps.produccion.models import Impresora


class ImpresoraService:

    @staticmethod
    def activas():
        return Impresora.objects.filter(activa=True)

    @staticmethod
    def por_tipo(tipo: str):
        return Impresora.objects.filter(tipo=tipo, activa=True)
