from rest_framework import serializers
from apps.produccion.models import Figura, FiguraImagen, FiguraPieza


class FiguraImagenSerializer(serializers.ModelSerializer):
    class Meta:
        model  = FiguraImagen
        fields = ["id", "imagen", "orden"]


class FiguraPiezaSerializer(serializers.ModelSerializer):
    pieza_nombre    = serializers.ReadOnlyField(source="pieza.nombre")
    pieza_costo     = serializers.ReadOnlyField(source="pieza.costo_total_real")
    pieza_precio    = serializers.ReadOnlyField(source="pieza.precio_venta_sugerido")
    subtotal_costo  = serializers.ReadOnlyField()
    subtotal_precio = serializers.ReadOnlyField()

    class Meta:
        model  = FiguraPieza
        fields = [
            "id", "figura", "pieza", "pieza_nombre",
            "pieza_costo", "pieza_precio",
            "cantidad", "subtotal_costo", "subtotal_precio",
        ]
        read_only_fields = ("figura",)


class FiguraSerializer(serializers.ModelSerializer):
    figura_piezas = FiguraPiezaSerializer(many=True, read_only=True)
    imagenes      = FiguraImagenSerializer(many=True, read_only=True)
    costo_total   = serializers.ReadOnlyField()
    precio_total  = serializers.ReadOnlyField()
    total_piezas  = serializers.ReadOnlyField()

    class Meta:
        model  = Figura
        fields = [
            "id", "nombre", "descripcion",
            "imagenes", "costo_total", "precio_total", "total_piezas",
            "figura_piezas", "creado_en", "actualizado_en",
        ]
        read_only_fields = ("empresa",)
