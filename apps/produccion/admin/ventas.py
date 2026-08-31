"""
admin/ventas.py
Cotizaciones / Ventas con generación de PDF imprimible.
"""
from decimal import Decimal

from django.contrib import admin
from django.http import HttpResponse, HttpResponseNotAllowed, Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import path, reverse
from django.utils.html import format_html, mark_safe

from apps.produccion.models import Venta, Pedido, Tarea
from apps.produccion.admin.mixins import EmpresaMixin, VentaForm


@admin.register(Venta)
class VentaAdmin(EmpresaMixin, admin.ModelAdmin):
    grupos_empresa    = {"Maker"}
    form              = VentaForm
    list_display      = ("numeros_pedido", "fecha", "clientes_nombre", "precio_total_fmt",
                         "btn_imprimir", "btn_entregado", "btn_cancelado")
    list_filter       = ("fecha",)
    search_fields     = ("pedidos__numero_pedido", "pedidos__cliente__nombre")
    ordering          = ("-fecha",)
    filter_horizontal = ("pedidos",)
    readonly_fields   = ("info_pedidos", "accion_cotizacion")

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

    # ── URLs personalizadas ───────────────────────────────────
    def get_urls(self):
        return [
            path(
                "<int:venta_id>/cotizacion/",
                self.admin_site.admin_view(self.cotizacion_view),
                name="venta-cotizacion",
            ),
            path(
                "<int:venta_id>/marcar/<str:nuevo_estado>/",
                self.admin_site.admin_view(self.marcar_estado_view),
                name="venta-marcar-estado",
            ),
        ] + super().get_urls()

    def cotizacion_view(self, request, venta_id):
        venta   = get_object_or_404(Venta, pk=venta_id)
        pedidos = venta.pedidos.select_related("cliente", "figura", "maquina", "color", "tipo").all()
        total   = sum(p.precio_total for p in pedidos)
        cliente = next((p.cliente for p in pedidos if p.cliente), None)
        return HttpResponse(render_to_string(
            "admin/produccion/cotizacion.html",
            {"venta": venta, "pedidos": pedidos, "total": total, "cliente": cliente},
            request=request,
        ))

    def marcar_estado_view(self, request, venta_id, nuevo_estado):
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])
        if nuevo_estado not in (Pedido.Estado.ENTREGADO, Pedido.Estado.CANCELADO):
            raise Http404
        venta = get_object_or_404(Venta, pk=venta_id)
        pedidos_ids = list(venta.pedidos.values_list("id", flat=True))
        Pedido.objects.filter(pk__in=pedidos_ids).update(estado=nuevo_estado)
        Tarea.objects.filter(pedido_id__in=pedidos_ids).update(estado=nuevo_estado)
        self.message_user(request, f"Venta #{venta.pk} marcada como «{nuevo_estado}» ({len(pedidos_ids)} pedido(s)).")
        return redirect(reverse("admin:produccion_venta_changelist"))

    # ── Guardar empresa ───────────────────────────────────────
    def save_model(self, request, obj, form, change):
        empresa = self._empresa(request)
        if empresa is None:
            pedidos_ids = request.POST.getlist("pedidos")
            if pedidos_ids:
                primer = Pedido.objects.filter(pk__in=pedidos_ids, empresa__isnull=False).first()
                if primer:
                    empresa = primer.empresa
        if empresa is not None:
            obj.empresa = empresa
        admin.ModelAdmin.save_model(self, request, obj, form, change)

    # ── list_display ──────────────────────────────────────────
    def numeros_pedido(self, obj):
        nums = [p.numero_pedido for p in obj.pedidos.all() if p.numero_pedido]
        return ", ".join(nums) if nums else "—"
    numeros_pedido.short_description = "N° Pedidos"

    def clientes_nombre(self, obj):
        nombres = {p.cliente.nombre for p in obj.pedidos.select_related("cliente").all() if p.cliente}
        return ", ".join(nombres) if nombres else "—"
    clientes_nombre.short_description = "Cliente(s)"

    def precio_total_fmt(self, obj):
        total = sum(p.precio_total for p in obj.pedidos.all())
        return f"$ {total:,.0f} COP" if total else "—"
    precio_total_fmt.short_description = "Total"

    def btn_imprimir(self, obj):
        url = reverse("admin:venta-cotizacion", args=[obj.pk])
        return format_html(
            '<a href="{}" target="_blank" rel="noopener noreferrer"'
            ' onclick="event.stopPropagation()"'
            ' style="display:inline-block;background:#417690;color:#fff;'
            'padding:4px 12px;border-radius:4px;text-decoration:none;'
            'font-size:12px;font-weight:bold;white-space:nowrap">'
            '📄 Imprimir</a>',
            url,
        )
    btn_imprimir.short_description = "Cotización"

    def _venta_finalizada(self, obj):
        """Devuelve el estado si TODOS los pedidos de la venta ya están en
        ese mismo estado final (Entregado o Cancelado), o None si sigue
        habiendo pedidos en otro estado (o la venta no tiene pedidos)."""
        estados = list(obj.pedidos.values_list("estado", flat=True))
        if not estados:
            return None
        if all(e == Pedido.Estado.ENTREGADO for e in estados):
            return Pedido.Estado.ENTREGADO
        if all(e == Pedido.Estado.CANCELADO for e in estados):
            return Pedido.Estado.CANCELADO
        return None

    def _boton_estado(self, obj, nuevo_estado, etiqueta, color, deshabilitado):
        if deshabilitado:
            return format_html(
                '<button type="button" disabled title="Ya no se puede cambiar: la venta ya quedó finalizada" '
                'style="display:inline-block;background:#ccc;color:#777;'
                'padding:4px 12px;border:none;border-radius:4px;'
                'font-size:12px;font-weight:bold;white-space:nowrap;cursor:not-allowed">{}</button>',
                etiqueta,
            )
        # No se envuelve en su propio <form>: la tabla del changelist ya
        # está adentro de #changelist-form (para las acciones en lote), y
        # el HTML no permite formularios anidados — el navegador descarta
        # silenciosamente cualquier <form> extra dentro de otro, dejando el
        # botón sin enviar nada. En su lugar, "formaction" hace que este
        # botón envíe el formulario que ya existe hacia esta URL puntual,
        # reutilizando su método POST y su csrfmiddlewaretoken.
        url = reverse("admin:venta-marcar-estado", args=[obj.pk, nuevo_estado])
        return format_html(
            '<button type="submit" formaction="{}" formmethod="post" '
            'onclick="event.stopPropagation();" '
            'style="display:inline-block;background:{};color:#fff;'
            'padding:4px 12px;border:none;border-radius:4px;text-decoration:none;'
            'font-size:12px;font-weight:bold;white-space:nowrap;cursor:pointer">{}</button>',
            url, color, etiqueta,
        )

    def btn_entregado(self, obj):
        finalizada = self._venta_finalizada(obj)
        return self._boton_estado(obj, Pedido.Estado.ENTREGADO, "Entregado", "#2e7d32", deshabilitado=bool(finalizada))
    btn_entregado.short_description = ""

    def btn_cancelado(self, obj):
        finalizada = self._venta_finalizada(obj)
        return self._boton_estado(obj, Pedido.Estado.CANCELADO, "Cancelado", "#c62828", deshabilitado=bool(finalizada))
    btn_cancelado.short_description = ""

    # ── readonly fields ───────────────────────────────────────
    def info_pedidos(self, obj):
        if not obj.pk or not obj.pedidos.exists():
            return mark_safe('<p style="color:#6c757d;font-style:italic">Selecciona uno o más pedidos.</p>')

        def row(label, value):
            return (
                f'<tr>'
                f'<td style="color:#888;width:160px;padding:4px 8px 4px 0">{label}</td>'
                f'<td style="padding:4px 0"><strong>{value}</strong></td>'
                f'</tr>'
            )

        bloques, total_global = [], Decimal("0")
        for p in obj.pedidos.select_related("cliente", "figura", "color", "tipo").all():
            rows = []
            if p.cliente:
                rows.append(row("Cliente", p.cliente.nombre))
                if p.cliente.documento:
                    rows.append(row(p.cliente.get_tipo_documento_display(), p.cliente.documento))
            if p.figura:
                rows.append(row("Figura", p.figura.nombre))
            if p.color or p.tipo:
                partes = [v.nombre for v in (p.color, p.tipo) if v]
                rows.append(row("Color / Tipo", " · ".join(partes)))
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
            f'<div style="border-top:2px solid #417690;padding-top:8px;'
            f'font-size:14px;font-weight:bold;color:#417690">'
            f'TOTAL COTIZACIÓN: $ {total_global:,.0f} COP</div>'
        )
        return mark_safe("".join(bloques))
    info_pedidos.short_description = "Resumen de pedidos"

    def accion_cotizacion(self, obj):
        if not obj.pk:
            return mark_safe('<p style="color:#6c757d;font-style:italic">Guarda primero para generar la cotización.</p>')
        url = reverse("admin:venta-cotizacion", args=[obj.pk])
        return format_html(
            '<a href="{}" target="_blank" style="display:inline-block;'
            'background:#417690;color:#fff;padding:9px 20px;border-radius:5px;'
            'text-decoration:none;font-weight:bold;font-size:13px">'
            '📄 Ver / Imprimir Cotización</a>',
            url,
        )
    accion_cotizacion.short_description = "Generar cotización"
