# models/__init__.py
# Exporta todos los modelos para que Django los detecte
# y para que se puedan importar como: from apps.produccion.models import Cliente

from .cliente          import Cliente
from .impresora        import Impresora
from .material         import TipoMaterial, Material
from .insumo           import Insumo
from .gasto            import Gasto
from .variables_fijas  import VariablesFijas
from .inventario_pieza import InventarioPieza, PiezaImagen
from .pedido           import Pedido
from .venta_tarea      import Venta, Tarea

__all__ = [
    "Cliente", "Impresora",
    "TipoMaterial", "Material",
    "Insumo", "Gasto",
    "VariablesFijas", "InventarioPieza", "PiezaImagen",
    "Pedido", "Venta", "Tarea",
]
