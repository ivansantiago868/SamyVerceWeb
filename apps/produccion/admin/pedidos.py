"""
admin/pedidos.py
Gestión de Pedidos y Tareas de producción.
"""
from decimal import Decimal

from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import AutocompleteSelect
from django.core.exceptions import ValidationError
from django.urls import path, reverse
from django.utils.html import format_html, format_html_join

from apps.produccion.models import Pedido, PedidoMaterial, Tarea, FiguraPieza
from apps.produccion.admin.figura import FiguraAutocompleteJsonView
from apps.produccion.admin.mixins import EmpresaMixin


class FiguraAutocompleteSelect(AutocompleteSelect):
    """Apunta el autocomplete de "figura" a la vista propia de PedidoAdmin,
    que sí incluye la miniatura (el endpoint admin:autocomplete compartido no la trae)."""

    def get_url(self):
        return reverse("admin:pedido_figura_autocomplete")


class DatalistTextInput(forms.TextInput):
    """Input de texto con sugerencias (<datalist>) de valores existentes.

    A diferencia de un <select>, sigue aceptando un valor nuevo que no
    esté en las sugerencias (necesario para números de pedido nuevos).
    """

    def __init__(self, attrs=None, choices=()):
        super().__init__(attrs)
        self.choices = choices

    def render(self, name, value, attrs=None, renderer=None):
        attrs         = dict(attrs or {})
        list_id       = f"{attrs.get('id', name)}_list"
        attrs["list"] = list_id
        input_html    = super().render(name, value, attrs, renderer)
        options_html  = format_html_join("", "<option value='{}'>", ((c,) for c in self.choices))
        return format_html("{}<datalist id='{}'>{}</datalist>", input_html, list_id, options_html)


class TareaForm(forms.ModelForm):
    class Meta:
        model  = Tarea
        fields = "__all__"

    def clean_realizados(self):
        realizados = self.cleaned_data.get("realizados")
        if realizados is None:
            return realizados
        cantidad = (
            self.instance.cantidad
            if self.instance.pk
            else self.cleaned_data.get("cantidad", 0)
        )
        if cantidad and realizados > cantidad:
            raise ValidationError(
                f"Los realizados ({realizados}) no pueden superar "
                f"la cantidad del pedido ({cantidad})."
            )
        return realizados


class PedidoMaterialInline(admin.TabularInline):
    model               = PedidoMaterial
    extra               = 0
    fields              = ("pieza", "material")
    readonly_fields     = ("pieza",)
    autocomplete_fields = ["material"]
    verbose_name        = "Material por pieza"
    verbose_name_plural = "Materiales por pieza (solo figuras)"
    can_delete          = False

    def has_add_permission(self, request, obj=None):
        return False  # Solo se crean por signal


class PedidoForm(forms.ModelForm):
    class Meta:
        model   = Pedido
        fields  = "__all__"
        widgets = {"numero_pedido": DatalistTextInput()}

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("figura"):
            raise ValidationError("Debes seleccionar una Figura.")
        return cleaned


@admin.register(Pedido)
class PedidoAdmin(EmpresaMixin, admin.ModelAdmin):
    form                = PedidoForm
    grupos_empresa      = {"Maker"}
    list_display        = ("miniatura_figura", "numero_pedido", "cliente", "figura",
                           "cantidad", "realizados", "restantes", "estado",
                           "fecha_entrega", "prioridad", "maquina")
    list_editable       = ("cantidad", "estado")
    list_filter         = ("estado", "prioridad", "maquina")
    search_fields       = ("numero_pedido", "cliente__nombre", "figura__nombre", "descripcion")
    readonly_fields     = ("restantes", "realizados", "peso_total", "precio_total", "gr_pieza", "precio_unidad")
    autocomplete_fields = ["cliente", "figura"]
    inlines             = [PedidoMaterialInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("figura").prefetch_related("figura__imagenes")

    @admin.display(description="Miniatura")
    def miniatura_figura(self, obj):
        url = obj.figura.primera_imagen_url if obj.figura_id else None
        if not url:
            return "—"
        return format_html(
            '<img src="{}" style="width:44px;height:44px;object-fit:cover;border-radius:4px">',
            url,
        )

    def get_inline_instances(self, request, obj=None):
        inlines = super().get_inline_instances(request, obj)
        # Solo mostrar el inline de materiales si el pedido ya tiene figura guardada
        if obj is None or not obj.figura_id:
            return [i for i in inlines if not isinstance(i, PedidoMaterialInline)]
        return inlines

    def get_urls(self):
        return [
            path(
                "figura-autocomplete/",
                self.admin_site.admin_view(FiguraAutocompleteJsonView.as_view(admin_site=self.admin_site)),
                name="pedido_figura_autocomplete",
            ),
        ] + super().get_urls()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "figura":
            kwargs["widget"] = FiguraAutocompleteSelect(db_field, self.admin_site, using=kwargs.get("using"))
        elif db_field.name in ("color", "tipo"):
            kwargs["queryset"] = db_field.remote_field.model.objects.select_related("figura").order_by("figura__nombre", "nombre")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        FormClass = super().get_form(request, obj, **kwargs)
        FormClass.base_fields["numero_pedido"].widget.choices = list(
            self.get_queryset(request)
            .exclude(numero_pedido="")
            .order_by("numero_pedido")
            .values_list("numero_pedido", flat=True)
            .distinct()
        )
        return FormClass

    def save_model(self, request, obj, form, change):
        if change:
            anterior = Pedido.objects.values("estado", "cantidad").get(pk=obj.pk)
            super().save_model(request, obj, form, change)
            obj.refresh_from_db(fields=["estado", "cantidad"])
            if obj.estado != anterior["estado"]:
                Tarea.objects.filter(pedido=obj).update(estado=obj.estado)
            if obj.cantidad != anterior["cantidad"]:
                self._sincronizar_tareas_cantidad(obj)
        else:
            super().save_model(request, obj, form, change)

    @staticmethod
    def _sincronizar_tareas_cantidad(pedido):
        """Recalcula cantidad y precio_total de las Tareas de un Pedido cuando
        cambia Pedido.cantidad, con la misma fórmula que usa la creación
        inicial en signals.crear_tarea_desde_pedido (Venta no se actualiza
        aparte: sus totales se calculan en vivo desde Pedido.precio_total)."""
        if not pedido.figura_id:
            return
        for tarea in Tarea.objects.filter(pedido=pedido):
            try:
                fp = FiguraPieza.objects.select_related("pieza").get(
                    figura_id=pedido.figura_id,
                    pieza__nombre=tarea.producto,
                )
            except FiguraPieza.DoesNotExist:
                continue
            tarea.cantidad = fp.cantidad * pedido.cantidad
            tarea.precio_total = round(fp.subtotal_precio * pedido.cantidad, 2)
            tarea.save(update_fields=["cantidad", "precio_total"])

    class Media:
        js = ("admin/js/pedido_producto.js",)


class OcultarListosFilter(admin.SimpleListFilter):
    """Vista por defecto de Tareas (sin parámetro en la URL): "Tareas
    pendientes", que excluye los estados finales (Listo, Entregado,
    Cancelado). Se muestra como tres opciones explícitas (en vez del
    'Todo' automático de Django) para que el estado por defecto sea
    "pendientes", no "mostrar todo"."""

    title = "Vista"
    parameter_name = "ocultar_listos"

    ESTADOS_FINALES     = (Tarea.Estado.LISTO, Tarea.Estado.ENTREGADO, Tarea.Estado.CANCELADO)
    ESTADOS_TERMINADOS  = (Tarea.Estado.LISTO, Tarea.Estado.ENTREGADO)

    def lookups(self, request, model_admin):
        return (
            ("no", "Mostrar todos"),
            ("terminados", "Mostrar terminados"),
        )

    def choices(self, changelist):
        yield {
            "selected": self.value() not in ("no", "terminados"),
            "query_string": changelist.get_query_string(remove=[self.parameter_name]),
            "display": "Tareas pendientes",
        }
        yield {
            "selected": self.value() == "no",
            "query_string": changelist.get_query_string({self.parameter_name: "no"}),
            "display": "Mostrar todos",
        }
        yield {
            "selected": self.value() == "terminados",
            "query_string": changelist.get_query_string({self.parameter_name: "terminados"}),
            "display": "Mostrar terminados",
        }

    def queryset(self, request, queryset):
        if self.value() == "no":
            return queryset
        if self.value() == "terminados":
            return queryset.filter(estado__in=self.ESTADOS_TERMINADOS)
        return queryset.exclude(estado__in=self.ESTADOS_FINALES)


@admin.register(Tarea)
class TareaAdmin(EmpresaMixin, admin.ModelAdmin):
    form                = TareaForm
    grupos_empresa      = {"Maker"}
    list_display        = ("miniatura_figura", "producto","cliente","prioridad",
                           "piezas_por_figura", "color_tipo", "cantidad", "realizados", "restantes",
                           "fecha_entrega", "maquina", "estado")
    list_editable       = ("realizados", "estado")
    list_filter         = (OcultarListosFilter, "estado", "prioridad", "maquina")
    search_fields       = ("producto", "cliente_texto", "cliente__nombre")
    readonly_fields     = ("restantes", "piezas_por_figura")
    autocomplete_fields = ["cliente"]

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("pedido__figura", "pedido__color", "pedido__tipo")
            .prefetch_related("pedido__figura__imagenes")
        )

    @admin.display(description="Color / Tipo")
    def color_tipo(self, obj):
        if not obj.pedido_id:
            return "—"
        partes = [p.nombre for p in (obj.pedido.color, obj.pedido.tipo) if p]
        return " / ".join(partes) if partes else "—"

    @admin.display(description="Miniatura")
    def miniatura_figura(self, obj):
        if not obj.pedido_id or not obj.pedido.figura_id:
            return "—"
        url = obj.pedido.figura.primera_imagen_url
        if not url:
            return "—"
        return format_html(
            '<img src="{}" style="width:44px;height:44px;object-fit:cover;border-radius:4px">',
            url,
        )

    @admin.display(description="Piezas/figura")
    def piezas_por_figura(self, obj):
        if not obj.pedido_id or not obj.pedido.figura_id:
            return "—"
        try:
            fp = FiguraPieza.objects.only("cantidad").get(
                figura_id=obj.pedido.figura_id,
                pieza__nombre=obj.producto,
            )
            return fp.cantidad
        except FiguraPieza.DoesNotExist:
            return "—"

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return (
                "restantes", "piezas_por_figura", "prioridad", "pedido", "cliente",
                "cliente_texto", "producto", "cantidad", "precio_total",
                "fecha_entrega", "maquina", "descripcion", "creado_en",
            )
        return ("restantes",)

    def save_model(self, request, obj, form, change):
        if change and obj.pedido_id:
            anterior = Tarea.objects.values("estado", "realizados").get(pk=obj.pk)
            super().save_model(request, obj, form, change)
            # El trigger PostgreSQL pudo haber cambiado el estado; leer el valor real
            obj.refresh_from_db(fields=["estado"])

            if obj.estado != anterior["estado"]:
                Pedido.objects.filter(pk=obj.pedido_id).update(estado=obj.estado)

            delta = obj.realizados - anterior["realizados"]
            if delta > 0:
                # ── Descontar material del insumo ──────────────────────
                try:
                    pedido = Pedido.objects.select_related("figura").get(pk=obj.pedido_id)
                    if pedido.figura_id:
                        fp = FiguraPieza.objects.select_related("pieza", "insumo").get(
                            figura=pedido.figura,
                            pieza__nombre=obj.producto,
                        )
                        if fp.insumo_id and fp.pieza.peso_gramos:
                            gramos = Decimal(str(delta)) * fp.pieza.peso_gramos
                            fp.insumo.cantidad_final = max(
                                Decimal("0"),
                                fp.insumo.cantidad_final - gramos,
                            )
                            fp.insumo.save(update_fields=["cantidad_final"])
                except FiguraPieza.DoesNotExist:
                    pedido = Pedido.objects.select_related("figura").get(pk=obj.pedido_id)

                # ── Recalcular Pedido.realizados ───────────────────────
                # Una figura se completa cuando TODAS sus piezas tienen
                # suficientes realizados: floor(tarea.realizados / fp.cantidad)
                # Pedido.realizados = mínimo de esos valores entre todas las tareas
                self._sincronizar_realizados_pedido(obj.pedido_id)
        else:
            super().save_model(request, obj, form, change)

    @staticmethod
    def _sincronizar_realizados_pedido(pedido_id):
        try:
            pedido = Pedido.objects.select_related("figura").get(pk=pedido_id)
        except Pedido.DoesNotExist:
            return
        if not pedido.figura_id:
            return

        tareas = list(Tarea.objects.filter(pedido_id=pedido_id).values("producto", "realizados"))
        if not tareas:
            return

        min_figuras = None
        for t in tareas:
            try:
                fp = FiguraPieza.objects.get(
                    figura=pedido.figura,
                    pieza__nombre=t["producto"],
                )
                if fp.cantidad > 0:
                    completadas = t["realizados"] // fp.cantidad
                    if min_figuras is None or completadas < min_figuras:
                        min_figuras = completadas
            except FiguraPieza.DoesNotExist:
                continue

        if min_figuras is not None:
            Pedido.objects.filter(pk=pedido_id).update(
                realizados=min(min_figuras, pedido.cantidad)
            )

    def has_add_permission(self, _request):
        return False
