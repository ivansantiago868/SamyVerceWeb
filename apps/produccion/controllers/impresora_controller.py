"""
controllers/impresora_controller.py
Serializer y lógica de negocio para Impresoras.
"""
from rest_framework import serializers
from apps.produccion.models import Impresora


class ImpresoraSerializer(serializers.ModelSerializer):
    depreciacion_por_hora  = serializers.ReadOnlyField()
    mantenimiento_por_hora = serializers.ReadOnlyField()

    class Meta:
        model  = Impresora
        fields = "__all__"


class ImpresoraController:

    @staticmethod
    def activas():
        return Impresora.objects.filter(activa=True)

    @staticmethod
    def por_tipo(tipo: str):
        return Impresora.objects.filter(tipo=tipo, activa=True)
