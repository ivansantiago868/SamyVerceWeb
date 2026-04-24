# controllers/__init__.py — re-exporta desde serializers/ y services/
from apps.produccion.serializers import (
    ClienteSerializer, ImpresoraSerializer, InsumoSerializer,
    GastoSerializer, VariablesFijasSerializer, InventarioPiezaSerializer,
    PedidoSerializer, VentaSerializer, TareaSerializer,
    CotizadorInputSerializer, CotizadorLoteInputSerializer,
    CotizadorDesdeCatalogoSerializer, CotizadorDesdeCatalogoLoteSerializer,
)
from apps.produccion.services import (
    ClienteService    as ClienteController,
    ImpresoraService  as ImpresoraController,
    InsumoService     as InsumoController,
    GastoService      as GastoController,
    PedidoService     as PedidoController,
    VentaService      as VentaController,
    TareaService      as TareaController,
)
from apps.produccion.controllers.cotizador_controller      import CotizadorController
from apps.produccion.controllers.variables_fijas_controller import VariablesFijasController

InventarioController = InventarioPiezaSerializer.__class__  # alias placeholder

__all__ = [
    "ClienteSerializer",         "ClienteController",
    "ImpresoraSerializer",       "ImpresoraController",
    "InsumoSerializer",          "InsumoController",
    "GastoSerializer",           "GastoController",
    "VariablesFijasSerializer",  "VariablesFijasController",
    "InventarioPiezaSerializer",
    "PedidoSerializer",          "PedidoController",
    "VentaSerializer",           "VentaController",
    "TareaSerializer",           "TareaController",
    "CotizadorInputSerializer", "CotizadorLoteInputSerializer",
    "CotizadorDesdeCatalogoSerializer", "CotizadorDesdeCatalogoLoteSerializer",
    "CotizadorController",
]
