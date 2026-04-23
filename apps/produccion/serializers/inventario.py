from rest_framework import serializers
from apps.produccion.models import InventarioPieza


class InventarioPiezaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = InventarioPieza
        fields = "__all__"
        read_only_fields = ("empresa",)
