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
    FiguraView, FiguraPiezaView,
    # Cotizador
    CotizadorRecursosView,
    CotizadorView, CotizadorLoteView,
    CotizadorDesdeCatalogoView, CotizadorDesdeCatalogoLoteView,
    # Diseño 3D
    Diseno3DCrearView, Diseno3DListView, Diseno3DDetalleView,
    # Carrito
    CarritoCheckoutView,
    # Portal del cliente
    ClienteLoginView, ClienteLogoutView, ClienteMeView, ClienteMisPedidosView,
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
router.register(r"figuras",         FiguraView,          basename="figura")
router.register(r"figura-piezas",   FiguraPiezaView,     basename="figura-pieza")

# ── Cotizador ─────────────────────────────────────────────────────
cotizador_urls = [
    path("cotizador/recursos/",             CotizadorRecursosView.as_view(),          name="cotizador-recursos"),
    path("cotizador/",                     CotizadorView.as_view(),                  name="cotizador"),
    path("cotizador/lote/",                CotizadorLoteView.as_view(),              name="cotizador-lote"),
    path("cotizador/desde-catalogo/",      CotizadorDesdeCatalogoView.as_view(),     name="cotizador-catalogo"),
    path("cotizador/desde-catalogo/lote/", CotizadorDesdeCatalogoLoteView.as_view(), name="cotizador-catalogo-lote"),
]

# ── Diseño 3D ─────────────────────────────────────────────────────
diseno3d_urls = [
    path("diseno3d/",          Diseno3DCrearView.as_view(),   name="diseno3d-crear"),
    path("diseno3d/lista/",    Diseno3DListView.as_view(),    name="diseno3d-lista"),
    path("diseno3d/<int:pk>/", Diseno3DDetalleView.as_view(), name="diseno3d-detalle"),
]

# ── Carrito ───────────────────────────────────────────────────────
carrito_urls = [
    path("carrito/checkout/", CarritoCheckoutView.as_view(), name="carrito-checkout"),
]

# ── Portal del cliente ────────────────────────────────────────────
# Prefijo propio (no "clientes/...") para no chocar con la ruta de detalle
# del router (clientes/<pk>/), que capturaría "login"/"me" como si fueran un pk.
cliente_portal_urls = [
    path("portal-cliente/login/",       ClienteLoginView.as_view(),      name="cliente-login"),
    path("portal-cliente/logout/",      ClienteLogoutView.as_view(),     name="cliente-logout"),
    path("portal-cliente/me/",          ClienteMeView.as_view(),         name="cliente-me"),
    path("portal-cliente/mis-pedidos/", ClienteMisPedidosView.as_view(), name="cliente-mis-pedidos"),
]

urlpatterns = router.urls + cotizador_urls + diseno3d_urls + carrito_urls + cliente_portal_urls
