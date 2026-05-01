from django import forms
from django.contrib import admin
from django.utils.html import format_html
from apps.produccion.models import Figura, FiguraImagen, FiguraPieza
from apps.produccion.admin.mixins import EmpresaMixin, DragDropImageWidget


class FiguraImagenInlineForm(forms.ModelForm):
    class Meta:
        model   = FiguraImagen
        fields  = ("imagen", "orden")
        widgets = {"imagen": DragDropImageWidget()}


class FiguraImagenInline(admin.TabularInline):
    model           = FiguraImagen
    form            = FiguraImagenInlineForm
    extra           = 1
    fields          = ("imagen", "orden", "preview_ia")
    readonly_fields = ("preview_ia",)

    @admin.display(description="Vista IA")
    def preview_ia(self, obj):
        if obj.imagen_procesada:
            return format_html(
                '<img src="{}" style="height:72px;border-radius:6px;'
                'object-fit:cover;box-shadow:0 1px 4px rgba(0,0,0,.2)">',
                obj.imagen_procesada.url,
            )
        return format_html('<span style="color:#aaa;font-size:11px">⏳ procesando…</span>')


class FiguraPiezaInline(admin.TabularInline):
    model               = FiguraPieza
    extra               = 1
    fields              = ("pieza", "insumo", "cantidad", "subtotal_costo_display", "subtotal_precio_display")
    readonly_fields     = ("subtotal_costo_display", "subtotal_precio_display")
    autocomplete_fields = ["pieza", "insumo"]

    def subtotal_costo_display(self, obj):
        return f"${obj.subtotal_costo:,.0f}" if obj.pk else "—"
    subtotal_costo_display.short_description = "Subtotal costo"

    def subtotal_precio_display(self, obj):
        return f"${obj.subtotal_precio:,.0f}" if obj.pk else "—"
    subtotal_precio_display.short_description = "Subtotal precio"


@admin.register(Figura)
class FiguraAdmin(EmpresaMixin, admin.ModelAdmin):
    grupos_empresa  = {"Maker"}
    list_display    = ("miniatura_ia", "id", "nombre", "total_piezas", "costo_total_display", "precio_total_display", "actualizado_en")
    search_fields   = ("nombre", "descripcion")
    readonly_fields = ("costo_total_display", "precio_total_display", "creado_en", "actualizado_en")
    inlines         = [FiguraImagenInline, FiguraPiezaInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("imagenes")

    @admin.display(description="Imagen IA")
    def miniatura_ia(self, obj):
        primera = next(iter(obj.imagenes.all()), None)
        if not primera or not primera.imagen_procesada:
            return format_html('<span style="color:#ccc;font-size:18px">⏳</span>')
        return format_html(
            '<img src="{}" style="height:90px;max-width:120px;border-radius:8px;'
            'object-fit:contain;background:#f5f5f5;box-shadow:0 1px 6px rgba(0,0,0,.15)">',
            primera.imagen_procesada.url,
        )
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
