"""
admin/recursos.py
Recursos compartidos: Clientes, Impresoras, Materiales, Insumos, Gastos.
"""
from django.contrib import admin
from django.shortcuts import render
from django.urls import path

from apps.produccion.models import Cliente, Impresora, TipoMaterial, Material, Insumo, Gasto
from apps.produccion.admin.mixins import EmpresaMixin, GastoMultipleForm


@admin.register(Cliente)
class ClienteAdmin(EmpresaMixin, admin.ModelAdmin):
    grupos_empresa = {"Maker"}
    list_display  = ("nombre", "tipo_documento", "documento", "email", "telefono")
    search_fields = ("nombre", "email", "documento")
    list_filter   = ("tipo_documento",)


@admin.register(Impresora)
class ImpresoraAdmin(EmpresaMixin, admin.ModelAdmin):
    grupos_empresa  = {"Maker"}
    list_display    = ("nombre", "tipo", "costo", "vida_util_horas", "consumo_promedio_kw", "activa")
    list_filter     = ("tipo", "activa")
    search_fields   = ("nombre",)
    readonly_fields = ("depreciacion_por_hora", "mantenimiento_por_hora")


@admin.register(TipoMaterial)
class TipoMaterialAdmin(EmpresaMixin, admin.ModelAdmin):
    grupos_empresa = {"Admin Empresa"}
    list_display  = ("nombre",)
    search_fields = ("nombre",)


@admin.register(Material)
class MaterialAdmin(EmpresaMixin, admin.ModelAdmin):
    grupos_empresa = {"Admin Empresa"}
    list_display  = ("tipo", "nombre")
    list_filter   = ("tipo",)
    search_fields = ("nombre",)


@admin.register(Insumo)
class InsumoAdmin(EmpresaMixin, admin.ModelAdmin):
    grupos_empresa  = {"Maker"}
    list_display    = ("producto", "material", "precio", "cantidad_inicial", "cantidad_final", "diferencia", "actualizado_en")
    search_fields   = ("producto",)
    list_filter     = ("material__tipo",)
    readonly_fields = ("producto", "material", "cantidad_inicial", "cantidad_final", "diferencia", "stock_disponible", "actualizado_en")
    fields          = ("producto", "material", "precio", "cantidad_inicial", "cantidad_final", "diferencia", "stock_disponible", "actualizado_en")

    def has_add_permission(self, request):
        return False


@admin.register(Gasto)
class GastoAdmin(EmpresaMixin, admin.ModelAdmin):
    grupos_empresa      = {"Maker"}
    list_display        = ("cuui", "articulo", "material", "peso", "costo", "fecha")
    list_filter         = ("fecha", "material__tipo")
    search_fields       = ("articulo",)
    ordering            = ("-fecha",)
    readonly_fields     = ("cuui",)
    autocomplete_fields = ["material"]

    def get_urls(self):
        return [
            path(
                "crear-multiple/",
                self.admin_site.admin_view(self.crear_multiple_view),
                name="gasto-crear-multiple",
            ),
        ] + super().get_urls()

    def crear_multiple_view(self, request):
        creados, cuuis = None, []
        if request.method == "POST":
            form = GastoMultipleForm(request.POST)
            if form.is_valid():
                d = form.cleaned_data
                empresa = self._empresa(request)
                for _ in range(d["unidades"]):
                    g = Gasto.objects.create(
                        empresa=empresa,
                        articulo=d["articulo"],
                        material=d.get("material"),
                        peso=d["peso"],
                        costo=d["costo"],
                        fecha=d["fecha"],
                    )
                    cuuis.append(g.cuui)
                creados = len(cuuis)
                form = GastoMultipleForm()
        else:
            form = GastoMultipleForm()

        return render(request, "admin/produccion/gasto/crear_multiple.html", {
            **self.admin_site.each_context(request),
            "form": form, "creados": creados, "cuuis": cuuis,
            "opts": self.model._meta, "title": "Agregar múltiples gastos",
        })
