from django import forms
from django.contrib import admin
from apps.produccion.models import Figura, FiguraImagen, FiguraPieza
from apps.produccion.admin.mixins import EmpresaMixin, DragDropImageWidget


class FiguraImagenInlineForm(forms.ModelForm):
    class Meta:
        model   = FiguraImagen
        fields  = ("imagen", "orden")
        widgets = {"imagen": DragDropImageWidget()}


class FiguraImagenInline(admin.TabularInline):
    model  = FiguraImagen
    form   = FiguraImagenInlineForm
    extra  = 1
    fields = ("imagen", "orden")


class FiguraPiezaInline(admin.TabularInline):
    model               = FiguraPieza
    extra               = 1
    fields              = ("pieza", "cantidad", "subtotal_costo_display", "subtotal_precio_display")
    readonly_fields     = ("subtotal_costo_display", "subtotal_precio_display")
    autocomplete_fields = ["pieza"]

    def subtotal_costo_display(self, obj):
        return f"${obj.subtotal_costo:,.0f}" if obj.pk else "—"
    subtotal_costo_display.short_description = "Subtotal costo"

    def subtotal_precio_display(self, obj):
        return f"${obj.subtotal_precio:,.0f}" if obj.pk else "—"
    subtotal_precio_display.short_description = "Subtotal precio"


@admin.register(Figura)
class FiguraAdmin(EmpresaMixin, admin.ModelAdmin):
    grupos_empresa  = {"Maker"}
    list_display    = ("id", "nombre", "total_piezas", "costo_total_display", "precio_total_display", "actualizado_en")
    search_fields   = ("nombre", "descripcion")
    readonly_fields = ("costo_total_display", "precio_total_display", "creado_en", "actualizado_en")
    inlines         = [FiguraImagenInline, FiguraPiezaInline]
    fieldsets = (
        (None, {
            "fields": ("nombre", "descripcion"),
        }),
        ("Totales", {
            "fields": ("costo_total_display", "precio_total_display"),
            "classes": ("collapse",),
        }),
        ("Fechas", {
            "fields": ("creado_en", "actualizado_en"),
            "classes": ("collapse",),
        }),
    )

    def costo_total_display(self, obj):
        return f"${obj.costo_total:,.0f}" if obj.pk else "—"
    costo_total_display.short_description = "Costo total"

    def precio_total_display(self, obj):
        return f"${obj.precio_total:,.0f}" if obj.pk else "—"
    precio_total_display.short_description = "Precio total"
