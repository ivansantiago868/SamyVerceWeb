"""
admin/pedidos.py
Gestión de Pedidos y Tareas de producción.
"""
from decimal import Decimal

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from apps.produccion.models import Pedido, PedidoMaterial, Tarea, FiguraPieza
from apps.produccion.admin.mixins import EmpresaMixin


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
        model  = Pedido
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("figura"):
            raise ValidationError("Debes seleccionar una Figura.")
        return cleaned


@admin.register(Pedido)
class PedidoAdmin(EmpresaMixin, admin.ModelAdmin):
    form                = PedidoForm
    grupos_empresa      = {"Maker"}
    list_display        = ("id", "numero_pedido", "cliente", "figura",
                           "cantidad", "realizados", "restantes", "estado",
                           "fecha_entrega", "prioridad", "maquina")
    list_editable       = ("estado",)
    list_filter         = ("estado", "prioridad", "maquina")
    search_fields       = ("numero_pedido", "cliente__nombre", "figura__nombre", "descripcion")
    readonly_fields     = ("restantes", "realizados", "peso_total", "precio_total", "gr_pieza", "precio_unidad")
    autocomplete_fields = ["cliente", "figura"]
    inlines             = [PedidoMaterialInline]

    def get_inline_instances(self, request, obj=None):
        inlines = super().get_inline_instances(request, obj)
        # Solo mostrar el inline de materiales si el pedido ya tiene figura guardada
        if obj is None or not obj.figura_id:
            return [i for i in inlines if not isinstance(i, PedidoMaterialInline)]
        return inlines

    def save_model(self, request, obj, form, change):
        if change:
            anterior_estado = Pedido.objects.values_list("estado", flat=True).get(pk=obj.pk)
            super().save_model(request, obj, form, change)
            obj.refresh_from_db(fields=["estado"])
            if obj.estado != anterior_estado:
                Tarea.objects.filter(pedido=obj).update(estado=obj.estado)
        else:
            super().save_model(request, obj, form, change)

    class Media:
        js = ("admin/js/pedido_producto.js",)


@admin.register(Tarea)
class TareaAdmin(EmpresaMixin, admin.ModelAdmin):
    form                = TareaForm
    grupos_empresa      = {"Maker"}
    list_display        = ("id", "prioridad", "cliente", "producto",
                           "piezas_por_figura", "cantidad", "realizados", "restantes",
                           "fecha_entrega", "maquina", "estado")
    list_editable       = ("realizados", "estado")
    list_filter         = ("estado", "prioridad", "maquina")
    search_fields       = ("producto", "cliente_texto", "cliente__nombre")
    readonly_fields     = ("restantes", "piezas_por_figura")
    autocomplete_fields = ["cliente"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("pedido__figura")

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
