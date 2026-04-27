from django.db import models
from .empresa import Empresa


class Impresora(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True, related_name="impresoras", verbose_name="Empresa")

    class Tipo(models.TextChoices):
        FILAMENTO = "Filamento", "Filamento (FDM)"
        RESINA    = "Resina",    "Resina (SLA/MSLA)"
        LASER     = "Lacer",     "Láser"

    nombre                    = models.CharField(max_length=100)
    tipo                      = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.FILAMENTO)
    costo                     = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Costo (COP)")
    vida_util_horas           = models.PositiveIntegerField(verbose_name="Vida útil estimada (horas)")
    costo_mantenimiento_anual = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Costo mantenimiento anual (COP)")
    consumo_promedio_kw       = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True, verbose_name="Consumo promedio (kW)")
    activa                    = models.BooleanField(default=True)

    @property
    def depreciacion_por_hora(self):
        if self.vida_util_horas and self.costo is not None:
            return round(float(self.costo) / self.vida_util_horas, 4)
        return 0

    @property
    def mantenimiento_por_hora(self):
        if self.costo_mantenimiento_anual is not None:
            return round(float(self.costo_mantenimiento_anual) / 8760, 4)
        return 0

    class Meta:
        ordering        = ["nombre"]
        verbose_name    = "Impresora"
        verbose_name_plural = "Impresoras"

    def __str__(self):
        return self.nombre
