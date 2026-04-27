from django.db import models
from .empresa import Empresa
from .material import Material


class Insumo(models.Model):
    empresa  = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True, related_name="insumos", verbose_name="Empresa")
    producto = models.CharField(max_length=255, verbose_name="Producto")
    material = models.ForeignKey(Material, on_delete=models.PROTECT,
                                 null=True, blank=True, verbose_name="Material")
    precio           = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, verbose_name="Precio (COP)")
    cantidad_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Cantidad inicial (g)")
    cantidad_final   = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Cantidad final (g)")
    actualizado_en   = models.DateTimeField(auto_now=True)

    @property
    def diferencia(self):
        return round(float(self.cantidad_final) - float(self.cantidad_inicial), 2)

    @property
    def stock_disponible(self):
        return float(self.cantidad_final)

    class Meta:
        ordering        = ["id"]
        verbose_name    = "Insumo"
        verbose_name_plural = "Insumos"

    def __str__(self):
        return self.producto
