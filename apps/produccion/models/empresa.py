from django.contrib.auth.models import User
from django.db import models


class Empresa(models.Model):
    nombre    = models.CharField(max_length=255, verbose_name="Nombre / Razón social")
    nit       = models.CharField(max_length=30, blank=True, verbose_name="NIT")
    email     = models.EmailField(blank=True)
    telefono  = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    direccion = models.TextField(blank=True, verbose_name="Dirección")
    logo      = models.ImageField(upload_to="empresas/logos/", null=True, blank=True, verbose_name="Logo")
    activa    = models.BooleanField(default=True, verbose_name="Activa")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ["nombre"]
        verbose_name        = "Empresa"
        verbose_name_plural = "Empresas"

    def __str__(self):
        return self.nombre


class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil")
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="usuarios",
        verbose_name="Empresa",
    )

    class Meta:
        verbose_name        = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuario"

    def __str__(self):
        return f"{self.usuario.username} — {self.empresa}"
