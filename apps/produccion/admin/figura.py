from django import forms
from django.contrib import admin
from django.urls import path
from django.utils.html import format_html, mark_safe
from apps.produccion.models import CategoriaFigura, EtiquetaFigura, Figura, FiguraImagen, FiguraPieza
from apps.produccion.admin.mixins import EmpresaMixin, DragDropImageWidget, DragDropFileWidget


@admin.register(CategoriaFigura)
class CategoriaFiguraAdmin(EmpresaMixin, admin.ModelAdmin):
    grupos_empresa = {"Maker"}
    list_display   = ("nombre",)
    search_fields  = ("nombre",)


@admin.register(EtiquetaFigura)
class EtiquetaFiguraAdmin(EmpresaMixin, admin.ModelAdmin):
    grupos_empresa = {"Maker"}
    list_display   = ("nombre",)
    search_fields  = ("nombre",)


class FiguraImagenInlineForm(forms.ModelForm):
    procesar_con_ia = forms.BooleanField(
        required=False,
        initial=True,
        label="Procesar con IA",
        widget=forms.CheckboxInput(attrs={"title": "Marcar para generar imagen IA automáticamente"}),
    )

    class Meta:
        model   = FiguraImagen
        fields  = ("imagen", "orden")
        widgets = {"imagen": DragDropImageWidget()}


class FiguraImagenInline(admin.TabularInline):
    model           = FiguraImagen
    form            = FiguraImagenInlineForm
    extra           = 1
    fields          = ("imagen", "orden", "procesar_con_ia", "preview_ia")
    readonly_fields = ("preview_ia",)

    @admin.display(description="Vista IA")
    def preview_ia(self, obj):
        if obj.imagen_procesada:
            return format_html(
                '<img src="{}" style="height:72px;border-radius:6px;'
                'object-fit:cover;box-shadow:0 1px 4px rgba(0,0,0,.2)">',
                obj.imagen_procesada.url,
            )
        if getattr(obj, "ia_error", ""):
            return format_html(
                '<span style="color:#c0392b;font-size:11px" title="{}">✗ {}</span>',
                obj.ia_error, obj.ia_error,
            )
        return format_html('<span style="color:#aaa;font-size:11px">⏳ procesando…</span>')


class FiguraPiezaInline(admin.TabularInline):
    model               = FiguraPieza
    extra               = 1
    can_delete          = True
    verbose_name_plural = "Piezas de la figura  (marca ✓ Eliminar + Guardar para quitar una pieza)"
    fields              = ("pieza", "insumo", "cantidad", "subtotal_costo_display", "subtotal_precio_display")
    readonly_fields     = ("subtotal_costo_display", "subtotal_precio_display")
    autocomplete_fields = ["pieza", "insumo"]

    def subtotal_costo_display(self, obj):
        return f"${obj.subtotal_costo:,.0f}" if obj.pk else "—"
    subtotal_costo_display.short_description = "Subtotal costo"

    def subtotal_precio_display(self, obj):
        return f"${obj.subtotal_precio:,.0f}" if obj.pk else "—"
    subtotal_precio_display.short_description = "Subtotal precio"


class FiguraAdminForm(forms.ModelForm):
    prompt_ia = forms.CharField(
        required=False,
        label="Tema / palabras clave para IA",
        widget=forms.TextInput(attrs={
            "id": "id_prompt_ia",
            "placeholder": "Ej: figura retro gaming, colores vivos, para niños…",
            "style": "width:100%;max-width:600px",
        }),
        help_text="Describe el producto en pocas palabras. La IA redactará la descripción.",
    )

    class Meta:
        model   = Figura
        fields  = "__all__"
        widgets = {"archivo_3mf": DragDropFileWidget()}


@admin.register(Figura)
class FiguraAdmin(EmpresaMixin, admin.ModelAdmin):
    grupos_empresa     = {"Maker"}
    form               = FiguraAdminForm
    list_display       = ("miniatura_ia", "nombre", "categorias_display", "etiquetas_display", "total_piezas", "costo_total_display", "precio_total_display", "actualizado_en")
    list_display_links = ("miniatura_ia", "nombre")
    list_filter        = ("categorias", "etiquetas")
    filter_horizontal  = ("categorias", "etiquetas")
    search_fields      = ("nombre", "descripcion")
    readonly_fields    = ("costo_total_display", "precio_total_display", "creado_en", "actualizado_en", "carrusel_ia", "boton_generar_ia")
    inlines            = [FiguraImagenInline, FiguraPiezaInline]
    fieldsets = (
        ("Galería IA", {
            "fields": ("carrusel_ia",),
            "description": "Imágenes procesadas por IA. Se actualiza al guardar nuevas imágenes.",
        }),
        (None, {
            "fields": ("nombre", "categorias", "etiquetas", "archivo_3mf", "prompt_ia", "boton_generar_ia", "descripcion"),
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

    class Media:
        js = ("admin/js/figura_ia_descripcion.js",)

    def get_urls(self):
        from apps.produccion.views.pdf_catalogo_figuras import exportar_catalogo_pdf, exportar_catalogo_pdf_real, exportar_catalogo_pdf_mixto
        from apps.produccion.views.ia_descripcion import generar_descripcion_ia
        return [
            path("catalogo-pdf/",
                 self.admin_site.admin_view(exportar_catalogo_pdf),
                 name="figuras_catalogo_pdf"),
            path("catalogo-pdf-real/",
                 self.admin_site.admin_view(exportar_catalogo_pdf_real),
                 name="figuras_catalogo_pdf_real"),
            path("catalogo-pdf-mixto/",
                 self.admin_site.admin_view(exportar_catalogo_pdf_mixto),
                 name="figuras_catalogo_pdf_mixto"),
            path("generar-descripcion-ia/",
                 self.admin_site.admin_view(generar_descripcion_ia),
                 name="figuras_generar_descripcion_ia"),
        ] + super().get_urls()

    def save_formset(self, request, form, formset, change):
        from apps.produccion.models.figura import FiguraImagen
        from django.db.models import Max
        instances = formset.save(commit=False)

        # Auto-asignar orden solo a imágenes nuevas que no tienen orden explícito (>0)
        nuevas_sin_orden = [
            o for o in instances
            if not o.pk and isinstance(o, FiguraImagen) and o.orden == 0
        ]
        if nuevas_sin_orden:
            figura = form.instance
            max_o = FiguraImagen.objects.filter(figura=figura).aggregate(m=Max("orden"))["m"]
            siguiente = (max_o + 1) if max_o is not None else 0
            for obj in nuevas_sin_orden:
                obj.orden = siguiente
                siguiente += 1

        for f, obj in zip(formset.saved_forms, instances):
            procesar = f.cleaned_data.get("procesar_con_ia", True)
            obj._skip_ia = not procesar
            obj.save()
        formset.save_m2m()
        for obj in formset.deleted_objects:
            obj.delete()

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_delete"] = False  # Evita borrar la figura desde el formulario de edición
        return super().change_view(request, object_id, form_url, extra_context)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("imagenes", "categorias", "etiquetas")

    @admin.display(description="Generar descripción")
    def boton_generar_ia(self, obj):
        return mark_safe(
            '<div style="display:flex;align-items:center;gap:10px;margin:4px 0">'
            '<button type="button" id="btn-generar-descripcion"'
            ' style="background:#1a4b8c;color:#fff;border:none;border-radius:4px;'
            'padding:7px 16px;font-size:13px;font-weight:bold;cursor:pointer;">'
            '✨ Generar con IA'
            '</button>'
            '<span id="ia-status" style="font-size:12px"></span>'
            '</div>'
        )
    boton_generar_ia.short_description = ""

    @admin.display(description="Imagen IA")
    def miniatura_ia(self, obj):
        primera = next(iter(obj.imagenes.all()), None)
        if not primera:
            return format_html('<span style="color:#ccc;font-size:18px">⏳</span>')
        if primera.imagen_procesada:
            return format_html(
                '<img src="{}" style="height:90px;max-width:120px;border-radius:8px;'
                'object-fit:contain;background:#f5f5f5;box-shadow:0 1px 6px rgba(0,0,0,.15)">',
                primera.imagen_procesada.url,
            )
        if primera.imagen:
            return format_html(
                '<img src="{}" style="height:90px;max-width:120px;border-radius:8px;'
                'object-fit:contain;background:#f5f5f5;box-shadow:0 1px 6px rgba(0,0,0,.15)">',
                primera.imagen.url,
            )
        if primera.ia_error:
            return format_html(
                '<span style="color:#c0392b;font-size:11px" title="{}">✗ {}</span>',
                primera.ia_error, primera.ia_error,
            )
        return format_html('<span style="color:#ccc;font-size:18px">⏳</span>')

    @admin.display(description="Categorías")
    def categorias_display(self, obj):
        return ", ".join(c.nombre for c in obj.categorias.all()) or "—"

    @admin.display(description="Etiquetas")
    def etiquetas_display(self, obj):
        return ", ".join(e.nombre for e in obj.etiquetas.all()) or "—"

    def carrusel_ia(self, obj):
        if not obj or not obj.pk:
            return mark_safe('<p style="color:#6c757d;font-style:italic">Guarda la figura primero.</p>')
        procesadas = [img for img in obj.imagenes.all() if img.imagen_procesada]
        if not procesadas:
            con_error = [img for img in obj.imagenes.all() if img.ia_error]
            if con_error:
                errores_html = "".join(
                    format_html('<li>{}</li>', img.ia_error) for img in con_error
                )
                return format_html(
                    '<p style="color:#c0392b;font-style:italic">✗ Error procesando imágenes IA:</p>'
                    '<ul style="color:#c0392b;font-size:12px">{}</ul>',
                    mark_safe(errores_html),
                )
            return mark_safe('<p style="color:#6c757d;font-style:italic">⏳ Sin imágenes IA aún. Agrega imágenes en el panel inferior.</p>')

        count = len(procesadas)
        slides = "".join(
            format_html(
                '<div class="pc-slide">'
                '<img src="{}" alt="IA {}" style="cursor:zoom-in;max-width:100%;height:auto" '
                'onclick="window._svLightbox&&window._svLightbox.open(this.src)">'
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
            boton_zip, count,
            mark_safe(slides), mark_safe(dots), mark_safe(descargas),
        )
    carrusel_ia.short_description = "Carrusel imágenes IA"

    def costo_total_display(self, obj):
        return f"${obj.costo_total:,.0f}" if obj.pk else "—"
    costo_total_display.short_description = "Costo total"

    def precio_total_display(self, obj):
        return f"${obj.precio_total:,.0f}" if obj.pk else "—"
    precio_total_display.short_description = "Precio total"
