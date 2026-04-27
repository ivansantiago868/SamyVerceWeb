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
)
from .cotizador_view import (
    CotizadorRecursosView,
    CotizadorView,
    CotizadorLoteView,
    CotizadorDesdeCatalogoView,
    CotizadorDesdeCatalogoLoteView,
)

__all__ = [
    "ClienteView", "ImpresoraView", "InsumoView", "GastoView",
    "VariablesFijasView", "InventarioPiezaView", "PedidoView", "VentaView", "TareaView",
    "CotizadorRecursosView", "CotizadorView", "CotizadorLoteView",
    "CotizadorDesdeCatalogoView", "CotizadorDesdeCatalogoLoteView",
]
