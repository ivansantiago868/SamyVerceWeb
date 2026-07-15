# models/__init__.py
# Exporta todos los modelos para que Django los detecte
# y para que se puedan importar como: from apps.produccion.models import Cliente

from .empresa          import Empresa, PerfilUsuario
from .cliente          import Cliente
from .impresora        import Impresora
from .material         import TipoMaterial, Material
from .insumo           import Insumo
from .gasto            import Gasto
from .variables_fijas  import VariablesFijas
from .inventario_pieza import InventarioPieza, PiezaImagen
from .pedido           import Pedido, PedidoMaterial
from .venta_tarea      import Venta, Tarea
from .figura           import CategoriaFigura, Figura, FiguraImagen, FiguraPieza
from .diseno3d         import Diseno3D

__all__ = [
    "Empresa", "PerfilUsuario",
    "Cliente", "Impresora",
    "TipoMaterial", "Material",
    "Insumo", "Gasto",
    "VariablesFijas", "InventarioPieza", "PiezaImagen",
    "Pedido", "PedidoMaterial", "Venta", "Tarea",
    "CategoriaFigura", "Figura", "FiguraImagen", "FiguraPieza",
    "Diseno3D",
]
