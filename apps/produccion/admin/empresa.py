"""
admin/empresa.py
Gestión de Empresas y Usuarios de la plataforma.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group
from django.core.mail import send_mail

from apps.produccion.models import Empresa, PerfilUsuario, TipoMaterial, Material


# ── Catálogo inicial de materiales ────────────────────────────
_CATALOGO_INICIAL = {
    "PLA":    ["PLA Estándar", "PLA+", "PLA Matte", "PLA Silk", "PLA Madera"],
    "PETG":   ["PETG Estándar", "PETG Carbon"],
    "ABS":    ["ABS Estándar", "ABS+"],
    "ASA":    ["ASA Estándar"],
    "TPU":    ["TPU 95A", "TPU 85A"],
    "Resina": ["Resina Estándar", "Resina ABS-Like", "Resina Flexible"],
    "Nylon":  ["Nylon PA12", "Nylon PA6-GF"],
}


def sembrar_materiales(empresa):
    for tipo_nombre, materiales in _CATALOGO_INICIAL.items():
        tipo, _ = TipoMaterial.objects.get_or_create(empresa=empresa, nombre=tipo_nombre)
        for mat_nombre in materiales:
            Material.objects.get_or_create(empresa=empresa, tipo=tipo, nombre=mat_nombre)


# ══════════════════════════════════════════════════════════════
# Empresa Admin
# ══════════════════════════════════════════════════════════════
from django import forms
from django.utils.html import format_html


# ── Inline de usuarios de la empresa ─────────────────────────
class UsuariosEmpresaInline(admin.TabularInline):
    model        = PerfilUsuario
    extra        = 0
    can_delete   = False
    verbose_name = "Usuario"
    verbose_name_plural = "Usuarios de la empresa"
    fields       = ("usuario_link", "rol", "activo")
    readonly_fields = ("usuario_link", "rol", "activo")

    def usuario_link(self, obj):
        if obj.usuario_id:
            url = f"/admin/auth/user/{obj.usuario_id}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.usuario.username)
        return "—"
    usuario_link.short_description = "Usuario"

    def rol(self, obj):
        grupos = ", ".join(obj.usuario.groups.values_list("name", flat=True))
        return grupos or "— sin rol —"
    rol.short_description = "Rol"

    def activo(self, obj):
        return "✅" if obj.usuario.is_active else "❌"
    activo.short_description = "Activo"

    def has_add_permission(self, request, obj=None):
        return False


class EmpresaAdminForm(forms.ModelForm):
    admin_username = forms.CharField(
        label="Usuario admin de empresa",
        required=False,
        help_text="Se creará al guardar (solo en creación nueva)",
    )
    admin_password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text="Dejar vacío para generar automáticamente",
    )

    class Meta:
        model  = Empresa
        fields = "__all__"


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    form          = EmpresaAdminForm
    inlines       = [UsuariosEmpresaInline]
    list_display  = ("nombre", "nit", "email", "telefono", "total_usuarios", "activa")
    search_fields = ("nombre", "nit")
    list_filter   = ("activa",)

    def total_usuarios(self, obj):
        return obj.usuarios.count()
    total_usuarios.short_description = "Usuarios"
    fieldsets = (
        (None, {
            "fields": ("nombre", "nit", "email", "telefono", "direccion", "logo", "activa"),
        }),
        ("Crear usuario administrador", {
            "fields": ("admin_username", "admin_password"),
            "description": "Completa estos campos solo al crear una empresa nueva.",
        }),
    )

    def _puede_acceder(self, request):
        return request.user.is_superuser or request.user.has_perm("produccion.view_empresa")

    def get_model_perms(self, request):
        return super().get_model_perms(request) if self._puede_acceder(request) else {}

    def has_add_permission(self, request):
        return self._puede_acceder(request)

    def has_change_permission(self, request, obj=None):
        return self._puede_acceder(request)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.has_perm("produccion.delete_empresa")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if change:
            return

        username = form.cleaned_data.get("admin_username", "").strip()
        if not username:
            sembrar_materiales(obj)
            self.message_user(request, f"Materiales estándar creados para '{obj.nombre}'.")
            return

        password = form.cleaned_data.get("admin_password", "").strip() or User.objects.make_random_password(12)
        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_password(password)
            user.email    = obj.email or ""
            user.is_staff = True
            user.save()

            grupo, _ = Group.objects.get_or_create(name="Admin Empresa")
            user.groups.add(grupo)
            PerfilUsuario.objects.update_or_create(usuario=user, defaults={"empresa": obj})

            if obj.email:
                try:
                    send_mail(
                        subject=f"Bienvenido a SamyVerce — {obj.nombre}",
                        message=(
                            f"Hola,\n\n"
                            f"Tu empresa '{obj.nombre}' ha sido registrada en SamyVerce.\n\n"
                            f"Credenciales de acceso:\n"
                            f"  Usuario:    {username}\n"
                            f"  Contraseña: {password}\n\n"
                            f"Accede en: http://localhost:8000/admin/\n\n"
                            f"Por seguridad, cambia tu contraseña en el primer ingreso.\n\n"
                            f"— Equipo SamyVerce"
                        ),
                        from_email="noreply@samyverce.com",
                        recipient_list=[obj.email],
                        fail_silently=True,
                    )
                    self.message_user(request, f"Credenciales enviadas a {obj.email}")
                except Exception:
                    pass

            self.message_user(request, f"Usuario '{username}' creado y asignado a '{obj.nombre}'.")

        sembrar_materiales(obj)
        self.message_user(request, f"Materiales estándar creados para '{obj.nombre}'.")


# ══════════════════════════════════════════════════════════════
# Usuario Admin
# ══════════════════════════════════════════════════════════════
class PerfilInline(admin.StackedInline):
    model        = PerfilUsuario
    can_delete   = False
    verbose_name = "Empresa asignada"
    extra        = 1


admin.site.unregister(User)


@admin.register(User)
class UsuarioAdmin(UserAdmin):
    inlines = [PerfilInline]

    _PUEDE_GESTIONAR = {"Super Admin Plataforma", "Admin Empresa"}
    _GRUPOS_EMPRESA  = {"Admin Empresa", "Maker"}

    def _mis_grupos(self, request):
        return set(request.user.groups.values_list("name", flat=True))

    def _mi_empresa(self, request):
        try:
            return request.user.perfil.empresa
        except Exception:
            return None

    def _puede_gestionar(self, request):
        return request.user.is_superuser or bool(self._mis_grupos(request) & self._PUEDE_GESTIONAR)

    def get_model_perms(self, request):
        return super().get_model_perms(request) if self._puede_gestionar(request) else {}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or "Super Admin Plataforma" in self._mis_grupos(request):
            return qs
        empresa = self._mi_empresa(request)
        return qs.filter(perfil__empresa=empresa) if empresa else qs.none()

    def get_fieldsets(self, request, obj=None):
        if not request.user.is_superuser:
            if obj is None:
                return (
                    (None,          {"fields": ("username", "password1", "password2")}),
                    ("Información", {"fields": ("first_name", "last_name", "email")}),
                    ("Rol",         {"fields": ("groups",)}),
                )
            return (
                (None,          {"fields": ("username", "password")}),
                ("Información", {"fields": ("first_name", "last_name", "email")}),
                ("Estado",      {"fields": ("is_active",)}),
                ("Rol",         {"fields": ("groups",)}),
            )
        return super().get_fieldsets(request, obj)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "groups" and not request.user.is_superuser:
            kwargs["queryset"] = Group.objects.filter(name__in=self._GRUPOS_EMPRESA)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        obj.is_staff = True
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if "Admin Empresa" in self._mis_grupos(request):
            empresa = self._mi_empresa(request)
            if empresa:
                PerfilUsuario.objects.update_or_create(
                    usuario=form.instance, defaults={"empresa": empresa}
                )
