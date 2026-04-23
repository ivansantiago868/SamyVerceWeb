from django.db import models


class InventarioPieza(models.Model):
    """
    Catálogo de piezas con estructura de costos completa.
    Sirve de base para el Cotizador y guarda histórico de cálculos.
    """

    nombre                   = models.CharField(max_length=255, verbose_name="Nombre de la pieza")
    peso_gramos              = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Peso estimado (g)")
    tiempo_impresion_horas   = models.DecimalField(max_digits=8,  decimal_places=2, verbose_name="Tiempo de impresión (h)")
    tiempo_postproceso_horas = models.DecimalField(max_digits=8,  decimal_places=2, default=0, verbose_name="Tiempo post-procesado (h)")
    costo_empaque            = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Costo empaque (COP)")
    # Costos calculados — guardados como histórico
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
    imagen                   = models.ImageField(upload_to="piezas/imagenes/", null=True, blank=True, verbose_name="Imagen de la pieza")
    url_referencia           = models.URLField(max_length=500, null=True, blank=True, verbose_name="URL de referencia")
    actualizado_en           = models.DateTimeField(auto_now=True)

    class Meta:
        ordering        = ["nombre"]
        verbose_name        = "Pieza"
        verbose_name_plural = "Piezas"

    def __str__(self):
        return self.nombre
