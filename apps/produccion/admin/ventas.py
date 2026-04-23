"""
admin/ventas.py
Cotizaciones / Ventas con generación de PDF imprimible.
"""
from decimal import Decimal

from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import path, reverse
from django.utils.html import format_html, mark_safe

from apps.produccion.models import Venta, Pedido
from apps.produccion.admin.mixins import EmpresaMixin, VentaForm


@admin.register(Venta)
class VentaAdmin(EmpresaMixin, admin.ModelAdmin):
    grupos_empresa    = {"Maker"}
    form              = VentaForm
    list_display      = ("id", "fecha", "numeros_pedido", "clientes_nombre", "precio_total_fmt", "btn_imprimir")
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
        ] + super().get_urls()

    def cotizacion_view(self, request, venta_id):
        venta   = get_object_or_404(Venta, pk=venta_id)
        pedidos = venta.pedidos.select_related("cliente", "pieza", "maquina").all()
        total   = sum(p.precio_total for p in pedidos)
        return HttpResponse(render_to_string(
            "admin/produccion/cotizacion.html",
            {"venta": venta, "pedidos": pedidos, "total": total},
            request=request,
        ))

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
        for p in obj.pedidos.select_related("cliente", "pieza").all():
            rows = []
            if p.cliente:
                rows.append(row("Cliente", p.cliente.nombre))
                if p.cliente.documento:
                    rows.append(row(p.cliente.get_tipo_documento_display(), p.cliente.documento))
            if p.pieza:
                rows.append(row("Pieza", p.pieza.nombre))
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
