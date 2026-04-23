"""
controllers/cotizador_controller.py
Serializers de entrada y orquestación del Cotizador.
La lógica matemática vive en services/cotizador.py.
"""
from rest_framework import serializers
from apps.produccion.models import InventarioPieza, VariablesFijas
from apps.produccion.services.cotizador import cotizar, cotizar_por_cantidad


# ── Serializers de input ──────────────────────────────────────────

class CotizadorInputSerializer(serializers.Serializer):
    nombre_pieza             = serializers.CharField(max_length=255)
    peso_gramos              = serializers.FloatField(min_value=0.1,  help_text="Peso en gramos")
    tiempo_impresion_horas   = serializers.FloatField(min_value=0.01, help_text="Tiempo de impresión en horas")
    tiempo_postproceso_horas = serializers.FloatField(min_value=0,    default=0.0)
    costo_empaque_override   = serializers.FloatField(min_value=0,    default=0.0,
                                                      help_text="Cantidad de empaques (precio unitario viene de Variables Fijas)")


class CotizadorLoteInputSerializer(CotizadorInputSerializer):
    cantidad = serializers.IntegerField(min_value=1, help_text="Cantidad de piezas")


class CotizadorDesdeCatalogoSerializer(serializers.Serializer):
    pieza_id                 = serializers.IntegerField(help_text="ID de la pieza en Inventario")
    tiempo_postproceso_horas = serializers.FloatField(min_value=0, default=0.0)
    costo_empaque_override   = serializers.FloatField(min_value=0, default=0.0)


class CotizadorDesdeCatalogoLoteSerializer(CotizadorDesdeCatalogoSerializer):
    cantidad = serializers.IntegerField(min_value=1)


# ── Controlador ───────────────────────────────────────────────────

class CotizadorController:

    @staticmethod
    def _get_variables():
        try:
            return VariablesFijas.objects.get(pk=1)
        except VariablesFijas.DoesNotExist:
            raise ValueError(
                "No existen Variables Fijas configuradas. "
                "Créalas en /api/v1/variables-fijas/ antes de cotizar."
            )

    @classmethod
    def cotizar_pieza(cls, datos: dict) -> dict:
        variables = cls._get_variables()
        resultado = cotizar(
            nombre_pieza             = datos["nombre_pieza"],
            peso_gramos              = datos["peso_gramos"],
            tiempo_impresion_horas   = datos["tiempo_impresion_horas"],
            tiempo_postproceso_horas = datos.get("tiempo_postproceso_horas", 0),
            costo_empaque_override   = datos.get("costo_empaque_override", 0),
            variables                = variables,
        )
        return resultado.to_dict()

    @classmethod
    def cotizar_lote(cls, datos: dict) -> dict:
        variables = cls._get_variables()
        return cotizar_por_cantidad(
            nombre_pieza             = datos["nombre_pieza"],
            peso_gramos              = datos["peso_gramos"],
            tiempo_impresion_horas   = datos["tiempo_impresion_horas"],
            cantidad                 = datos["cantidad"],
            tiempo_postproceso_horas = datos.get("tiempo_postproceso_horas", 0),
            costo_empaque_override   = datos.get("costo_empaque_override", 0),
            variables                = variables,
        )

    @classmethod
    def cotizar_desde_catalogo(cls, datos: dict) -> dict:
        variables = cls._get_variables()
        try:
            pieza = InventarioPieza.objects.get(pk=datos["pieza_id"])
        except InventarioPieza.DoesNotExist:
            raise LookupError(f"Pieza con ID {datos['pieza_id']} no encontrada en el inventario.")

        resultado = cotizar(
            nombre_pieza             = pieza.nombre,
            peso_gramos              = float(pieza.peso_gramos),
            tiempo_impresion_horas   = float(pieza.tiempo_impresion_horas),
            tiempo_postproceso_horas = datos.get("tiempo_postproceso_horas", 0),
            costo_empaque_override   = datos.get("costo_empaque_override", 0),
            variables                = variables,
        )
        data = resultado.to_dict()
        data["pieza_catalogo"] = {
            "id":                 pieza.id,
            "nombre":             pieza.nombre,
            "precio_guardado":    float(pieza.precio_venta_sugerido),
            "costo_guardado":     float(pieza.costo_total_real),
            "precio_recalculado": resultado.precio_venta_sugerido,
            "diferencia_precio":  resultado.precio_venta_sugerido - float(pieza.precio_venta_sugerido),
        }
        return data

    @classmethod
    def cotizar_lote_desde_catalogo(cls, datos: dict) -> dict:
        variables = cls._get_variables()
        try:
            pieza = InventarioPieza.objects.get(pk=datos["pieza_id"])
        except InventarioPieza.DoesNotExist:
            raise LookupError(f"Pieza con ID {datos['pieza_id']} no encontrada en el inventario.")

        resultado = cotizar_por_cantidad(
            nombre_pieza             = pieza.nombre,
            peso_gramos              = float(pieza.peso_gramos),
            tiempo_impresion_horas   = float(pieza.tiempo_impresion_horas),
            cantidad                 = datos["cantidad"],
            tiempo_postproceso_horas = datos.get("tiempo_postproceso_horas", 0),
            costo_empaque_override   = datos.get("costo_empaque_override", 0),
            variables                = variables,
        )
        resultado["pieza_catalogo"] = {"id": pieza.id, "nombre": pieza.nombre}
        return resultado
