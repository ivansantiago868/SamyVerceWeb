"""
controllers/cliente_controller.py
Serializer y lógica de negocio para Clientes.
"""
from rest_framework import serializers
from apps.produccion.models import Cliente


class ClienteSerializer(serializers.ModelSerializer):

    class Meta:
        model  = Cliente
        fields = "__all__"

    def validate_nombre(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("El nombre debe tener al menos 2 caracteres.")
        return value.strip()

    def validate_email(self, value):
        if value and value.upper() == "N/A":
            return ""
        return value


class ClienteController:
    """Operaciones de negocio sobre Clientes."""

    @staticmethod
    def buscar(termino: str):
        return Cliente.objects.filter(nombre__icontains=termino)

    @staticmethod
    def obtener_con_pedidos(cliente_id: int):
        return Cliente.objects.prefetch_related("pedido_set").get(pk=cliente_id)
