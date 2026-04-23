from rest_framework import serializers
from apps.produccion.models import Gasto


class GastoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Gasto
        fields = "__all__"
        read_only_fields = ("empresa",)
