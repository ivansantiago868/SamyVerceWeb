"""
admin/mixins.py
Mixin multi-tenant, widgets de arrastrar-soltar y formularios compartidos.
"""
import datetime

from django import forms
from django.contrib import admin
from django.utils.html import format_html

from apps.produccion.models import InventarioPieza, PiezaImagen, Venta

# ── Grupos de plataforma ──────────────────────────────────────
GRUPOS_PLATAFORMA = {"Super Admin Plataforma"}


# ══════════════════════════════════════════════════════════════
# Mixin multi-tenant
# ══════════════════════════════════════════════════════════════
class EmpresaMixin:
    """Filtra datos por empresa y controla visibilidad según rol."""

    grupos_empresa: set = set()

    def _grupos(self, request):
        return set(request.user.groups.values_list("name", flat=True))

    def _empresa(self, request):
        if request.user.is_superuser:
            return None
        try:
            return request.user.perfil.empresa
        except Exception:
            return None

    def _es_plataforma(self, request):
        if request.user.is_superuser:
            return False
        return bool(self._grupos(request) & GRUPOS_PLATAFORMA)

    def get_model_perms(self, request):
        if request.user.is_superuser:
            return super().get_model_perms(request)
        if self._es_plataforma(request):
            return {}
        if self.grupos_empresa and not (self._grupos(request) & self.grupos_empresa):
            return {}
        return super().get_model_perms(request)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        empresa = self._empresa(request)
        if empresa is not None:
            qs = qs.filter(empresa=empresa)
        return qs

    def get_exclude(self, request, obj=None):
        exclude = list(super().get_exclude(request, obj) or [])
        if not request.user.is_superuser and "empresa" not in exclude:
            exclude.append("empresa")
        return exclude

    def save_model(self, request, obj, form, change):
        empresa = self._empresa(request)
        if empresa is not None:
            obj.empresa = empresa
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        empresa = self._empresa(request)
        if empresa is not None and hasattr(db_field.related_model, "empresa"):
            kwargs["queryset"] = db_field.related_model.objects.filter(empresa=empresa)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        empresa = self._empresa(request)
        if empresa is not None and hasattr(db_field.related_model, "empresa"):
            kwargs["queryset"] = db_field.related_model.objects.filter(empresa=empresa)
        return super().formfield_for_manytomany(db_field, request, **kwargs)


# ══════════════════════════════════════════════════════════════
# Widgets drag-drop
# ══════════════════════════════════════════════════════════════
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


# ══════════════════════════════════════════════════════════════
# Formularios
# ══════════════════════════════════════════════════════════════
class InventarioPiezaForm(forms.ModelForm):
    class Meta:
        model   = InventarioPieza
        exclude = ["empresa"]
        widgets = {
            "archivo_3mf": DragDropFileWidget(),
            "imagen":      DragDropImageWidget(),
        }


class PiezaImagenInlineForm(forms.ModelForm):
    class Meta:
        model   = PiezaImagen
        fields  = ("imagen",)
        widgets = {"imagen": DragDropImageWidget()}


class PiezaImagenInline(admin.TabularInline):
    model           = PiezaImagen
    form            = PiezaImagenInlineForm
    extra           = 1
    can_delete      = True
    fields          = ("imagen", "orden_display", "preview")
    readonly_fields = ("orden_display", "preview")
    verbose_name_plural = "Imágenes de la pieza (marca ✓ en 'Eliminar' para borrar)"

    @admin.display(description="Orden")
    def orden_display(self, obj):
        return obj.orden if obj.pk else "—"

    @admin.display(description="Vista previa")
    def preview(self, obj):
        if obj.imagen:
            return format_html(
                '<img src="{}" style="height:72px;border-radius:6px;'
                'object-fit:cover;box-shadow:0 1px 4px rgba(0,0,0,.2)">',
                obj.imagen.url,
            )
        return format_html('<span style="color:#aaa;font-size:11px">—</span>')


class VentaForm(forms.ModelForm):
    class Meta:
        model  = Venta
        fields = ("pedidos", "fecha", "notas")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fecha"].initial = datetime.date.today


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
    fecha    = forms.DateField(
        initial=datetime.date.today,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Fecha de compra",
    )
    color    = forms.CharField(
        required=False, initial="#000000", label="Color",
        help_text="Color del material comprado (ej. color del filamento).",
        widget=forms.TextInput(attrs={"type": "color", "style": "width:52px;height:32px;padding:2px"}),
    )
    unidades = forms.IntegerField(min_value=1, initial=1, label="Unidades")
