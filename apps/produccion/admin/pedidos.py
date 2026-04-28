"""
admin/pedidos.py
Gestión de Pedidos y Tareas de producción.
"""
from decimal import Decimal

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db.models import F

from apps.produccion.models import Pedido, PedidoMaterial, Tarea
from apps.produccion.admin.mixins import EmpresaMixin


class PedidoMaterialInline(admin.TabularInline):
    model               = PedidoMaterial
    extra               = 0
    fields              = ("pieza", "material")
    readonly_fields     = ("pieza",)
    autocomplete_fields = ["material"]
    verbose_name        = "Material por pieza"
    verbose_name_plural = "Materiales por pieza (solo figuras)"
    can_delete          = False

    def has_add_permission(self, request, obj=None):
        return False  # Solo se crean por signal


class PedidoForm(forms.ModelForm):
    class Meta:
        model  = Pedido
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("figura"):
            raise ValidationError("Debes seleccionar una Figura.")
        return cleaned


@admin.register(Pedido)
class PedidoAdmin(EmpresaMixin, admin.ModelAdmin):
    form                = PedidoForm
    grupos_empresa      = {"Maker"}
    list_display        = ("id", "numero_pedido", "cliente", "figura",
                           "cantidad", "realizados", "restantes", "estado",
                           "fecha_entrega", "prioridad", "maquina")
    list_editable       = ("estado",)
    list_filter         = ("estado", "prioridad", "maquina")
    search_fields       = ("numero_pedido", "cliente__nombre", "figura__nombre", "descripcion")
    readonly_fields     = ("restantes", "realizados", "peso_total", "precio_total", "gr_pieza", "precio_unidad")
    autocomplete_fields = ["cliente", "figura"]
    inlines             = [PedidoMaterialInline]

    def get_inline_instances(self, request, obj=None):
        inlines = super().get_inline_instances(request, obj)
        # Solo mostrar el inline de materiales si el pedido ya tiene figura guardada
        if obj is None or not obj.figura_id:
            return [i for i in inlines if not isinstance(i, PedidoMaterialInline)]
        return inlines

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
