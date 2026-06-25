from django.contrib import admin
from django.utils.html import format_html

from apps.produccion.models.diseno3d import Diseno3D
from apps.produccion.admin.mixins import EmpresaMixin, DragDropImageWidget


class Diseno3DAdminForm:
    pass  # usa el ModelForm por defecto de Django


@admin.register(Diseno3D)
class Diseno3DAdmin(EmpresaMixin, admin.ModelAdmin):
    grupos_empresa = {"Maker"}

    list_display = (
        "miniatura", "nombre_display", "estado_badge",
        "progreso_bar", "formato", "creado_en",
    )
    list_display_links = ("miniatura", "nombre_display")
    list_filter        = ("estado", "formato")
    search_fields      = ("nombre", "tripo_task_id", "prompt")
    readonly_fields    = (
        "estado", "progreso", "tripo_task_id", "tripo_image_token",
        "analisis_ia", "error_mensaje", "url_descarga_tripo",
        "creado_en", "actualizado_en",
        "vista_previa_imagen", "boton_descarga",
    )
    fieldsets = (
        ("Imagen de referencia", {
            "fields": ("vista_previa_imagen", "imagen_original", "nombre"),
            "description": (
                "Sube la imagen de referencia. "
                "El sistema la analizará con IA y generará el modelo 3D automáticamente."
            ),
        }),
        ("Parámetros Tripo AI", {
            "fields": (
                "model_version", "formato",
                ("texture", "pbr", "enable_image_autofix"),
                "face_limit",
                ("texture_alignment", "orientation"),
                "prompt",
            ),
        }),
        ("Estado del proceso", {
            "fields": (
                "estado", "progreso", "tripo_task_id",
                "error_mensaje", "analisis_ia",
            ),
            "classes": ("collapse",),
        }),
        ("Resultado", {
            "fields": ("boton_descarga", "archivo_modelo"),
        }),
        ("Metadatos", {
            "fields": ("creado_en", "actualizado_en"),
            "classes": ("collapse",),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if "imagen_original" in form.base_fields:
            form.base_fields["imagen_original"].widget = DragDropImageWidget()
        return form

    # ── List display helpers ─────────────────────────────────────────

    @admin.display(description="")
    def miniatura(self, obj):
        if obj.imagen_original:
            try:
                return format_html(
                    '<img src="{}" style="height:64px;width:64px;object-fit:cover;'
                    'border-radius:6px;box-shadow:0 1px 4px rgba(0,0,0,.2)">',
                    obj.imagen_original.url,
                )
            except Exception:
                pass
        return format_html('<span style="color:#ccc;font-size:20px">🖼</span>')

    @admin.display(description="Nombre")
    def nombre_display(self, obj):
        return obj.nombre or f"Diseño #{obj.pk}"

    @admin.display(description="Estado")
    def estado_badge(self, obj):
        colores = {
            "pendiente":  "#6c757d",
            "procesando": "#fd7e14",
            "completado": "#28a745",
            "fallido":    "#dc3545",
        }
        iconos = {
            "pendiente":  "⏳",
            "procesando": "⚙️",
            "completado": "✅",
            "fallido":    "❌",
        }
        color = colores.get(obj.estado, "#6c757d")
        icono = iconos.get(obj.estado, "")
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;'
            'border-radius:12px;font-size:11px;font-weight:bold">{} {}</span>',
            color, icono, obj.get_estado_display(),
        )

    @admin.display(description="Progreso")
    def progreso_bar(self, obj):
        p = obj.progreso
        return format_html(
            '<div style="width:80px;background:#e9ecef;border-radius:4px;height:8px">'
            '<div style="width:{}%;background:#417690;border-radius:4px;height:8px"></div>'
            '</div> <small>{}%</small>',
            p, p,
        )

    # ── Detail view helpers ──────────────────────────────────────────

    @admin.display(description="Vista previa")
    def vista_previa_imagen(self, obj):
        if obj.pk and obj.imagen_original:
            try:
                return format_html(
                    '<img src="{}" style="max-height:200px;max-width:300px;'
                    'border-radius:8px;object-fit:contain;background:#f5f5f5;'
                    'box-shadow:0 1px 6px rgba(0,0,0,.15)">',
                    obj.imagen_original.url,
                )
            except Exception:
                pass
        return format_html(
            '<span style="color:#6c757d;font-style:italic">Sin imagen aún.</span>'
        )

    @admin.display(description="Descargar modelo")
    def boton_descarga(self, obj):
        if obj.estado == "completado" and obj.archivo_modelo:
            try:
                return format_html(
                    '<a href="{}" download '
                    'style="display:inline-flex;align-items:center;gap:.4rem;'
                    'background:#28a745;color:#fff;border-radius:4px;'
                    'padding:8px 16px;font-size:13px;font-weight:bold;text-decoration:none">'
                    '⬇ Descargar modelo {}</a>',
                    obj.archivo_modelo.url,
                    obj.formato.upper(),
                )
            except Exception:
                pass
        if obj.estado == "procesando":
            return format_html(
                '<span style="color:#fd7e14;font-size:13px">⚙️ Generando... {}%</span>',
                obj.progreso,
            )
        if obj.estado == "fallido":
            return format_html(
                '<span style="color:#dc3545;font-size:13px">❌ {}</span>',
                obj.error_mensaje or "Error desconocido",
            )
        return format_html(
            '<span style="color:#6c757d;font-style:italic;font-size:12px">Pendiente</span>'
        )

    def save_model(self, request, obj, form, change):
        """Al guardar un nuevo diseño, lanza automáticamente la generación."""
        is_new = not obj.pk
        super().save_model(request, obj, form, change)
        if is_new:
            from apps.produccion.controllers.diseno3d_controller import Diseno3DController
            try:
                Diseno3DController.iniciar_generacion(obj)
                self.message_user(
                    request,
                    f"Diseño 3D #{obj.pk} creado. Generación iniciada en Tripo AI. "
                    "Recarga la página en 2-5 minutos para ver el resultado.",
                )
            except Exception as exc:
                obj.estado        = "fallido"
                obj.error_mensaje = str(exc)
                obj.save(update_fields=["estado", "error_mensaje"])
                self.message_user(
                    request, f"Error al iniciar generación: {exc}", level="error"
                )
