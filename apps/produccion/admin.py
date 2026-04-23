import datetime
from decimal import Decimal

from django import forms
from django.contrib import admin
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import path, reverse
from django.utils.html import format_html, mark_safe

from apps.produccion.models import (
    Cliente, Impresora, TipoMaterial, Material,
    Insumo, Gasto,
    VariablesFijas, InventarioPieza, PiezaImagen,
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


class PiezaImagenInlineForm(forms.ModelForm):
    class Meta:
        model   = PiezaImagen
        fields  = ("imagen", "orden")
        widgets = {"imagen": DragDropImageWidget()}


class PiezaImagenInline(admin.TabularInline):
    model  = PiezaImagen
    form   = PiezaImagenInlineForm
    extra  = 1
    fields = ("imagen", "orden")


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
        return format_html('<img src="{}" style="height:48px;border-radius:4px;object-fit:cover">', img.url)
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
                " active" if i == 0 else "",
                i,
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
            count,
            mark_safe(slides_html),
            mark_safe(dots_html),
        )

    carrusel_imagenes.short_description = "Carrusel de imágenes"


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display        = ("id", "numero_pedido", "prioridad", "cliente", "pieza",
                           "cantidad", "realizados", "restantes", "precio_total",
                           "fecha_entrega", "maquina", "estado")
    list_editable       = ("estado",)
    list_filter         = ("estado", "prioridad", "maquina")
    search_fields       = ("numero_pedido", "cliente__nombre", "pieza__nombre", "descripcion")
    readonly_fields     = ("restantes", "realizados", "peso_total", "precio_total", "gr_pieza", "precio_unidad")
    autocomplete_fields = ["cliente", "material", "pieza"]

    def save_model(self, request, obj, form, change):
        if change:
            anterior_estado = Pedido.objects.values_list("estado", flat=True).get(pk=obj.pk)
            super().save_model(request, obj, form, change)
            if obj.estado != anterior_estado:
                Tarea.objects.filter(pedido=obj).update(estado=obj.estado)
        else:
            super().save_model(request, obj, form, change)

    class Media:
        js = ('admin/js/pedido_producto.js',)


class VentaForm(forms.ModelForm):
    class Meta:
        model  = Venta
        fields = ("pedidos", "fecha", "notas")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fecha"].initial = datetime.date.today


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    form             = VentaForm
    list_display     = ("id", "fecha", "numeros_pedido", "clientes_nombre", "precio_total_fmt")
    list_filter      = ("fecha",)
    search_fields    = ("pedidos__numero_pedido", "pedidos__cliente__nombre")
    ordering         = ("-fecha",)
    filter_horizontal = ("pedidos",)
    readonly_fields  = ("info_pedidos", "accion_cotizacion")
    fieldsets = (
        (None, {
            "fields": ("pedidos", "fecha", "notas"),
        }),
        ("Vista previa", {
            "fields": ("info_pedidos",),
        }),
        ("Cotización", {
            "fields": ("accion_cotizacion",),
        }),
    )

    def get_urls(self):
        return [
            path(
                "<int:venta_id>/cotizacion/",
                self.admin_site.admin_view(self.cotizacion_view),
                name="venta-cotizacion",
            ),
        ] + super().get_urls()

    def cotizacion_view(self, request, venta_id):
        venta = get_object_or_404(Venta, pk=venta_id)
        pedidos = venta.pedidos.select_related("cliente", "pieza", "maquina").all()
        total = sum(p.precio_total for p in pedidos)
        return HttpResponse(render_to_string(
            "admin/produccion/cotizacion.html",
            {"venta": venta, "pedidos": pedidos, "total": total},
            request=request,
        ))

    # ── list_display helpers ───────────────────────────────────
    def numeros_pedido(self, obj):
        nums = [p.numero_pedido for p in obj.pedidos.all() if p.numero_pedido]
        return ", ".join(nums) if nums else "—"
    numeros_pedido.short_description = "N° Pedidos"

    def clientes_nombre(self, obj):
        nombres = list({p.cliente.nombre for p in obj.pedidos.select_related("cliente").all() if p.cliente})
        return ", ".join(nombres) if nombres else "—"
    clientes_nombre.short_description = "Cliente(s)"

    def precio_total_fmt(self, obj):
        total = sum(p.precio_total for p in obj.pedidos.all())
        return f"$ {total:,.0f} COP" if total else "—"
    precio_total_fmt.short_description = "Total"

    # ── readonly fields ────────────────────────────────────────
    def info_pedidos(self, obj):
        if not obj.pk or not obj.pedidos.exists():
            return mark_safe(
                '<p style="color:#6c757d;font-style:italic">'
                'Selecciona uno o más pedidos para ver los datos.</p>'
            )

        def row(label, value):
            return (f'<tr>'
                    f'<td style="color:#888;width:160px;padding:4px 8px 4px 0">{label}</td>'
                    f'<td style="padding:4px 0"><strong>{value}</strong></td>'
                    f'</tr>')

        bloques = []
        total_global = Decimal("0")
        for p in obj.pedidos.select_related("cliente", "pieza").all():
            c, pz = p.cliente, p.pieza
            rows = []
            if c:
                rows.append(row("Cliente", c.nombre))
                if c.documento:
                    rows.append(row(c.get_tipo_documento_display(), c.documento))
            if pz:
                rows.append(row("Pieza", pz.nombre))
            rows.append(row("Cantidad", f"{p.cantidad} uds."))
            rows.append(row("Precio unitario", f"$ {p.precio_unidad:,.0f} COP"))
            rows.append(row("Subtotal", f"$ {p.precio_total:,.0f} COP"))
            if p.fecha_entrega:
                rows.append(row("Fecha entrega", str(p.fecha_entrega)))
            total_global += Decimal(str(p.precio_total))
            num = p.numero_pedido or f"#{p.pk}"
            bloques.append(
                f'<div style="margin-bottom:16px">'
                f'<div style="font-weight:bold;color:#417690;margin-bottom:6px">Pedido {num}</div>'
                f'<table style="border-collapse:collapse;font-size:13px">{"".join(rows)}</table>'
                f'</div>'
            )

        bloques.append(
            f'<div style="border-top:2px solid #417690;padding-top:8px;font-size:14px;font-weight:bold;color:#417690">'
            f'TOTAL COTIZACIÓN: $ {total_global:,.0f} COP</div>'
        )
        return mark_safe("".join(bloques))
    info_pedidos.short_description = "Resumen de pedidos"

    def accion_cotizacion(self, obj):
        if not obj.pk:
            return mark_safe(
                '<p style="color:#6c757d;font-style:italic">'
                'Guarda primero para generar la cotización.</p>'
            )
        url = reverse("admin:venta-cotizacion", args=[obj.pk])
        return format_html(
            '<a href="{}" target="_blank" style="display:inline-block;'
            'background:#417690;color:#fff;padding:9px 20px;border-radius:5px;'
            'text-decoration:none;font-weight:bold;font-size:13px">'
            '📄 Ver / Imprimir Cotización</a>',
            url,
        )
    accion_cotizacion.short_description = "Generar cotización"


@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display        = ("id", "prioridad", "cliente", "producto",
                           "cantidad", "realizados", "restantes", "fecha_entrega", "maquina", "estado")
    list_editable       = ("realizados", "estado")
    list_filter         = ("estado", "prioridad", "maquina")
    search_fields       = ("producto", "cliente_texto", "cliente__nombre")
    readonly_fields     = ("restantes",)
    autocomplete_fields = ["cliente"]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return (
                "restantes", "prioridad", "pedido", "cliente", "cliente_texto",
                "producto", "cantidad", "precio_total", "fecha_entrega",
                "maquina", "descripcion", "creado_en",
            )
        return ("restantes",)

    def save_model(self, request, obj, form, change):
        if change and obj.pedido_id:
            anterior = Tarea.objects.values("estado", "realizados").get(pk=obj.pk)
            super().save_model(request, obj, form, change)
            if obj.estado != anterior["estado"]:
                Pedido.objects.filter(pk=obj.pedido_id).update(estado=obj.estado)
            delta = obj.realizados - anterior["realizados"]
            if delta > 0:
                Pedido.objects.filter(pk=obj.pedido_id).update(realizados=F("realizados") + delta)
                pedido = Pedido.objects.select_related("material").get(pk=obj.pedido_id)
                if pedido.material_id and pedido.gr_pieza:
                    insumo = pedido.material
                    insumo.cantidad_inicial = insumo.cantidad_inicial + (Decimal(delta) * pedido.gr_pieza)
                    insumo.save()
        else:
            super().save_model(request, obj, form, change)

    def has_add_permission(self, _request):
        return False
