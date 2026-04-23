from django.db import models


class TipoMaterial(models.Model):
    nombre = models.CharField(max_length=50, unique=True, verbose_name="Tipo")

    class Meta:
        ordering        = ["nombre"]
        verbose_name    = "Tipo de material"
        verbose_name_plural = "Tipos de material"

    def __str__(self):
        return self.nombre


class Material(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Material")
    tipo   = models.ForeignKey(TipoMaterial, on_delete=models.PROTECT,
                               related_name="materiales", verbose_name="Tipo")

    class Meta:
        ordering        = ["tipo__nombre", "nombre"]
        unique_together = [("nombre", "tipo")]
        verbose_name    = "Material"
        verbose_name_plural = "Materiales"

    def __str__(self):
        return f"{self.tipo.nombre} — {self.nombre}"
