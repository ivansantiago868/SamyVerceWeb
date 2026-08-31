"""
admin/recursos.py
Recursos compartidos: Clientes, Impresoras, Materiales, Insumos, Gastos.
"""
from django import forms
from django.contrib import admin
from django.contrib.auth.hashers import make_password
from django.db.models import Sum
from django.shortcuts import render
from django.urls import path
from django.utils.html import format_html

from apps.produccion.models import Cliente, Impresora, TipoMaterial, Material, Insumo, Gasto
from apps.produccion.admin.mixins import EmpresaMixin, GastoMultipleForm


def _color_swatch(color):
    if not color:
        return "—"
    return format_html(
        '<span style="display:inline-block;width:20px;height:20px;border-radius:4px;'
        'background:{};border:1px solid #ccc;vertical-align:middle" title="{}"></span>',
        color, color,
    )


class ClienteForm(forms.ModelForm):
    nueva_password = forms.CharField(
        required=False, widget=forms.PasswordInput(render_value=False),
        label="Nueva contraseña (portal del cliente)",
        help_text="Dejar en blanco para no cambiarla. Con esto el cliente puede loguearse en su catálogo con su número de documento.",
    )

    class Meta:
        model   = Cliente
        exclude = ("password",)

    def save(self, commit=True):
        cliente = super().save(commit=False)
        nueva_password = self.cleaned_data.get("nueva_password")
        if nueva_password:
            cliente.password = make_password(nueva_password)
        if commit:
            cliente.save()
            self.save_m2m()
        return cliente


@admin.register(Cliente)
class ClienteAdmin(EmpresaMixin, admin.ModelAdmin):
    grupos_empresa    = {"Maker"}
    form              = ClienteForm
    list_display      = ("nombre", "tipo_documento", "documento", "email", "telefono", "comision", "acceso_portal")
    search_fields     = ("nombre", "email", "documento")
    list_filter       = ("tipo_documento",)
    filter_horizontal = ("categorias_visibles",)

    @admin.display(description="Portal", boolean=True)
    def acceso_portal(self, obj):
        return bool(obj.password)


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
    list_display    = ("producto", "color_swatch", "material", "precio", "cantidad_inicial", "cantidad_final", "diferencia", "actualizado_en")
    search_fields   = ("producto",)
    list_filter     = ("material__tipo",)
    readonly_fields = ("producto", "material", "color", "cantidad_inicial", "cantidad_final", "diferencia", "stock_disponible", "actualizado_en")
    fields          = ("producto", "material", "color", "precio", "cantidad_inicial", "cantidad_final", "diferencia", "stock_disponible", "actualizado_en")

    def has_add_permission(self, request):
        return False

    @admin.display(description="Color")
    def color_swatch(self, obj):
        return _color_swatch(obj.color)

    def changelist_view(self, request, extra_context=None):
        qs = self.get_queryset(request)

        por_tipo_color = (
            qs.filter(material__isnull=False)
            .values("material__tipo__nombre", "color")
            .annotate(total=Sum("cantidad_final"))
        )

        tipos = sorted({r["material__tipo__nombre"] for r in por_tipo_color})
        colores = sorted({r["color"] or "" for r in por_tipo_color})
        matriz = {c: {t: 0.0 for t in tipos} for c in colores}
        for r in por_tipo_color:
            matriz[r["color"] or ""][r["material__tipo__nombre"]] = float(r["total"] or 0)

        series = [
            {
                "color": c or "#d1d5db",
                "label": c or "Sin color",
                "data": [matriz[c][t] for t in tipos],
            }
            for c in colores
        ]

        extra_context = extra_context or {}
        extra_context["tipos_chart"] = {"tipos": tipos, "series": series}
        return super().changelist_view(request, extra_context=extra_context)


class GastoForm(forms.ModelForm):
    color = forms.CharField(
        required=False,
        initial="#000000",
        label="Color",
        help_text="Color del material comprado (ej. color del filamento).",
        widget=forms.TextInput(attrs={"type": "color", "style": "width:52px;height:32px;padding:2px"}),
    )
    unidades = forms.IntegerField(
        required=False, min_value=1, initial=1, label="Unidades compradas",
        help_text="Unidades idénticas de esta misma referencia. Al grabar se crea un Gasto "
                  "(y su Insumo correspondiente) por cada una.",
    )

    class Meta:
        model  = Gasto
        fields = "__all__"


@admin.register(Gasto)
class GastoAdmin(EmpresaMixin, admin.ModelAdmin):
    grupos_empresa      = {"Maker"}
    form                = GastoForm
    list_display        = ("cuui", "articulo", "color_swatch", "material", "peso", "costo", "fecha")
    list_filter         = ("fecha", "material__tipo")
    search_fields       = ("articulo",)
    ordering            = ("-fecha",)
    readonly_fields     = ("cuui",)
    autocomplete_fields = ["material"]

    @admin.display(description="Color")
    def color_swatch(self, obj):
        return _color_swatch(obj.color)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj is not None:
            # "unidades" solo aplica al crear un Gasto nuevo, no al editar uno existente.
            form.base_fields.pop("unidades", None)
        return form

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if change:
            return
        unidades = form.cleaned_data.get("unidades") or 1
        if unidades <= 1:
            return
        for _ in range(unidades - 1):
            Gasto.objects.create(
                empresa=obj.empresa,
                articulo=obj.articulo,
                material=obj.material,
                peso=obj.peso,
                costo=obj.costo,
                fecha=obj.fecha,
                color=obj.color,
            )
        self.message_user(
            request,
            f"Se crearon {unidades} gastos (y sus insumos) para «{obj.articulo}».",
        )

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
                        color=d.get("color", ""),
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
