from rest_framework import serializers
from apps.produccion.models import Tarea


class TareaSerializer(serializers.ModelSerializer):
    restantes      = serializers.ReadOnlyField()
    maquina_nombre = serializers.CharField(source="maquina.nombre", read_only=True)

    class Meta:
        model  = Tarea
        fields = "__all__"
        read_only_fields = ("empresa",)

    def validate(self, data):
        if data.get("realizados", 0) > data.get("cantidad", 0):
            raise serializers.ValidationError("Los realizados no pueden superar la cantidad total.")
        return data
