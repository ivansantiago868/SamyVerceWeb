"""
admin/__init__.py
Registra todos los ModelAdmin importando los submódulos.
"""
from apps.produccion.admin.empresa   import EmpresaAdmin, UsuarioAdmin   # noqa: F401
from apps.produccion.admin.recursos  import (                              # noqa: F401
    ClienteAdmin, ImpresoraAdmin,
    TipoMaterialAdmin, MaterialAdmin,
    InsumoAdmin, GastoAdmin,
)
from apps.produccion.admin.produccion import (                             # noqa: F401
    VariablesFijasAdmin, InventarioPiezaAdmin,
)
from apps.produccion.admin.pedidos   import PedidoAdmin, TareaAdmin       # noqa: F401
from apps.produccion.admin.ventas    import VentaAdmin                    # noqa: F401
from apps.produccion.admin.figura    import FiguraAdmin                    # noqa: F401
