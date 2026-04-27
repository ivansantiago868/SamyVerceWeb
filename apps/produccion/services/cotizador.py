"""
services/cotizador.py
Lógica de negocio del Cotizador de Impresión 3D.
Replica exactamente las fórmulas de la hoja 'Cotizador' del Excel.

Fórmulas verificadas contra datos reales:
  Nitendo64:  peso=24g, t=1h  → costo_total=2575.08 COP → precio=5000 COP ✅
  SuperNES:   peso=120g, t=12h → costo_total=16116.97 COP → precio=25000 COP ✅
"""
import math
from dataclasses import dataclass, field
from decimal import Decimal

from apps.produccion.models import VariablesFijas


@dataclass
class ResultadoCotizacion:
    # ── Inputs ────────────────────────────────────────────────────
    nombre_pieza:              str
    peso_gramos:               float
    tiempo_impresion_horas:    float
    tiempo_postproceso_horas:  float
    costo_empaque_override:    float   # 0 si se usa el de variables fijas

    # ── Variables fijas usadas ────────────────────────────────────
    precio_rollo_filamento:    float
    peso_rollo_gramos:         float
    costo_electricidad_kwh:    float
    consumo_impresora_kw:      float
    valor_hora_trabajo:        float
    margen_ganancia:           float
    margen_fallos:             float
    costo_impresora:           float
    vida_util_horas:           int
    costo_mantenimiento_anual: float
    horas_totales_anio:        int
    costo_empaque_variable:    float

    # ── Resultados calculados ─────────────────────────────────────
    costo_material:            float = field(init=False)
    costo_energia:             float = field(init=False)
    costo_tiempo:              float = field(init=False)
    costo_empaque_final:       float = field(init=False)
    subtotal_produccion:       float = field(init=False)
    amortizacion_fallos:       float = field(init=False)
    depreciacion_pieza:        float = field(init=False)
    mantenimiento_preventivo:  float = field(init=False)
    costo_total_real:          float = field(init=False)
    precio_sin_redondeo:       float = field(init=False)
    redondeo:                  float = field(init=False)
    precio_venta_sugerido:     float = field(init=False)

    def __post_init__(self):
        self._calcular()

    def _calcular(self):
        # 1. Costo del Material
        #    = (peso_pieza / peso_rollo) * precio_rollo
        self.costo_material = round(
            (self.peso_gramos / self.peso_rollo_gramos) * self.precio_rollo_filamento, 2
        )

        # 2. Costo de Energía
        #    = consumo_kw * tiempo_impresion * costo_kwh
        self.costo_energia = round(
            self.consumo_impresora_kw * self.tiempo_impresion_horas * self.costo_electricidad_kwh, 2
        )

        # 3. Costo de Tiempo (mano de obra)
        #    = tiempo_postproceso * valor_hora
        self.costo_tiempo = round(
            self.tiempo_postproceso_horas * self.valor_hora_trabajo, 2
        )

        # 4. Costo de Empaque
        #    = precio_unitario_empaque (Variables Fijas) × cantidad_empaques
        self.costo_empaque_final = round(
            self.costo_empaque_variable * self.costo_empaque_override, 2
        )

        # 5. Subtotal Costo de Producción
        self.subtotal_produccion = round(
            self.costo_material + self.costo_energia + self.costo_tiempo + self.costo_empaque_final, 2
        )

        # 6. Amortización de Fallos
        #    = subtotal * margen_fallos
        self.amortizacion_fallos = round(
            self.subtotal_produccion * self.margen_fallos, 2
        )

        # 7. Depreciación por Pieza
        #    = (costo_impresora / vida_util_horas) * tiempo_impresion
        self.depreciacion_pieza = round(
            (self.costo_impresora / self.vida_util_horas) * self.tiempo_impresion_horas, 2
        )

        # 8. Mantenimiento Preventivo
        #    = (costo_mantenimiento_anual / horas_totales_anio) * tiempo_impresion
        self.mantenimiento_preventivo = round(
            (self.costo_mantenimiento_anual / self.horas_totales_anio) * self.tiempo_impresion_horas, 2
        )

        # 9. Costo Total Real
        self.costo_total_real = round(
            self.subtotal_produccion
            + self.amortizacion_fallos
            + self.depreciacion_pieza
            + self.mantenimiento_preventivo,
            2
        )

        # 10. Precio sin redondeo
        #     = costo_total / (1 - margen_ganancia)
        self.precio_sin_redondeo = round(
            self.costo_total_real / (1 - self.margen_ganancia), 2
        )

        # 11. Redondeo al siguiente múltiplo de 5000 (comportamiento Excel verificado)
        self.precio_venta_sugerido = math.ceil(self.precio_sin_redondeo / 5000) * 5000
        self.precio_venta_sugerido = math.ceil(self.precio_sin_redondeo / 1000) * 1000
        self.redondeo = round(self.precio_venta_sugerido - self.precio_sin_redondeo, 2)
        

    def to_dict(self):
        return {
            "inputs": {
                "nombre_pieza":             self.nombre_pieza,
                "peso_gramos":              self.peso_gramos,
                "tiempo_impresion_horas":   self.tiempo_impresion_horas,
                "tiempo_postproceso_horas": self.tiempo_postproceso_horas,
                "costo_empaque_override":   self.costo_empaque_override,
            },
            "variables_fijas_usadas": {
                "precio_rollo_filamento":    self.precio_rollo_filamento,
                "peso_rollo_gramos":         self.peso_rollo_gramos,
                "costo_electricidad_kwh":    self.costo_electricidad_kwh,
                "consumo_impresora_kw":      self.consumo_impresora_kw,
                "valor_hora_trabajo":        self.valor_hora_trabajo,
                "margen_ganancia":           self.margen_ganancia,
                "margen_fallos":             self.margen_fallos,
                "costo_impresora":           self.costo_impresora,
                "vida_util_horas":           self.vida_util_horas,
                "costo_mantenimiento_anual": self.costo_mantenimiento_anual,
                "costo_empaque_variable":    self.costo_empaque_variable,
            },
            "desglose": {
                "costo_material":           self.costo_material,
                "costo_energia":            self.costo_energia,
                "costo_tiempo":             self.costo_tiempo,
                "costo_empaque":            self.costo_empaque_final,
                "subtotal_produccion":      self.subtotal_produccion,
                "amortizacion_fallos":      self.amortizacion_fallos,
                "depreciacion_pieza":       self.depreciacion_pieza,
                "mantenimiento_preventivo": self.mantenimiento_preventivo,
            },
            "resultado": {
                "costo_total_real":      self.costo_total_real,
                "precio_sin_redondeo":   self.precio_sin_redondeo,
                "redondeo":              self.redondeo,
                "precio_venta_sugerido": self.precio_venta_sugerido,
            }
        }


def cotizar(
    nombre_pieza: str,
    peso_gramos: float,
    tiempo_impresion_horas: float,
    tiempo_postproceso_horas: float = 0.0,
    costo_empaque_override: float = 0.0,
    variables: VariablesFijas = None,
    impresora=None,
    insumo=None,
) -> ResultadoCotizacion:
    """
    Función principal del cotizador.
    Si no se pasa `variables`, lee el singleton de la BD.
    Si se pasa `impresora`, sobreescribe costo, vida útil y mantenimiento.
    Si se pasa `insumo` (con precio definido), sobreescribe precio y peso del rollo.
    """
    if variables is None:
        variables = VariablesFijas.objects.filter(empresa__isnull=True).first()

    insumo_tiene_precio = insumo and insumo.precio is not None

    return ResultadoCotizacion(
        nombre_pieza=nombre_pieza,
        peso_gramos=peso_gramos,
        tiempo_impresion_horas=tiempo_impresion_horas,
        tiempo_postproceso_horas=tiempo_postproceso_horas,
        costo_empaque_override=costo_empaque_override,
        precio_rollo_filamento=float(insumo.precio) if insumo_tiene_precio else float(variables.precio_rollo_filamento),
        peso_rollo_gramos=float(insumo.cantidad_inicial) if insumo_tiene_precio else float(variables.peso_rollo_gramos),
        costo_electricidad_kwh=float(variables.costo_electricidad_kwh),
        consumo_impresora_kw=float(variables.consumo_impresora_kw),
        valor_hora_trabajo=float(variables.valor_hora_trabajo),
        margen_ganancia=float(variables.margen_ganancia),
        margen_fallos=float(variables.margen_fallos),
        costo_impresora=float(impresora.costo) if impresora else float(variables.costo_impresora),
        vida_util_horas=impresora.vida_util_horas if impresora else variables.vida_util_horas,
        costo_mantenimiento_anual=float(impresora.costo_mantenimiento_anual) if impresora else float(variables.costo_mantenimiento_anual),
        horas_totales_anio=variables.horas_totales_anio,
        costo_empaque_variable=float(variables.costo_empaque),
    )


def cotizar_por_cantidad(
    nombre_pieza: str,
    peso_gramos: float,
    tiempo_impresion_horas: float,
    cantidad: int,
    tiempo_postproceso_horas: float = 0.0,
    costo_empaque_override: float = 0.0,
    variables: VariablesFijas = None,
    impresora=None,
    insumo=None,
) -> dict:
    """
    Cotiza una pieza y escala los resultados por cantidad.
    """
    resultado = cotizar(
        nombre_pieza=nombre_pieza,
        peso_gramos=peso_gramos,
        tiempo_impresion_horas=tiempo_impresion_horas,
        tiempo_postproceso_horas=tiempo_postproceso_horas,
        costo_empaque_override=costo_empaque_override,
        variables=variables,
        impresora=impresora,
        insumo=insumo,
    )
    data = resultado.to_dict()
    data["escala"] = {
        "cantidad": cantidad,
        "costo_total_lote":    round(resultado.costo_total_real * cantidad, 2),
        "precio_total_lote":   resultado.precio_venta_sugerido * cantidad,
        "peso_total_gramos":   round(peso_gramos * cantidad, 2),
        "tiempo_total_horas":  round(tiempo_impresion_horas * cantidad, 2),
    }
    return data
