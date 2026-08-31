"""
controllers/carrito_controller.py
Checkout público del catálogo (sin pago): crea el Cliente, un Pedido por
cada producto del carrito (lo que ya dispara la creación automática de
Tareas vía signals.crear_tarea_desde_pedido) y la Venta que los agrupa.
"""
from django.db import transaction
from django.utils import timezone

from apps.produccion.models import Cliente, Figura, FiguraColor, FiguraTipo, Pedido, Venta


class CarritoError(Exception):
    """Error de validación de negocio (figura inexistente, color/tipo que
    no pertenece a la figura elegida, etc.)."""


class CarritoController:

    @staticmethod
    def _generar_numero_pedido():
        return f"WEB-{timezone.now():%Y%m%d%H%M%S}"

    @staticmethod
    @transaction.atomic
    def confirmar_pedido(nombre_recibe: str, direccion: str, items: list, cliente_id: int = None) -> dict:
        figura_ids = [it["figura_id"] for it in items]
        figuras_por_id = {f.id: f for f in Figura.objects.filter(pk__in=figura_ids).select_related("empresa")}

        faltantes = set(figura_ids) - set(figuras_por_id)
        if faltantes:
            raise CarritoError(f"Producto(s) no encontrado(s): {sorted(faltantes)}")

        empresa = next(iter(figuras_por_id.values())).empresa

        if cliente_id:
            # Cliente logueado en el portal: el pedido se suma a su historial
            # en vez de crear un registro nuevo y desconectado cada vez. No se
            # filtra por empresa porque cliente_id nunca llega desde el
            # navegador — sale de request.session, ya autenticado por
            # documento+contraseña en ClienteLoginView.
            cliente = Cliente.objects.filter(pk=cliente_id).first()
            if not cliente:
                raise CarritoError("Cliente no válido.")
        else:
            cliente = Cliente.objects.create(
                empresa=empresa,
                nombre=nombre_recibe,
                direccion=direccion,
            )

        numero_pedido = CarritoController._generar_numero_pedido()
        pedidos = []
        for it in items:
            figura = figuras_por_id[it["figura_id"]]

            color = None
            if it.get("color_id"):
                color = FiguraColor.objects.filter(pk=it["color_id"], figura=figura).first()
                if not color:
                    raise CarritoError(f"El color elegido no pertenece a «{figura.nombre}».")

            tipo = None
            if it.get("tipo_id"):
                tipo = FiguraTipo.objects.filter(pk=it["tipo_id"], figura=figura).first()
                if not tipo:
                    raise CarritoError(f"El tipo elegido no pertenece a «{figura.nombre}».")

            pedido = Pedido.objects.create(
                empresa=empresa,
                numero_pedido=numero_pedido,
                cliente=cliente,
                figura=figura,
                color=color,
                tipo=tipo,
                cantidad=it["cantidad"],
                descripcion="Pedido realizado desde el catálogo web.",
                nombre_recibe=nombre_recibe,
                direccion_entrega=direccion,
            )
            pedidos.append(pedido)

        venta = Venta.objects.create(empresa=empresa, fecha=timezone.now().date())
        venta.pedidos.set(pedidos)

        return {
            "numero_pedido": numero_pedido,
            "venta_id": venta.id,
            "total": sum(p.precio_total for p in pedidos),
        }
