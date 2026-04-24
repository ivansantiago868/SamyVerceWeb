from rest_framework import serializers
from apps.produccion.models import Insumo


class InsumoSerializer(serializers.ModelSerializer):
    diferencia       = serializers.ReadOnlyField()
    stock_disponible = serializers.ReadOnlyField()

    class Meta:
        model  = Insumo
        fields = "__all__"
        read_only_fields = ("empresa",)
