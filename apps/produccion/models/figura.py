from django.db import models
from .empresa import Empresa
from .inventario_pieza import InventarioPieza


class Figura(models.Model):
    empresa     = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True,
                                    related_name="figuras", verbose_name="Empresa")
    nombre      = models.CharField(max_length=255, verbose_name="Nombre de la figura")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    creado_en   = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    @property
    def costo_total(self):
        return sum(fp.subtotal_costo for fp in self.figura_piezas.select_related("pieza").all())

    @property
    def precio_total(self):
        return sum(fp.subtotal_precio for fp in self.figura_piezas.select_related("pieza").all())

    @property
    def total_piezas(self):
        return sum(fp.cantidad for fp in self.figura_piezas.all())

    class Meta:
        ordering        = ["nombre"]
        verbose_name    = "Figura"
        verbose_name_plural = "Figuras"

    def __str__(self):
        return self.nombre


class FiguraImagen(models.Model):
    figura = models.ForeignKey(Figura, on_delete=models.CASCADE,
                               related_name="imagenes", verbose_name="Figura")
    imagen = models.ImageField(upload_to="figuras/imagenes/", verbose_name="Imagen")
    orden  = models.PositiveSmallIntegerField(default=0, verbose_name="Orden")

    class Meta:
        ordering        = ["orden", "id"]
        verbose_name    = "Imagen de figura"
        verbose_name_plural = "Imágenes de figura"

    def __str__(self):
        return f"Imagen #{self.orden} — {self.figura.nombre}"


class FiguraPieza(models.Model):
    figura   = models.ForeignKey(Figura, on_delete=models.CASCADE,
                                 related_name="figura_piezas", verbose_name="Figura")
    pieza    = models.ForeignKey(InventarioPieza, on_delete=models.PROTECT,
                                 related_name="en_figuras", verbose_name="Pieza")
    cantidad = models.PositiveIntegerField(default=1, verbose_name="Cantidad")

    @property
    def subtotal_costo(self):
        return round(float(self.pieza.costo_total_real) * self.cantidad, 2)

    @property
    def subtotal_precio(self):
        return round(float(self.pieza.precio_venta_sugerido) * self.cantidad, 2)

    class Meta:
        ordering        = ["pieza__nombre"]
        unique_together = [("figura", "pieza")]
        verbose_name    = "Pieza de figura"
        verbose_name_plural = "Piezas de figura"

    def __str__(self):
        return f"{self.pieza.nombre} × {self.cantidad}"
