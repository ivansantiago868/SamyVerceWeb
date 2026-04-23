from django.db import models, transaction
from .material import Material


class Gasto(models.Model):

    cuui     = models.PositiveIntegerField(unique=True, editable=False, verbose_name="CUUI")
    articulo = models.CharField(max_length=255, verbose_name="Artículo")
    material = models.ForeignKey(Material, on_delete=models.PROTECT,
                                 null=True, blank=True, verbose_name="Material")
    peso     = models.DecimalField(max_digits=10, decimal_places=2, default=1000, verbose_name="Peso (g)")
    costo    = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Costo (COP)")
    fecha    = models.DateField(verbose_name="Fecha de compra")

    def save(self, *args, **kwargs):
        if not self.cuui:
            with transaction.atomic():
                ultimo = Gasto.objects.select_for_update().order_by("-cuui").first()
                self.cuui = (ultimo.cuui + 1) if ultimo else 1
        super().save(*args, **kwargs)

    class Meta:
        ordering        = ["-fecha", "cuui"]
        verbose_name    = "Gasto"
        verbose_name_plural = "Gastos"

    def __str__(self):
        return f"#{self.cuui} — {self.articulo}"
