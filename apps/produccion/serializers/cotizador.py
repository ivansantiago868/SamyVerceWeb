from rest_framework import serializers


class CotizadorInputSerializer(serializers.Serializer):
    nombre_pieza             = serializers.CharField(max_length=255)
    peso_gramos              = serializers.FloatField(min_value=0.1)
    tiempo_impresion_horas   = serializers.FloatField(min_value=0.01)
    tiempo_postproceso_horas = serializers.FloatField(min_value=0, default=0.0)
    costo_empaque_override   = serializers.FloatField(min_value=0, default=0.0)


class CotizadorLoteInputSerializer(CotizadorInputSerializer):
    cantidad = serializers.IntegerField(min_value=1)


class CotizadorDesdeCatalogoSerializer(serializers.Serializer):
    pieza_id                 = serializers.IntegerField()
    tiempo_postproceso_horas = serializers.FloatField(min_value=0, default=0.0)
    costo_empaque_override   = serializers.FloatField(min_value=0, default=0.0)


class CotizadorDesdeCatalogoLoteSerializer(CotizadorDesdeCatalogoSerializer):
    cantidad = serializers.IntegerField(min_value=1)
