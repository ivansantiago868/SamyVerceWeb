from apps.produccion.models import Tarea


class TareaService:

    @staticmethod
    def pendientes():
        return Tarea.objects.filter(
            estado__in=[Tarea.Estado.PENDIENTE, Tarea.Estado.EN_COLA]
        ).order_by("fecha_entrega")

    @staticmethod
    def por_maquina(maquina_id: int):
        return Tarea.objects.filter(maquina_id=maquina_id)

    @staticmethod
    def cambiar_estado(tarea_id: int, nuevo_estado: str) -> Tarea:
        tarea = Tarea.objects.get(pk=tarea_id)
        tarea.estado = nuevo_estado
        tarea.save(update_fields=["estado"])
        return tarea
