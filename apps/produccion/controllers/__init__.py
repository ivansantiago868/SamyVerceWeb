# controllers/__init__.py
from .cliente_controller        import ClienteSerializer,        ClienteController
from .impresora_controller      import ImpresoraSerializer,      ImpresoraController
from .insumo_controller         import InsumoSerializer,         InsumoController
from .gasto_controller          import GastoSerializer,          GastoController
from .variables_fijas_controller import VariablesFijasSerializer, VariablesFijasController
from .inventario_controller     import InventarioPiezaSerializer, InventarioController
from .pedido_controller         import PedidoSerializer,         PedidoController
from .venta_controller          import VentaSerializer,          VentaController
from .tarea_controller          import TareaSerializer,          TareaController
from .cotizador_controller      import (
    CotizadorInputSerializer,
    CotizadorLoteInputSerializer,
    CotizadorDesdeCatalogoSerializer,
    CotizadorDesdeCatalogoLoteSerializer,
    CotizadorController,
)

__all__ = [
    "ClienteSerializer",         "ClienteController",
    "ImpresoraSerializer",       "ImpresoraController",
    "InsumoSerializer",          "InsumoController",
    "GastoSerializer",           "GastoController",
    "VariablesFijasSerializer",  "VariablesFijasController",
    "InventarioPiezaSerializer", "InventarioController",
    "PedidoSerializer",          "PedidoController",
    "VentaSerializer",           "VentaController",
    "TareaSerializer",           "TareaController",
    "CotizadorInputSerializer",
    "CotizadorLoteInputSerializer",
    "CotizadorDesdeCatalogoSerializer",
    "CotizadorDesdeCatalogoLoteSerializer",
    "CotizadorController",
]
