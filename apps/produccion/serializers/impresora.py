from rest_framework import serializers
from apps.produccion.models import Impresora


class ImpresoraSerializer(serializers.ModelSerializer):
    depreciacion_por_hora  = serializers.ReadOnlyField()
    mantenimiento_por_hora = serializers.ReadOnlyField()

    class Meta:
        model  = Impresora
        fields = "__all__"
        read_only_fields = ("empresa",)
