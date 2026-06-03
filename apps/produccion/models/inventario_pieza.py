from django.db import models
from django.db.models import Max
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .empresa import Empresa
from .upload_paths import (
    upload_inventario_imagen, upload_inventario_procesada,
    upload_pieza_imagen, upload_pieza_procesada,
)


class InventarioPieza(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True, related_name="piezas", verbose_name="Empresa")
    """
    Catálogo de piezas con estructura de costos completa.
    Sirve de base para el Cotizador y guarda histórico de cálculos.
    """

    nombre                   = models.CharField(max_length=255, verbose_name="Nombre de la pieza")
    peso_gramos              = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Peso estimado (g)")
    tiempo_impresion_horas   = models.DecimalField(max_digits=8,  decimal_places=2, verbose_name="Tiempo de impresión (h)")
    tiempo_postproceso_horas = models.DecimalField(max_digits=8,  decimal_places=2, default=0, verbose_name="Tiempo post-procesado (h)")
    costo_empaque            = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Costo empaque (COP)")
    costo_material           = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Costo material (COP)")
    costo_energia            = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Costo energía (COP)")
    costo_tiempo             = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Costo tiempo (COP)")
    subtotal_produccion      = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Subtotal producción (COP)")
    amortizacion_fallos      = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Amortización fallos (COP)")
    depreciacion_pieza       = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Depreciación por pieza (COP)")
    mantenimiento_preventivo = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Mantenimiento preventivo (COP)")
    costo_total_real         = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Costo total real (COP)")
    precio_venta_sugerido    = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Precio venta sugerido (COP)")
    archivo_3mf              = models.FileField(upload_to="piezas/3mf/", null=True, blank=True, verbose_name="Archivo 3MF")
    imagen                   = models.ImageField(upload_to=upload_inventario_imagen, null=True, blank=True, verbose_name="Imagen de la pieza")
    imagen_procesada         = models.ImageField(upload_to=upload_inventario_procesada, null=True, blank=True, verbose_name="Imagen IA (estudio)")
    url_referencia           = models.URLField(max_length=500, null=True, blank=True, verbose_name="URL de referencia")
    actualizado_en           = models.DateTimeField(auto_now=True)

    class Meta:
        ordering            = ["nombre"]
        verbose_name        = "Pieza"
        verbose_name_plural = "Piezas"

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        imagen_cambio = True
        if self.pk:
            try:
                anterior = InventarioPieza.objects.values_list("imagen", flat=True).get(pk=self.pk)
                imagen_actual = self.imagen.name if self.imagen else None
                imagen_cambio = anterior != imagen_actual
            except InventarioPieza.DoesNotExist:
                pass
        super().save(*args, **kwargs)
        if imagen_cambio and self.imagen:
            from apps.produccion.services.vertex_imagen import procesar_en_background
            procesar_en_background(InventarioPieza, self.pk, self.imagen.url)


class PiezaImagen(models.Model):
    pieza            = models.ForeignKey(
        InventarioPieza,
        on_delete=models.CASCADE,
        related_name="imagenes",
        verbose_name="Pieza",
    )
    imagen           = models.ImageField(upload_to=upload_pieza_imagen, verbose_name="Imagen")
    imagen_procesada = models.ImageField(upload_to=upload_pieza_procesada, null=True, blank=True, verbose_name="Imagen IA (estudio)")
    orden            = models.PositiveSmallIntegerField(default=0, verbose_name="Orden")

    class Meta:
        ordering            = ["orden", "id"]
        verbose_name        = "Imagen de pieza"
        verbose_name_plural = "Imágenes de pieza"

    def __str__(self):
        return f"Imagen #{self.orden} — {self.pieza.nombre}"

    def save(self, *args, **kwargs):
        if not self.pk and self.pieza_id is not None:
            max_orden = PiezaImagen.objects.filter(pieza_id=self.pieza_id).aggregate(
                m=Max("orden")
            )["m"]
            self.orden = (max_orden + 1) if max_orden is not None else 0

        imagen_cambio = True
        if self.pk:
            try:
                anterior = PiezaImagen.objects.values_list("imagen", flat=True).get(pk=self.pk)
                imagen_cambio = anterior != self.imagen.name
            except PiezaImagen.DoesNotExist:
                pass
        super().save(*args, **kwargs)
        if imagen_cambio and self.imagen:
            from apps.produccion.services.vertex_imagen import procesar_en_background
            procesar_en_background(PiezaImagen, self.pk, self.imagen.url)


def _borrar_campo_drive(field):
    """Elimina un archivo de Drive si el campo tiene un ID válido."""
    if field and field.name and "/" not in field.name and "." not in field.name:
        try:
            field.storage.delete(field.name)
        except Exception:
            pass


@receiver(post_delete, sender=PiezaImagen)
def borrar_archivos_pieza_imagen(sender, instance, **kwargs):
    _borrar_campo_drive(instance.imagen)
    _borrar_campo_drive(instance.imagen_procesada)


@receiver(post_delete, sender=InventarioPieza)
def borrar_archivos_inventario_pieza(sender, instance, **kwargs):
    _borrar_campo_drive(instance.imagen)
    _borrar_campo_drive(instance.imagen_procesada)
