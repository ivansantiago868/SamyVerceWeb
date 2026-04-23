"""
tests/test_cotizador.py
Pruebas unitarias del servicio Cotizador.
Verifica las fórmulas contra los valores reales del Excel.
"""
from unittest.mock import MagicMock
from django.test import TestCase
from apps.produccion.services.cotizador import cotizar, cotizar_por_cantidad


def _mock_variables():
    """Crea un mock de VariablesFijas con los valores del Excel."""
    v = MagicMock()
    v.precio_rollo_filamento    = 80000
    v.peso_rollo_gramos         = 1000
    v.costo_electricidad_kwh    = 850
    v.consumo_impresora_kw      = 0.15
    v.valor_hora_trabajo        = 25000
    v.margen_ganancia           = 0.35
    v.margen_fallos             = 0.10
    v.costo_impresora           = 1500000
    v.vida_util_horas           = 5000
    v.costo_mantenimiento_anual = 200000
    v.horas_totales_anio        = 8760
    v.costo_empaque             = 1500
    return v


class CotizadorFormulasTest(TestCase):
    """Verifica cada fórmula contra los datos reales del Excel."""

    def setUp(self):
        self.vars = _mock_variables()

    # ── Nitendo64 (peso=24g, tiempo=1h) ──────────────────────────
    def test_nitendo64_costo_material(self):
        r = cotizar("Nitendo64", 24, 1.0, variables=self.vars)
        self.assertEqual(r.costo_material, 1920.0)

    def test_nitendo64_costo_energia(self):
        r = cotizar("Nitendo64", 24, 1.0, variables=self.vars)
        self.assertEqual(r.costo_energia, 127.5)

    def test_nitendo64_subtotal(self):
        r = cotizar("Nitendo64", 24, 1.0, variables=self.vars)
        # Con empaque de variables fijas (1500)
        self.assertEqual(r.subtotal_produccion, 2047.5 + 1500 + 25000)

    def test_nitendo64_subtotal_sin_empaque_sin_tiempo(self):
        """Replica exacta del Excel: t_post=0, empaque_override=0, valor_hora usa VF."""
        # El Excel muestra subtotal=2047.5 (sin empaque ni tiempo de trabajo)
        # Esto ocurre cuando el usuario pone valor_hora=0 en su cotizador.
        # Aquí testeamos con valor_hora=0 explícitamente
        v = _mock_variables()
        v.valor_hora_trabajo = 0
        v.costo_empaque = 0
        r = cotizar("Nitendo64", 24, 1.0, 0.0, 0.0, variables=v)
        self.assertEqual(r.subtotal_produccion, 2047.5)

    def test_nitendo64_amortizacion(self):
        v = _mock_variables(); v.valor_hora_trabajo = 0; v.costo_empaque = 0
        r = cotizar("Nitendo64", 24, 1.0, variables=v)
        self.assertEqual(r.amortizacion_fallos, 204.75)

    def test_nitendo64_depreciacion(self):
        v = _mock_variables(); v.valor_hora_trabajo = 0; v.costo_empaque = 0
        r = cotizar("Nitendo64", 24, 1.0, variables=v)
        self.assertEqual(r.depreciacion_pieza, 300.0)

    def test_nitendo64_mantenimiento(self):
        v = _mock_variables(); v.valor_hora_trabajo = 0; v.costo_empaque = 0
        r = cotizar("Nitendo64", 24, 1.0, variables=v)
        self.assertEqual(r.mantenimiento_preventivo, 22.83)

    def test_nitendo64_costo_total(self):
        v = _mock_variables(); v.valor_hora_trabajo = 0; v.costo_empaque = 0
        r = cotizar("Nitendo64", 24, 1.0, variables=v)
        self.assertEqual(r.costo_total_real, 2575.08)

    def test_nitendo64_precio_venta(self):
        v = _mock_variables(); v.valor_hora_trabajo = 0; v.costo_empaque = 0
        r = cotizar("Nitendo64", 24, 1.0, variables=v)
        self.assertEqual(r.precio_venta_sugerido, 5000)  # ✅ coincide con Excel

    # ── SuperNES (peso=120g, tiempo=12h) ─────────────────────────
    def test_supernes_costo_material(self):
        v = _mock_variables(); v.valor_hora_trabajo = 0; v.costo_empaque = 0
        r = cotizar("SuperNES", 120, 12.0, variables=v)
        self.assertEqual(r.costo_material, 9600.0)

    def test_supernes_costo_energia(self):
        v = _mock_variables(); v.valor_hora_trabajo = 0; v.costo_empaque = 0
        r = cotizar("SuperNES", 120, 12.0, variables=v)
        self.assertEqual(r.costo_energia, 1530.0)

    def test_supernes_costo_total(self):
        v = _mock_variables(); v.valor_hora_trabajo = 0; v.costo_empaque = 0
        r = cotizar("SuperNES", 120, 12.0, variables=v)
        self.assertEqual(r.costo_total_real, 16116.97)

    def test_supernes_precio_venta(self):
        v = _mock_variables(); v.valor_hora_trabajo = 0; v.costo_empaque = 0
        r = cotizar("SuperNES", 120, 12.0, variables=v)
        self.assertEqual(r.precio_venta_sugerido, 25000)  # ✅ coincide con Excel

    # ── Cotización por lote ───────────────────────────────────────
    def test_lote_escala_correctamente(self):
        v = _mock_variables(); v.valor_hora_trabajo = 0; v.costo_empaque = 0
        resultado = cotizar_por_cantidad("Nitendo64", 24, 1.0, 15, variables=v)
        self.assertEqual(resultado["escala"]["cantidad"], 15)
        self.assertEqual(resultado["escala"]["precio_total_lote"], 5000 * 15)
        self.assertAlmostEqual(resultado["escala"]["costo_total_lote"], 2575.08 * 15, places=1)
        self.assertEqual(resultado["escala"]["peso_total_gramos"], 24 * 15)

    # ── Validaciones de estructura ────────────────────────────────
    def test_resultado_tiene_todas_las_secciones(self):
        r = cotizar("Test", 50, 2.0, variables=self.vars)
        data = r.to_dict()
        self.assertIn("inputs",               data)
        self.assertIn("variables_fijas_usadas", data)
        self.assertIn("desglose",             data)
        self.assertIn("resultado",            data)

    def test_desglose_tiene_todos_los_campos(self):
        r = cotizar("Test", 50, 2.0, variables=self.vars)
        desglose = r.to_dict()["desglose"]
        for campo in ["costo_material", "costo_energia", "costo_tiempo",
                      "costo_empaque", "subtotal_produccion", "amortizacion_fallos",
                      "depreciacion_pieza", "mantenimiento_preventivo"]:
            self.assertIn(campo, desglose)

    def test_precio_siempre_multiplo_de_5000(self):
        v = _mock_variables(); v.valor_hora_trabajo = 0; v.costo_empaque = 0
        for peso in [10, 50, 75, 200, 500]:
            r = cotizar(f"Pieza_{peso}g", peso, 1.0, variables=v)
            self.assertEqual(r.precio_venta_sugerido % 5000, 0,
                             f"Precio {r.precio_venta_sugerido} no es múltiplo de 5000 para peso={peso}g")
