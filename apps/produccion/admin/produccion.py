"""
admin/produccion.py
Variables Fijas e Inventario de Piezas.
"""
from django.contrib import admin
from django.utils.html import format_html, mark_safe

from apps.produccion.models import VariablesFijas, InventarioPieza
from apps.produccion.admin.mixins import (
    EmpresaMixin, InventarioPiezaForm, PiezaImagenInline,
)


@admin.register(VariablesFijas)
class VariablesFijasAdmin(EmpresaMixin, admin.ModelAdmin):
    grupos_empresa = {"Admin Empresa"}

    def has_add_permission(self, request):
        empresa = self._empresa(request)
        if empresa is not None:
            return not VariablesFijas.objects.filter(empresa=empresa).exists()
        return not VariablesFijas.objects.filter(empresa__isnull=True).exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(InventarioPieza)
class InventarioPiezaAdmin(EmpresaMixin, admin.ModelAdmin):
    grupos_empresa  = {"Maker"}
    form            = InventarioPiezaForm

    def has_add_permission(self, request):
        return False
    inlines         = [PiezaImagenInline]
    list_display    = ("miniatura", "id", "nombre", "peso_gramos", "tiempo_impresion_horas",
                       "costo_total_real", "precio_venta_sugerido", "actualizado_en")
    search_fields   = ("nombre",)
    ordering        = ("nombre",)
    readonly_fields = ("actualizado_en", "carrusel_imagenes")
    fieldsets = (
        (None, {
            "fields": (
                "nombre", "peso_gramos", "tiempo_impresion_horas",
                "tiempo_postproceso_horas", "costo_empaque",
            ),
        }),
        ("Costos calculados", {
            "fields": (
                "costo_material", "costo_energia", "costo_tiempo",
                "subtotal_produccion", "amortizacion_fallos",
                "depreciacion_pieza", "mantenimiento_preventivo",
                "costo_total_real", "precio_venta_sugerido", "actualizado_en",
            ),
        }),
        ("Galería de imágenes", {
            "fields": ("carrusel_imagenes",),
            "description": "Agrega imágenes en el panel inferior. El carrusel se actualiza al guardar.",
        }),
        ("Archivos y referencias", {
            "fields": ("imagen", "archivo_3mf", "url_referencia"),
        }),
    )

    def miniatura(self, obj):
        img = obj.imagen or (obj.imagenes.first().imagen if obj.imagenes.exists() else None)
        if not img:
            return "—"
        return format_html(
            '<img src="{}" style="height:48px;border-radius:4px;object-fit:cover">',
            img.url,
        )
    miniatura.short_description = "Imagen"

    def carrusel_imagenes(self, obj):
        if not obj or not obj.pk:
            return mark_safe('<p style="color:#6c757d;font-style:italic">Guarda la pieza primero para agregar imágenes.</p>')
        imagenes = list(obj.imagenes.all())
        if not imagenes:
            return mark_safe('<p style="color:#6c757d;font-style:italic">Sin imágenes. Usa el panel inferior para agregar.</p>')
        count = len(imagenes)
        slides_html = "".join(
            format_html('<div class="pc-slide"><img src="{}" alt="Imagen {}"></div>', img.imagen.url, i + 1)
            for i, img in enumerate(imagenes)
        )
        dots_html = "".join(
            format_html(
                '<button type="button" class="pc-dot{}" data-index="{}"></button>',
                " active" if i == 0 else "", i,
            )
            for i in range(count)
        )
        return format_html(
            '<div class="pieza-carousel" data-count="{}">'
            '<div class="pc-track">{}</div>'
            '<button class="pc-btn pc-prev" type="button">&#8249;</button>'
            '<button class="pc-btn pc-next" type="button">&#8250;</button>'
            '<div class="pc-dots">{}</div>'
            '</div>',
            count, mark_safe(slides_html), mark_safe(dots_html),
        )
    carrusel_imagenes.short_description = "Carrusel de imágenes"
