from rest_framework import serializers
from apps.produccion.models import Venta


class VentaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Venta
        fields = "__all__"
        read_only_fields = ("empresa",)
