"""
controllers/tarea_controller.py
Serializer y lógica de negocio para Tareas.
"""
from rest_framework import serializers
from apps.produccion.models import Tarea


class TareaSerializer(serializers.ModelSerializer):
    restantes      = serializers.ReadOnlyField()
    maquina_nombre = serializers.CharField(source="maquina.nombre", read_only=True)

    class Meta:
        model  = Tarea
        fields = "__all__"

    def validate(self, data):
        if data.get("realizados", 0) > data.get("cantidad", 0):
            raise serializers.ValidationError("Los realizados no pueden superar la cantidad total.")
        return data


class TareaController:

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
