from .cliente        import ClienteSerializer
from .impresora      import ImpresoraSerializer
from .insumo         import InsumoSerializer
from .gasto          import GastoSerializer
from .variables_fijas import VariablesFijasSerializer
from .inventario     import InventarioPiezaSerializer
from .pedido         import PedidoSerializer
from .venta          import VentaSerializer
from .tarea          import TareaSerializer
from .figura         import FiguraSerializer, FiguraImagenSerializer, FiguraPiezaSerializer
from .cotizador      import (
    CotizadorInputSerializer,
    CotizadorLoteInputSerializer,
    CotizadorDesdeCatalogoSerializer,
    CotizadorDesdeCatalogoLoteSerializer,
)
from .diseno3d       import (
    Diseno3DInputSerializer,
    Diseno3DEstadoSerializer,
    Diseno3DListSerializer,
)

__all__ = [
    "ClienteSerializer",
    "ImpresoraSerializer",
    "InsumoSerializer",
    "GastoSerializer",
    "VariablesFijasSerializer",
    "InventarioPiezaSerializer",
    "PedidoSerializer",
    "VentaSerializer",
    "TareaSerializer",
    "FiguraSerializer", "FiguraPiezaSerializer",
    "CotizadorInputSerializer",
    "CotizadorLoteInputSerializer",
    "CotizadorDesdeCatalogoSerializer",
    "CotizadorDesdeCatalogoLoteSerializer",
    "Diseno3DInputSerializer",
    "Diseno3DEstadoSerializer",
    "Diseno3DListSerializer",
]
