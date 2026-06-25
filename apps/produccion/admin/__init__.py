"""
admin/__init__.py
Registra todos los ModelAdmin importando los submódulos.
"""
from django.contrib import admin

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
from apps.produccion.admin.diseno3d  import Diseno3DAdmin                  # noqa: F401

# ── Orden personalizado del menú lateral ──────────────────────
_ORDEN_MODELOS = [
    "cliente",
    "impresora",
    "gasto",
    "insumo",
    "inventariopieza",
    "figura",
    "diseno3d",
    "pedido",
    "tarea",
    "venta",
]


def _get_app_list_ordenado(self, request, app_label=None):
    app_list = original_get_app_list(self, request, app_label)
    for app in app_list:
        app["models"].sort(
            key=lambda m: _ORDEN_MODELOS.index(m["object_name"].lower())
            if m["object_name"].lower() in _ORDEN_MODELOS
            else 99
        )
    return app_list


original_get_app_list = admin.AdminSite.get_app_list
admin.AdminSite.get_app_list = _get_app_list_ordenado
