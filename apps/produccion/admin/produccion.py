"""
admin/produccion.py
Variables Fijas e Inventario de Piezas.
"""
from django.contrib import admin, messages
from django.db.models import ProtectedError
from django.http import HttpResponseRedirect
from django.urls import reverse
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
    list_display       = ("miniatura", "nombre", "peso_gramos", "tiempo_impresion_horas",
                          "costo_total_real", "precio_venta_sugerido", "actualizado_en")
    list_display_links = ("miniatura", "nombre")
    search_fields   = ("nombre",)
    ordering        = ("nombre",)
    readonly_fields = ("actualizado_en", "carrusel_imagenes")

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("imagenes")

    def save_formset(self, request, form, formset, change):
        from apps.produccion.models.inventario_pieza import PiezaImagen
        from django.db.models import Max
        instances = formset.save(commit=False)
        nuevas = [o for o in instances if not o.pk and isinstance(o, PiezaImagen)]
        if nuevas:
            pieza = form.instance
            max_o = PiezaImagen.objects.filter(pieza=pieza).aggregate(m=Max("orden"))["m"]
            siguiente = (max_o + 1) if max_o is not None else 0
            for obj in nuevas:
                obj.orden = siguiente
                siguiente += 1
        for form, obj in zip(formset.forms, instances):
            if not getattr(obj, '_skip_ia', None) is not None:
                procesar = form.cleaned_data.get("procesar_con_ia", True)
                obj._skip_ia = not procesar
            obj.save()
        formset.save_m2m()
        for obj in formset.deleted_objects:
            obj.delete()
    fieldsets = (
        ("Galería de imágenes", {
            "fields": ("carrusel_imagenes",),
            "description": "Agrega imágenes en el panel inferior. El carrusel se actualiza al guardar.",
        }),
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
        ("Archivos y referencias", {
            "fields": ("imagen", "url_referencia"),
        }),
    )

    def miniatura(self, obj):
        primera = next(iter(obj.imagenes.all()), None)
        img = primera.imagen_procesada if primera else obj.imagen_procesada
        if not img:
            return format_html('<span style="color:#ccc;font-size:18px">⏳</span>')
        return format_html(
            '<img src="{}" style="height:90px;max-width:120px;border-radius:8px;'
            'object-fit:contain;background:#f5f5f5;box-shadow:0 1px 6px rgba(0,0,0,.15)">',
            img.url,
        )
    miniatura.short_description = "Imagen IA"

    def carrusel_imagenes(self, obj):
        if not obj or not obj.pk:
            return mark_safe('<p style="color:#6c757d;font-style:italic">Guarda la pieza primero para agregar imágenes.</p>')
        procesadas = [img for img in obj.imagenes.all() if img.imagen_procesada]
        if not procesadas:
            return mark_safe('<p style="color:#6c757d;font-style:italic">⏳ Imágenes IA en proceso. Recarga en unos segundos.</p>')
        count = len(procesadas)
        slides_html = "".join(
            format_html(
                '<div class="pc-slide">'
                '<img src="{}" alt="Imagen {}" style="cursor:zoom-in" onclick="window._svLightbox&&window._svLightbox.open(this.src)">'
                '</div>',
                img.imagen_procesada.url, i + 1,
            )
            for i, img in enumerate(procesadas)
        )
        dots_html = "".join(
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
            '<a href="/api/v1/piezas/{}/descargar-imagenes-ia/" '
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
            boton_zip, count,
            mark_safe(slides_html), mark_safe(dots_html),
            mark_safe(descargas),
        )
    carrusel_imagenes.short_description = "Carrusel de imágenes IA"

    def delete_view(self, request, object_id, extra_context=None):
        try:
            return super().delete_view(request, object_id, extra_context)
        except ProtectedError as e:
            # Mostrar mensaje claro indicando qué figura usa esta pieza
            figuras = set()
            for obj in e.protected_objects:
                nombre = getattr(getattr(obj, "figura", None), "nombre", None)
                if nombre:
                    figuras.add(nombre)
            if figuras:
                lista = ", ".join(f'"{f}"' for f in sorted(figuras))
                msg = (
                    f'No se puede eliminar esta pieza porque está siendo usada en '
                    f'la(s) figura(s): {lista}. '
                    f'Primero quítala de esa figura y luego intenta de nuevo.'
                )
            else:
                msg = "No se puede eliminar: hay otros registros que dependen de esta pieza."
            self.message_user(request, msg, level=messages.ERROR)
            url = reverse("admin:produccion_inventariopieza_changelist")
            return HttpResponseRedirect(url)
