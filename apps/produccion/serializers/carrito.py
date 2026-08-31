from rest_framework import serializers


class CarritoItemSerializer(serializers.Serializer):
    """Un producto del carrito: figura + cantidad, con color/tipo opcionales
    (solo si la figura los tiene definidos)."""
    figura_id = serializers.IntegerField()
    cantidad  = serializers.IntegerField(min_value=1)
    color_id  = serializers.IntegerField(required=False, allow_null=True)
    tipo_id   = serializers.IntegerField(required=False, allow_null=True)


class CarritoCheckoutSerializer(serializers.Serializer):
    """Datos del checkout público (sin pago): solo nombre y dirección de
    quien recibe, más los productos elegidos."""
    nombre_recibe = serializers.CharField(max_length=255, trim_whitespace=True)
    direccion     = serializers.CharField(trim_whitespace=True)
    items         = CarritoItemSerializer(many=True)

    def validate_nombre_recibe(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("El nombre debe tener al menos 2 caracteres.")
        return value.strip()

    def validate_direccion(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Ingresa una dirección válida.")
        return value.strip()

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("El carrito está vacío.")
        return value
