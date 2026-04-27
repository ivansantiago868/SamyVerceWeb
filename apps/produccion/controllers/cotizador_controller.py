"""
controllers/cotizador_controller.py
Serializers de entrada y orquestación del Cotizador.
La lógica matemática vive en services/cotizador.py.
"""
from rest_framework import serializers
from apps.produccion.models import InventarioPieza, VariablesFijas, Impresora, Insumo
from apps.produccion.services.cotizador import cotizar, cotizar_por_cantidad


# ── Serializers de input ──────────────────────────────────────────

class CotizadorInputSerializer(serializers.Serializer):
    nombre_pieza             = serializers.CharField(max_length=255)
    peso_gramos              = serializers.FloatField(min_value=0.1,  help_text="Peso en gramos")
    tiempo_impresion_horas   = serializers.FloatField(min_value=0.01, help_text="Tiempo de impresión en horas")
    tiempo_postproceso_horas = serializers.FloatField(min_value=0,    default=0.0)
    costo_empaque_override   = serializers.FloatField(min_value=0,    default=0.0,
                                                      help_text="Cantidad de empaques (precio unitario viene de Variables Fijas)")
    impresora_id             = serializers.IntegerField(required=False, allow_null=True, default=None)
    insumo_id                = serializers.IntegerField(required=False, allow_null=True, default=None)


class CotizadorLoteInputSerializer(CotizadorInputSerializer):
    cantidad = serializers.IntegerField(min_value=1, help_text="Cantidad de piezas")


class CotizadorDesdeCatalogoSerializer(serializers.Serializer):
    pieza_id                 = serializers.IntegerField(help_text="ID de la pieza en Inventario")
    tiempo_postproceso_horas = serializers.FloatField(min_value=0, default=0.0)
    costo_empaque_override   = serializers.FloatField(min_value=0, default=0.0)
    impresora_id             = serializers.IntegerField(required=False, allow_null=True, default=None)
    insumo_id                = serializers.IntegerField(required=False, allow_null=True, default=None)


class CotizadorDesdeCatalogoLoteSerializer(CotizadorDesdeCatalogoSerializer):
    cantidad = serializers.IntegerField(min_value=1)


# ── Controlador ───────────────────────────────────────────────────

class CotizadorController:

    @staticmethod
    def _get_empresa_from_user(user):
        if not user or not user.is_authenticated:
            return None
        if user.is_superuser:
            return None
        try:
            return user.perfil.empresa
        except Exception:
            return None

    @staticmethod
    def _get_variables(empresa=None):
        try:
            if empresa:
                try:
                    return VariablesFijas.objects.get(empresa=empresa)
                except VariablesFijas.DoesNotExist:
                    pass
            return VariablesFijas.objects.get(pk=1)
        except VariablesFijas.DoesNotExist:
            raise ValueError(
                "No existen Variables Fijas configuradas. "
                "Créalas en /api/v1/variables-fijas/ antes de cotizar."
            )

    @staticmethod
    def _get_impresora(impresora_id, empresa):
        if not impresora_id:
            return None
        try:
            qs = Impresora.objects.filter(pk=impresora_id, activa=True)
            if empresa:
                qs = qs.filter(empresa=empresa)
            return qs.get()
        except Impresora.DoesNotExist:
            return None

    @staticmethod
    def _get_insumo(insumo_id, empresa):
        if not insumo_id:
            return None
        try:
            qs = Insumo.objects.select_related("material", "material__tipo").filter(pk=insumo_id)
            if empresa:
                qs = qs.filter(empresa=empresa)
            return qs.get()
        except Insumo.DoesNotExist:
            return None

    @classmethod
    def get_recursos(cls, user):
        empresa    = cls._get_empresa_from_user(user)
        is_super   = user and user.is_authenticated and getattr(user, 'is_superuser', False)
        if not empresa and not is_super:
            return {"impresoras": [], "insumos": [], "variables": None}

        imp_qs = Impresora.objects.filter(activa=True)
        ins_qs = Insumo.objects.select_related("material", "material__tipo")
        if empresa:
            imp_qs = imp_qs.filter(empresa=empresa)
            ins_qs = ins_qs.filter(empresa=empresa)

        impresoras = [
            {
                "id": imp.id,
                "nombre": imp.nombre,
                "tipo": imp.tipo,
                "costo": float(imp.costo),
                "vida_util_horas": imp.vida_util_horas,
                "costo_mantenimiento_anual": float(imp.costo_mantenimiento_anual),
            }
            for imp in imp_qs
        ]
        insumos = [
            {
                "id": ins.id,
                "producto": ins.producto,
                "material": str(ins.material) if ins.material else None,
                "precio": float(ins.precio) if ins.precio is not None else None,
                "cantidad_inicial": float(ins.cantidad_inicial),
                "stock_disponible": ins.stock_disponible,
            }
            for ins in ins_qs
        ]
        variables = None
        try:
            vf = cls._get_variables(empresa)
            variables = {
                "precio_rollo_filamento":    float(vf.precio_rollo_filamento),
                "peso_rollo_gramos":         float(vf.peso_rollo_gramos),
                "costo_electricidad_kwh":    float(vf.costo_electricidad_kwh),
                "consumo_impresora_kw":      float(vf.consumo_impresora_kw),
                "valor_hora_trabajo":        float(vf.valor_hora_trabajo),
                "margen_ganancia":           float(vf.margen_ganancia),
                "margen_fallos":             float(vf.margen_fallos),
                "costo_impresora":           float(vf.costo_impresora),
                "vida_util_horas":           vf.vida_util_horas,
                "costo_mantenimiento_anual": float(vf.costo_mantenimiento_anual),
                "costo_empaque_variable":    float(vf.costo_empaque),
            }
        except Exception:
            pass
        return {"impresoras": impresoras, "insumos": insumos, "variables": variables}

    @classmethod
    def cotizar_pieza(cls, datos: dict, user=None) -> dict:
        empresa   = cls._get_empresa_from_user(user)
        variables = cls._get_variables(empresa)
        impresora = cls._get_impresora(datos.get("impresora_id"), empresa)
        insumo    = cls._get_insumo(datos.get("insumo_id"), empresa)

        resultado = cotizar(
            nombre_pieza             = datos["nombre_pieza"],
            peso_gramos              = datos["peso_gramos"],
            tiempo_impresion_horas   = datos["tiempo_impresion_horas"],
            tiempo_postproceso_horas = datos.get("tiempo_postproceso_horas", 0),
            costo_empaque_override   = datos.get("costo_empaque_override", 0),
            variables                = variables,
            impresora                = impresora,
            insumo                   = insumo,
        )
        data = resultado.to_dict()
        if impresora:
            data["impresora_usada"] = {"id": impresora.id, "nombre": impresora.nombre, "tipo": impresora.tipo}
        if insumo:
            data["insumo_usado"] = {"id": insumo.id, "producto": insumo.producto,
                                    "material": str(insumo.material) if insumo.material else None}
        return data

    @classmethod
    def cotizar_lote(cls, datos: dict, user=None) -> dict:
        empresa   = cls._get_empresa_from_user(user)
        variables = cls._get_variables(empresa)
        impresora = cls._get_impresora(datos.get("impresora_id"), empresa)
        insumo    = cls._get_insumo(datos.get("insumo_id"), empresa)

        data = cotizar_por_cantidad(
            nombre_pieza             = datos["nombre_pieza"],
            peso_gramos              = datos["peso_gramos"],
            tiempo_impresion_horas   = datos["tiempo_impresion_horas"],
            cantidad                 = datos["cantidad"],
            tiempo_postproceso_horas = datos.get("tiempo_postproceso_horas", 0),
            costo_empaque_override   = datos.get("costo_empaque_override", 0),
            variables                = variables,
            impresora                = impresora,
            insumo                   = insumo,
        )
        if impresora:
            data["impresora_usada"] = {"id": impresora.id, "nombre": impresora.nombre, "tipo": impresora.tipo}
        if insumo:
            data["insumo_usado"] = {"id": insumo.id, "producto": insumo.producto,
                                    "material": str(insumo.material) if insumo.material else None}
        return data

    @classmethod
    def cotizar_desde_catalogo(cls, datos: dict, user=None) -> dict:
        empresa   = cls._get_empresa_from_user(user)
        variables = cls._get_variables(empresa)
        impresora = cls._get_impresora(datos.get("impresora_id"), empresa)
        insumo    = cls._get_insumo(datos.get("insumo_id"), empresa)

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
            impresora                = impresora,
            insumo                   = insumo,
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
        if impresora:
            data["impresora_usada"] = {"id": impresora.id, "nombre": impresora.nombre, "tipo": impresora.tipo}
        if insumo:
            data["insumo_usado"] = {"id": insumo.id, "producto": insumo.producto,
                                    "material": str(insumo.material) if insumo.material else None}
        return data

    @classmethod
    def cotizar_lote_desde_catalogo(cls, datos: dict, user=None) -> dict:
        empresa   = cls._get_empresa_from_user(user)
        variables = cls._get_variables(empresa)
        impresora = cls._get_impresora(datos.get("impresora_id"), empresa)
        insumo    = cls._get_insumo(datos.get("insumo_id"), empresa)

        try:
            pieza = InventarioPieza.objects.get(pk=datos["pieza_id"])
        except InventarioPieza.DoesNotExist:
            raise LookupError(f"Pieza con ID {datos['pieza_id']} no encontrada en el inventario.")

        data = cotizar_por_cantidad(
            nombre_pieza             = pieza.nombre,
            peso_gramos              = float(pieza.peso_gramos),
            tiempo_impresion_horas   = float(pieza.tiempo_impresion_horas),
            cantidad                 = datos["cantidad"],
            tiempo_postproceso_horas = datos.get("tiempo_postproceso_horas", 0),
            costo_empaque_override   = datos.get("costo_empaque_override", 0),
            variables                = variables,
            impresora                = impresora,
            insumo                   = insumo,
        )
        data["pieza_catalogo"] = {"id": pieza.id, "nombre": pieza.nombre}
        if impresora:
            data["impresora_usada"] = {"id": impresora.id, "nombre": impresora.nombre, "tipo": impresora.tipo}
        if insumo:
            data["insumo_usado"] = {"id": insumo.id, "producto": insumo.producto,
                                    "material": str(insumo.material) if insumo.material else None}
        return data
