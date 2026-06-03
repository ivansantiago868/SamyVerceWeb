from django.db import models
from django.db.models import Max
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .empresa import Empresa
from .inventario_pieza import InventarioPieza
from .insumo import Insumo
from .upload_paths import upload_figura_imagen, upload_figura_procesada


class Figura(models.Model):
    empresa     = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True,
                                    related_name="figuras", verbose_name="Empresa")
    nombre      = models.CharField(max_length=255, verbose_name="Nombre de la figura")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    archivo_3mf = models.FileField(upload_to="figuras/3mf/", null=True, blank=True, verbose_name="Archivo 3MF")
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
    figura           = models.ForeignKey(Figura, on_delete=models.CASCADE,
                                         related_name="imagenes", verbose_name="Figura")
    imagen           = models.ImageField(upload_to=upload_figura_imagen, verbose_name="Imagen")
    imagen_procesada = models.ImageField(upload_to=upload_figura_procesada, null=True, blank=True, verbose_name="Imagen IA (estudio)")
    orden            = models.PositiveSmallIntegerField(default=0, verbose_name="Orden")

    class Meta:
        ordering        = ["orden", "id"]
        verbose_name    = "Imagen de figura"
        verbose_name_plural = "Imágenes de figura"

    def __str__(self):
        return f"Imagen #{self.orden} — {self.figura.nombre}"

    def save(self, *args, **kwargs):
        if not self.pk and self.figura_id is not None:
            max_orden = FiguraImagen.objects.filter(figura_id=self.figura_id).aggregate(
                m=Max("orden")
            )["m"]
            self.orden = (max_orden + 1) if max_orden is not None else 0

        imagen_cambio = True
        if self.pk:
            try:
                anterior = FiguraImagen.objects.values_list("imagen", flat=True).get(pk=self.pk)
                imagen_cambio = anterior != self.imagen.name
            except FiguraImagen.DoesNotExist:
                pass
        super().save(*args, **kwargs)
        if imagen_cambio and self.imagen and not getattr(self, "_skip_ia", False):
            from apps.produccion.services.vertex_imagen import procesar_en_background
            procesar_en_background(FiguraImagen, self.pk, self.imagen.url)


def _borrar_campo_drive(field):
    if field and field.name and "/" not in field.name and "." not in field.name:
        try:
            field.storage.delete(field.name)
        except Exception:
            pass


@receiver(post_delete, sender=FiguraImagen)
def borrar_archivos_figura_imagen(sender, instance, **kwargs):
    _borrar_campo_drive(instance.imagen)
    _borrar_campo_drive(instance.imagen_procesada)


class FiguraPieza(models.Model):
    figura   = models.ForeignKey(Figura, on_delete=models.CASCADE,
                                 related_name="figura_piezas", verbose_name="Figura")
    pieza    = models.ForeignKey(InventarioPieza, on_delete=models.PROTECT,
                                 related_name="en_figuras", verbose_name="Pieza")
    insumo   = models.ForeignKey(Insumo, on_delete=models.PROTECT,
                                 null=True, blank=True, verbose_name="Insumo / Material")
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
