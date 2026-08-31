# views/__init__.py
from .recursos_view import (
    ClienteView,
    ImpresoraView,
    InsumoView,
    GastoView,
)
from .produccion_view import (
    VariablesFijasView,
    InventarioPiezaView,
    PedidoView,
    VentaView,
    TareaView,
    FiguraView,
    FiguraPiezaView,
)
from .cotizador_view import (
    CotizadorRecursosView,
    CotizadorView,
    CotizadorLoteView,
    CotizadorDesdeCatalogoView,
    CotizadorDesdeCatalogoLoteView,
)
from .diseno3d_view import (
    Diseno3DCrearView,
    Diseno3DListView,
    Diseno3DDetalleView,
)
from .carrito_view import CarritoCheckoutView
from .cliente_portal_view import (
    ClienteLoginView,
    ClienteLogoutView,
    ClienteMeView,
    ClienteMisPedidosView,
)

__all__ = [
    "ClienteView", "ImpresoraView", "InsumoView", "GastoView",
    "VariablesFijasView", "InventarioPiezaView", "PedidoView", "VentaView", "TareaView",
    "FiguraView", "FiguraPiezaView",
    "CotizadorRecursosView", "CotizadorView", "CotizadorLoteView",
    "CotizadorDesdeCatalogoView", "CotizadorDesdeCatalogoLoteView",
    "Diseno3DCrearView", "Diseno3DListView", "Diseno3DDetalleView",
    "CarritoCheckoutView",
    "ClienteLoginView", "ClienteLogoutView", "ClienteMeView", "ClienteMisPedidosView",
]
