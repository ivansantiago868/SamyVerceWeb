"""
urls.py
Todas las rutas de la app produccion.
Los ViewSets van al Router (CRUD automático).
Las APIViews del Cotizador van a path() individuales.
"""
from rest_framework.routers import DefaultRouter
from django.urls import path

from apps.produccion.views import (
    # Recursos
    ClienteView, ImpresoraView, InsumoView, GastoView,
    VariablesFijasView, InventarioPiezaView,
    PedidoView, VentaView, TareaView,
    # Cotizador
    CotizadorRecursosView,
    CotizadorView, CotizadorLoteView,
    CotizadorDesdeCatalogoView, CotizadorDesdeCatalogoLoteView,
)

# ── CRUD automático vía Router ────────────────────────────────────
router = DefaultRouter()
router.register(r"clientes",        ClienteView,         basename="cliente")
router.register(r"impresoras",      ImpresoraView,       basename="impresora")
router.register(r"insumos",         InsumoView,          basename="insumo")
router.register(r"gastos",          GastoView,           basename="gasto")
router.register(r"variables-fijas", VariablesFijasView,  basename="variables-fijas")
router.register(r"piezas",          InventarioPiezaView, basename="pieza")
router.register(r"pedidos",         PedidoView,          basename="pedido")
router.register(r"ventas",          VentaView,           basename="venta")
router.register(r"tareas",          TareaView,           basename="tarea")

# ── Cotizador ─────────────────────────────────────────────────────
cotizador_urls = [
    path("cotizador/recursos/",             CotizadorRecursosView.as_view(),          name="cotizador-recursos"),
    path("cotizador/",                     CotizadorView.as_view(),                  name="cotizador"),
    path("cotizador/lote/",                CotizadorLoteView.as_view(),              name="cotizador-lote"),
    path("cotizador/desde-catalogo/",      CotizadorDesdeCatalogoView.as_view(),     name="cotizador-catalogo"),
    path("cotizador/desde-catalogo/lote/", CotizadorDesdeCatalogoLoteView.as_view(), name="cotizador-catalogo-lote"),
]

urlpatterns = router.urls + cotizador_urls
