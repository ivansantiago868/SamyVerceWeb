from django import forms
from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
import datetime

from apps.produccion.models import (
    Cliente, Impresora, TipoMaterial, Material,
    Insumo, Gasto,
    VariablesFijas, InventarioPieza,
    Pedido, Venta, Tarea,
)


class DragDropFileWidget(forms.ClearableFileInput):
    template_name = "admin/widgets/drag_drop_file.html"

    class Media:
        css = {"all": ("admin/css/drag_drop_file.css",)}
        js  = ("admin/js/drag_drop_file.js",)


class DragDropImageWidget(forms.ClearableFileInput):
    template_name = "admin/widgets/drag_drop_image.html"

    class Media:
        css = {"all": ("admin/css/drag_drop_file.css",)}
        js  = ("admin/js/drag_drop_file.js",)


class InventarioPiezaForm(forms.ModelForm):
    class Meta:
        model   = InventarioPieza
        fields  = "__all__"
        widgets = {
            "archivo_3mf": DragDropFileWidget(),
            "imagen":      DragDropImageWidget(),
        }


class GastoMultipleForm(forms.Form):
    from apps.produccion.models.material import Material as _Mat

    articulo = forms.CharField(max_length=255, label="Artículo")
    material = forms.ModelChoiceField(
        queryset=_Mat.objects.select_related("tipo").all(),
        required=False, label="Material",
        empty_label="— Sin especificar —",
    )
    peso     = forms.DecimalField(max_digits=10, decimal_places=2, initial=1000, label="Peso (g)")
    costo    = forms.DecimalField(max_digits=14, decimal_places=2, label="Costo (COP)")
    fecha    = forms.DateField(initial=datetime.date.today,
                               widget=forms.DateInput(attrs={"type": "date"}),
                               label="Fecha de compra")
    unidades = forms.IntegerField(min_value=1, initial=1, label="Unidades")


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display  = ("id", "nombre", "tipo_documento", "documento", "email", "telefono")
    search_fields = ("nombre", "email", "documento")
    list_filter   = ("tipo_documento",)


@admin.register(Impresora)
class ImpresoraAdmin(admin.ModelAdmin):
    list_display    = ("id", "nombre", "tipo", "costo", "vida_util_horas", "activa")
    list_filter     = ("tipo", "activa")
    search_fields   = ("nombre",)
    readonly_fields = ("depreciacion_por_hora", "mantenimiento_por_hora")


@admin.register(TipoMaterial)
class TipoMaterialAdmin(admin.ModelAdmin):
    list_display  = ("id", "nombre")
    search_fields = ("nombre",)


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display  = ("id", "tipo", "nombre")
    list_filter   = ("tipo",)
    search_fields = ("nombre",)


@admin.register(Insumo)
class InsumoAdmin(admin.ModelAdmin):
    list_display    = ("id", "producto", "material", "cantidad_inicial", "cantidad_final", "diferencia", "actualizado_en")
    search_fields   = ("producto",)
    list_filter     = ("material__tipo",)
    readonly_fields = ("producto", "material", "cantidad_inicial", "cantidad_final", "diferencia", "stock_disponible", "actualizado_en")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    list_display    = ("cuui", "articulo", "material", "peso", "costo", "fecha")
    list_filter     = ("fecha", "material__tipo")
    search_fields   = ("articulo",)
    ordering        = ("-fecha",)
    readonly_fields = ("cuui",)
    autocomplete_fields = ["material"]

    def get_urls(self):
        return [
            path("crear-multiple/",
                 self.admin_site.admin_view(self.crear_multiple_view),
                 name="gasto-crear-multiple"),
        ] + super().get_urls()

    def crear_multiple_view(self, request):
        creados = None
        cuuis   = []

        if request.method == "POST":
            form = GastoMultipleForm(request.POST)
            if form.is_valid():
                d = form.cleaned_data
                for _ in range(d["unidades"]):
                    g = Gasto.objects.create(
                        articulo = d["articulo"],
                        material = d.get("material"),
                        peso     = d["peso"],
                        costo    = d["costo"],
                        fecha    = d["fecha"],
                    )
                    cuuis.append(g.cuui)
                creados = len(cuuis)
                form = GastoMultipleForm()
        else:
            form = GastoMultipleForm()

        context = {
            **self.admin_site.each_context(request),
            "form":    form,
            "creados": creados,
            "cuuis":   cuuis,
            "opts":    self.model._meta,
            "title":   "Agregar múltiples gastos",
        }
        return render(request, "admin/produccion/gasto/crear_multiple.html", context)


@admin.register(VariablesFijas)
class VariablesFijasAdmin(admin.ModelAdmin):
    """Singleton — no se puede añadir ni eliminar, solo editar."""

    def has_add_permission(self, request):
        return not VariablesFijas.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(InventarioPieza)
class InventarioPiezaAdmin(admin.ModelAdmin):
    form            = InventarioPiezaForm
    list_display    = ("id", "nombre", "peso_gramos", "tiempo_impresion_horas",
                       "costo_total_real", "precio_venta_sugerido", "actualizado_en")
    search_fields   = ("nombre",)
    ordering        = ("nombre",)
    readonly_fields = ("actualizado_en",)
    fieldsets = (
        (None, {
            "fields": (
                "nombre", "peso_gramos", "tiempo_impresion_horas",
                "tiempo_postproceso_horas", "costo_empaque",
            )
        }),
        ("Costos calculados", {
            "fields": (
                "costo_material", "costo_energia", "costo_tiempo",
                "subtotal_produccion", "amortizacion_fallos",
                "depreciacion_pieza", "mantenimiento_preventivo",
                "costo_total_real", "precio_venta_sugerido",
                "actualizado_en",
            )
        }),
        ("Archivos y referencias", {
            "fields": ("imagen", "archivo_3mf", "url_referencia"),
        }),
    )


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display        = ("id", "numero_pedido", "prioridad", "cliente", "pieza",
                           "cantidad", "realizados", "restantes", "precio_total",
                           "fecha_entrega", "maquina", "estado")
    list_filter         = ("estado", "prioridad", "maquina")
    search_fields       = ("numero_pedido", "cliente__nombre", "pieza__nombre", "descripcion")
    readonly_fields     = ("restantes", "peso_total", "precio_total", "gr_pieza", "precio_unidad")
    autocomplete_fields = ["cliente", "material", "pieza"]

    def get_readonly_fields(self, request, obj=None):
        base = list(self.readonly_fields)
        if obj is None:  # creación
            base.append("realizados")
        return base

    class Media:
        js = ('admin/js/pedido_producto.js',)


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display  = ("id", "fecha", "articulo", "cantidad", "cliente", "pedido")
    list_filter   = ("fecha",)
    search_fields = ("articulo",)
    ordering      = ("-fecha",)


@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display        = ("id", "prioridad", "cliente", "cliente_texto", "producto",
                           "cantidad", "realizados", "restantes", "fecha_entrega", "maquina", "estado")
    list_filter         = ("estado", "prioridad", "maquina")
    search_fields       = ("producto", "cliente_texto", "cliente__nombre")
    readonly_fields     = ("restantes",)
    autocomplete_fields = ["cliente"]
