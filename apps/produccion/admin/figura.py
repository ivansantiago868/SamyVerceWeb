from django import forms
from django.contrib import admin
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.urls import path, reverse
from django.utils.html import format_html, format_html_join, mark_safe
from apps.produccion.models import CategoriaFigura, EtiquetaFigura, Figura, FiguraImagen, FiguraPieza, FiguraArchivo3MF, FiguraColor, FiguraTipo
from apps.produccion.admin.mixins import EmpresaMixin, DragDropImageWidget, DragDropFileWidget


class FiguraAutocompleteJsonView(AutocompleteJsonView):
    """Agrega la miniatura (primera imagen del carrusel) a cada resultado del autocomplete."""

    def serialize_result(self, obj, to_field_name):
        result = super().serialize_result(obj, to_field_name)
        result["img"] = obj.primera_imagen_url
        return result


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
        fields  = ("imagen", "orden", "modo_carrusel")
        widgets = {"imagen": DragDropImageWidget()}


class FiguraImagenInline(admin.TabularInline):
    model           = FiguraImagen
    form            = FiguraImagenInlineForm
    extra           = 1
    fields          = ("imagen", "orden", "procesar_con_ia", "modo_carrusel", "preview_ia")
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


class FiguraArchivo3MFInlineForm(forms.ModelForm):
    class Meta:
        model   = FiguraArchivo3MF
        fields  = ("archivo", "nombre", "orden")
        widgets = {"archivo": DragDropFileWidget()}


class FiguraArchivo3MFInline(admin.TabularInline):
    model  = FiguraArchivo3MF
    form   = FiguraArchivo3MFInlineForm
    extra  = 1
    fields = ("archivo", "nombre", "orden")
    verbose_name_plural = "Archivos 3MF"


class FiguraColorInlineForm(forms.ModelForm):
    # Declarado explícito (no solo en Meta.widgets) para fijar `initial`: un
    # <input type="color"> nunca se envía vacío (el navegador manda "#000000"
    # por defecto), así que sin este initial coincidiendo, Django considera
    # "modificada" cualquier fila extra en blanco y exige nombre/imagen.
    color_hex = forms.CharField(
        required=False,
        initial="#000000",
        widget=forms.TextInput(attrs={"type": "color", "style": "width:52px;height:32px;padding:2px"}),
    )

    class Meta:
        model   = FiguraColor
        fields  = ("nombre", "color_hex", "imagen", "orden")
        widgets = {"imagen": DragDropImageWidget()}


class FiguraColorInline(admin.TabularInline):
    model           = FiguraColor
    form            = FiguraColorInlineForm
    extra           = 1
    fields          = ("nombre", "color_hex", "imagen", "orden", "preview")
    readonly_fields = ("preview",)
    verbose_name_plural = "Colores disponibles"

    @admin.display(description="Vista previa")
    def preview(self, obj):
        if obj.pk and obj.imagen:
            return format_html(
                '<img src="{}" style="height:56px;border-radius:6px;'
                'object-fit:cover;box-shadow:0 1px 4px rgba(0,0,0,.2)">',
                obj.imagen.url,
            )
        return format_html('<span style="color:#aaa;font-size:11px">—</span>')


class FiguraTipoInlineForm(forms.ModelForm):
    class Meta:
        model   = FiguraTipo
        fields  = ("nombre", "descripcion", "imagen", "orden")
        widgets = {"imagen": DragDropImageWidget()}


class FiguraTipoInline(admin.TabularInline):
    model           = FiguraTipo
    form            = FiguraTipoInlineForm
    extra           = 1
    fields          = ("nombre", "descripcion", "imagen", "orden", "preview")
    readonly_fields = ("preview",)
    verbose_name_plural = "Tipos / variantes (ej. \"Para NES\", \"Para Super Nintendo\")"

    @admin.display(description="Vista previa")
    def preview(self, obj):
        if obj.pk and obj.imagen:
            return format_html(
                '<img src="{}" style="height:56px;border-radius:6px;'
                'object-fit:cover;box-shadow:0 1px 4px rgba(0,0,0,.2)">',
                obj.imagen.url,
            )
        return format_html('<span style="color:#aaa;font-size:11px">—</span>')


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


@admin.register(Figura)
class FiguraAdmin(EmpresaMixin, admin.ModelAdmin):
    grupos_empresa     = {"Maker"}
    form               = FiguraAdminForm
    list_display       = ("miniatura_ia", "nombre", "categorias_display", "etiquetas_display", "total_piezas", "costo_total_display", "precio_total_display", "descargar_3mf", "btn_regenerar_ia", "actualizado_en")
    list_display_links = ("miniatura_ia", "nombre")
    list_filter        = ("categorias", "etiquetas")
    filter_horizontal  = ("categorias", "etiquetas")
    search_fields      = ("nombre", "descripcion")
    readonly_fields    = ("costo_total_display", "precio_total_display", "creado_en", "actualizado_en", "carrusel_ia", "boton_generar_ia")
    inlines            = [FiguraImagenInline, FiguraColorInline, FiguraTipoInline, FiguraArchivo3MFInline, FiguraPiezaInline]
    fieldsets = (
        ("Galería", {
            "fields": ("carrusel_ia",),
            "description": "Respeta lo elegido en \"Mostrar en carrusel\" por cada imagen (Solo IA / "
                           "Solo original / Ambas). Se actualiza al guardar.",
        }),
        (None, {
            "fields": ("nombre", "categorias", "etiquetas", "prompt_ia", "boton_generar_ia", "descripcion"),
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
        from apps.produccion.views.pdf_catalogo_figuras import exportar_catalogo_pdf
        from apps.produccion.views.zip_catalogo_figuras import exportar_zip_precios
        from apps.produccion.views.ia_descripcion import generar_descripcion_ia
        from apps.produccion.views.reintentar_ia import (
            reintentar_ia_fallidas, conteo_ia_fallidas, estado_ia_reintento, regenerar_ia_figura,
        )
        return [
            path("catalogo-pdf/",
                 self.admin_site.admin_view(exportar_catalogo_pdf),
                 name="figuras_catalogo_pdf"),
            path("descargar-zip-precios/",
                 self.admin_site.admin_view(exportar_zip_precios),
                 name="figuras_zip_precios"),
            path("generar-descripcion-ia/",
                 self.admin_site.admin_view(generar_descripcion_ia),
                 name="figuras_generar_descripcion_ia"),
            path("reintentar-ia-fallidas/",
                 self.admin_site.admin_view(reintentar_ia_fallidas),
                 name="figuras_reintentar_ia_fallidas"),
            path("conteo-ia-fallidas/",
                 self.admin_site.admin_view(conteo_ia_fallidas),
                 name="figuras_conteo_ia_fallidas"),
            path("estado-ia-reintento/",
                 self.admin_site.admin_view(estado_ia_reintento),
                 name="figuras_estado_ia_reintento"),
            path("<int:figura_id>/regenerar-ia/",
                 self.admin_site.admin_view(regenerar_ia_figura),
                 name="figuras_regenerar_ia"),
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
        return super().get_queryset(request).prefetch_related("imagenes", "categorias", "etiquetas", "archivos_3mf", "colores", "tipos")

    @admin.display(description="3MF")
    def descargar_3mf(self, obj):
        archivos = [a for a in obj.archivos_3mf.all() if a.descarga_url]
        if not archivos:
            return "—"
        return format_html_join(
            "",
            '<a href="{}" target="_blank" rel="noopener noreferrer"'
            ' onclick="event.stopPropagation()"'
            ' style="display:inline-block;background:#417690;color:#fff;'
            'padding:4px 10px;border-radius:4px;text-decoration:none;'
            'font-size:12px;font-weight:bold;white-space:nowrap;margin:2px 4px 2px 0">'
            '⬇ {}</a>',
            (
                (archivo.descarga_url, archivo.nombre or f"3MF #{i}")
                for i, archivo in enumerate(archivos, start=1)
            ),
        )

    @admin.display(description="Imágenes IA")
    def btn_regenerar_ia(self, obj):
        url = reverse("admin:figuras_regenerar_ia", args=[obj.pk])
        # Sin stopPropagation: el manejador de clic vive en document (delegación
        # de eventos, ver change_list.html) y necesita que el evento burbujee.
        return format_html(
            '<button type="button" class="btn-regenerar-ia-figura" '
            'data-url="{}" data-nombre="{}" '
            'style="display:inline-block;background:#8e44ad;color:#fff;border:none;'
            'padding:4px 10px;border-radius:4px;font-size:12px;font-weight:bold;'
            'white-space:nowrap;cursor:pointer">🔄 Regenerar IA</button>',
            url, obj.nombre,
        )

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

        if not primera.imagen:
            if primera.ia_error:
                return format_html(
                    '<span style="color:#c0392b;font-size:11px" title="{}">✗ {}</span>',
                    primera.ia_error, primera.ia_error,
                )
            return format_html('<span style="color:#ccc;font-size:18px">⏳</span>')

        # Sin imagen IA todavía: mostrar la foto normal, pero sin ocultar si sigue
        # procesando o si el procesamiento falló (el campo "imagen" siempre existe,
        # así que este estado debe mostrarse aparte, no en lugar de la miniatura).
        if primera.ia_error:
            estado = format_html(
                '<div style="color:#c0392b;font-size:10px" title="{}">✗ Error IA</div>',
                primera.ia_error,
            )
        else:
            estado = format_html('<div style="color:#999;font-size:10px">⏳ Generando IA…</div>')

        return format_html(
            '<div style="text-align:center">'
            '<img src="{}" style="height:90px;max-width:120px;border-radius:8px;'
            'object-fit:contain;background:#f5f5f5;box-shadow:0 1px 6px rgba(0,0,0,.15)">'
            '{}'
            '</div>',
            primera.imagen.url, estado,
        )

    @admin.display(description="Categorías")
    def categorias_display(self, obj):
        return ", ".join(c.nombre for c in obj.categorias.all()) or "—"

    @admin.display(description="Etiquetas")
    def etiquetas_display(self, obj):
        return ", ".join(e.nombre for e in obj.etiquetas.all()) or "—"

    def carrusel_ia(self, obj):
        if not obj or not obj.pk:
            return mark_safe('<p style="color:#6c757d;font-style:italic">Guarda la figura primero.</p>')

        def _urls_mostrar(img):
            url_ia = img.imagen_procesada.url if img.imagen_procesada else None
            url_normal = img.imagen.url if img.imagen else None
            if img.modo_carrusel == FiguraImagen.AMBAS:
                return [u for u in (url_ia, url_normal) if u]
            if img.modo_carrusel == FiguraImagen.NORMAL:
                return [url_normal] if url_normal else []
            # IA (default): usar la IA si existe, si no caer a la normal.
            return [url_ia] if url_ia else ([url_normal] if url_normal else [])

        disponibles = []
        for img in obj.imagenes.all():
            for url in _urls_mostrar(img):
                disponibles.append((url, None))
        for tipo in obj.tipos.all():
            if tipo.imagen:
                disponibles.append((tipo.imagen.url, tipo.nombre))

        if not disponibles:
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
            return mark_safe('<p style="color:#6c757d;font-style:italic">⏳ Sin imágenes aún. Agrega imágenes en el panel inferior.</p>')

        count = len(disponibles)
        slides = "".join(
            format_html(
                '<div class="pc-slide">'
                '<img src="{}" alt="{}" style="cursor:zoom-in;max-width:100%;height:auto" '
                'onclick="window._svLightbox&&window._svLightbox.open(this.src)">'
                '</div>',
                url, etiqueta or f"Imagen {i + 1}",
            )
            for i, (url, etiqueta) in enumerate(disponibles)
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
                '⬇ {}</a>',
                url, etiqueta or f"Imagen {i + 1}",
            )
            for i, (url, etiqueta) in enumerate(disponibles)
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
    carrusel_ia.short_description = "Carrusel de imágenes"

    def costo_total_display(self, obj):
        return f"${obj.costo_total:,.0f}" if obj.pk else "—"
    costo_total_display.short_description = "Costo total"

    def precio_total_display(self, obj):
        return f"${obj.precio_total:,.0f}" if obj.pk else "—"
    precio_total_display.short_description = "Precio total"
