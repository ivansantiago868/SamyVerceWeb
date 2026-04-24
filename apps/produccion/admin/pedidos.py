"""
admin/pedidos.py
Gestión de Pedidos y Tareas de producción.
"""
from decimal import Decimal

from django.contrib import admin
from django.db.models import F

from apps.produccion.models import Pedido, Tarea
from apps.produccion.admin.mixins import EmpresaMixin


@admin.register(Pedido)
class PedidoAdmin(EmpresaMixin, admin.ModelAdmin):
    grupos_empresa      = {"Maker"}
    list_display        = ("id", "numero_pedido", "cliente", "pieza",
                           "cantidad", "realizados", "restantes", "estado",
                           "fecha_entrega", "prioridad", "maquina")
    list_editable       = ("estado",)
    list_filter         = ("estado", "prioridad", "maquina")
    search_fields       = ("numero_pedido", "cliente__nombre", "pieza__nombre", "descripcion")
    readonly_fields     = ("restantes", "realizados", "peso_total", "precio_total", "gr_pieza", "precio_unidad")
    autocomplete_fields = ["cliente", "material", "pieza"]

    def save_model(self, request, obj, form, change):
        if change:
            anterior_estado = Pedido.objects.values_list("estado", flat=True).get(pk=obj.pk)
            super().save_model(request, obj, form, change)
            if obj.estado != anterior_estado:
                Tarea.objects.filter(pedido=obj).update(estado=obj.estado)
        else:
            super().save_model(request, obj, form, change)

    class Media:
        js = ("admin/js/pedido_producto.js",)


@admin.register(Tarea)
class TareaAdmin(EmpresaMixin, admin.ModelAdmin):
    grupos_empresa      = {"Maker"}
    list_display        = ("id", "prioridad", "cliente", "producto",
                           "cantidad", "realizados", "restantes", "fecha_entrega", "maquina", "estado")
    list_editable       = ("realizados", "estado")
    list_filter         = ("estado", "prioridad", "maquina")
    search_fields       = ("producto", "cliente_texto", "cliente__nombre")
    readonly_fields     = ("restantes",)
    autocomplete_fields = ["cliente"]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return (
                "restantes", "prioridad", "pedido", "cliente", "cliente_texto",
                "producto", "cantidad", "precio_total", "fecha_entrega",
                "maquina", "descripcion", "creado_en",
            )
        return ("restantes",)

    def save_model(self, request, obj, form, change):
        if change and obj.pedido_id:
            anterior = Tarea.objects.values("estado", "realizados").get(pk=obj.pk)
            super().save_model(request, obj, form, change)
            if obj.estado != anterior["estado"]:
                Pedido.objects.filter(pk=obj.pedido_id).update(estado=obj.estado)
            delta = obj.realizados - anterior["realizados"]
            if delta > 0:
                Pedido.objects.filter(pk=obj.pedido_id).update(realizados=F("realizados") + delta)
                pedido = Pedido.objects.select_related("material").get(pk=obj.pedido_id)
                if pedido.material_id and pedido.gr_pieza:
                    insumo = pedido.material
                    insumo.cantidad_inicial += Decimal(delta) * pedido.gr_pieza
                    insumo.save()
        else:
            super().save_model(request, obj, form, change)

    def has_add_permission(self, _request):
        return False
