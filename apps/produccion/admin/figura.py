from django import forms
from django.contrib import admin
from django.utils.html import format_html, mark_safe
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
    list_display       = ("miniatura_ia", "nombre", "total_piezas", "costo_total_display", "precio_total_display", "actualizado_en")
    list_display_links = ("miniatura_ia", "nombre")
    search_fields   = ("nombre", "descripcion")
    readonly_fields = ("costo_total_display", "precio_total_display", "creado_en", "actualizado_en", "carrusel_ia")
    inlines         = [FiguraImagenInline, FiguraPiezaInline]
    fieldsets = (
        ("Galería IA", {
            "fields": ("carrusel_ia",),
            "description": "Imágenes procesadas por IA. Se actualiza al guardar nuevas imágenes.",
        }),
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

    def carrusel_ia(self, obj):
        if not obj or not obj.pk:
            return mark_safe('<p style="color:#6c757d;font-style:italic">Guarda la figura primero.</p>')
        procesadas = [img for img in obj.imagenes.all() if img.imagen_procesada]
        if not procesadas:
            return mark_safe('<p style="color:#6c757d;font-style:italic">⏳ Sin imágenes IA aún. Agrega imágenes en el panel inferior.</p>')

        count = len(procesadas)
        slides = "".join(
            format_html(
                '<div class="pc-slide">'
                '<img src="{}" alt="IA {}" style="cursor:pointer" '
                'onclick="window.open(this.src)">'
                '</div>',
                img.imagen_procesada.url, i + 1,
            )
            for i, img in enumerate(procesadas)
        )
        dots = "".join(
            format_html(
                '<button type="button" class="pc-dot{}" data-index="{}"></button>',
                " active" if i == 0 else "", i,
            )
            for i in range(count)
        )
        descargas = "".join(
            format_html(
                '<a href="{}" download style="display:inline-flex;align-items:center;gap:.3rem;'
                'background:#f8f9fa;border:1px solid #dee2e6;border-radius:4px;'
                'padding:4px 10px;font-size:12px;color:#495057;text-decoration:none;margin:2px">'
                '⬇ Imagen {}</a>',
                img.imagen_procesada.url, i + 1,
            )
            for i, img in enumerate(procesadas)
        )
        boton_zip = format_html(
            '<a href="/api/v1/figuras/{}/descargar-imagenes-ia/" '
            'style="display:inline-flex;align-items:center;gap:.4rem;'
            'background:#417690;color:#fff;border-radius:4px;padding:6px 14px;'
            'font-size:13px;font-weight:bold;text-decoration:none;margin-bottom:8px">'
            '⬇ Descargar todas ({} imágenes)</a>',
            obj.pk, count,
        )
        return format_html(
            '{}'
            '<div class="pieza-carousel" data-count="{}">'
            '<div class="pc-track">{}</div>'
            '<button class="pc-btn pc-prev" type="button">&#8249;</button>'
            '<button class="pc-btn pc-next" type="button">&#8250;</button>'
            '<div class="pc-dots">{}</div>'
            '</div>'
            '<div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:4px">{}</div>',
            boton_zip,
            count,
            mark_safe(slides),
            mark_safe(dots),
            mark_safe(descargas),
        )
    carrusel_ia.short_description = "Carrusel imágenes IA"

    def costo_total_display(self, obj):
        return f"${obj.costo_total:,.0f}" if obj.pk else "—"
    costo_total_display.short_description = "Costo total"

    def precio_total_display(self, obj):
        return f"${obj.precio_total:,.0f}" if obj.pk else "—"
    precio_total_display.short_description = "Precio total"
