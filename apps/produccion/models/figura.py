from django.db import models
from django.db.models import Max
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .empresa import Empresa
from .inventario_pieza import InventarioPieza
from .insumo import Insumo
from .upload_paths import upload_figura_imagen, upload_figura_procesada, upload_figura_color, upload_figura_tipo
from config.google_drive_storage import borrar_archivo_drive as _borrar_campo_drive


class CategoriaFigura(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True,
                                related_name="categorias_figura", verbose_name="Empresa")
    nombre  = models.CharField(max_length=100, verbose_name="Categoría")

    class Meta:
        ordering        = ["nombre"]
        verbose_name    = "Categoría de figura"
        verbose_name_plural = "Categorías de figura"

    def __str__(self):
        return self.nombre


class EtiquetaFigura(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True,
                                related_name="etiquetas_figura", verbose_name="Empresa")
    nombre  = models.CharField(max_length=100, verbose_name="Etiqueta")

    class Meta:
        ordering        = ["nombre"]
        verbose_name    = "Etiqueta de figura"
        verbose_name_plural = "Etiquetas de figura"

    def __str__(self):
        return self.nombre


class Figura(models.Model):
    empresa     = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True,
                                    related_name="figuras", verbose_name="Empresa")
    categorias  = models.ManyToManyField(CategoriaFigura, blank=True,
                                         related_name="figuras", verbose_name="Categorías")
    etiquetas   = models.ManyToManyField(EtiquetaFigura, blank=True,
                                         related_name="figuras", verbose_name="Etiquetas")
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

    @property
    def primera_imagen_url(self):
        primera = self.imagenes.first()
        if not primera:
            return None
        if primera.imagen_procesada:
            return primera.imagen_procesada.url
        if primera.imagen:
            return primera.imagen.url
        return None

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
    ia_error         = models.TextField(blank=True, default="", verbose_name="Error de procesamiento IA")
    orden            = models.PositiveSmallIntegerField(default=0, verbose_name="Orden")
    IA, NORMAL, AMBAS = "ia", "normal", "ambas"
    MODO_CARRUSEL_CHOICES = [
        (IA,     "Solo IA"),
        (NORMAL, "Solo original"),
        (AMBAS,  "Ambas"),
    ]
    modo_carrusel = models.CharField(
        max_length=10,
        choices=MODO_CARRUSEL_CHOICES,
        default=IA,
        verbose_name="Mostrar en carrusel",
        help_text="Solo IA: muestra la imagen IA si existe (si no, cae a la original). "
                   "Solo original: muestra siempre la imagen normal. "
                   "Ambas: muestra las dos como fotos separadas en el carrusel.",
    )

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

        imagen_anterior = None
        imagen_cambio = True
        if self.pk:
            try:
                anterior_obj = FiguraImagen.objects.only("imagen").get(pk=self.pk)
                imagen_anterior = anterior_obj.imagen
                imagen_cambio = imagen_anterior.name != self.imagen.name
            except FiguraImagen.DoesNotExist:
                pass
        super().save(*args, **kwargs)
        if imagen_cambio and imagen_anterior:
            _borrar_campo_drive(imagen_anterior)
        if imagen_cambio and self.imagen and not getattr(self, "_skip_ia", False):
            from apps.produccion.services.vertex_imagen import procesar_en_background
            procesar_en_background(FiguraImagen, self.pk, self.imagen.url)


@receiver(post_delete, sender=FiguraImagen)
def borrar_archivos_figura_imagen(sender, instance, **kwargs):
    _borrar_campo_drive(instance.imagen)
    _borrar_campo_drive(instance.imagen_procesada)


class FiguraArchivo3MF(models.Model):
    figura  = models.ForeignKey(Figura, on_delete=models.CASCADE,
                                related_name="archivos_3mf", verbose_name="Figura")
    archivo = models.FileField(upload_to="figuras/3mf/", verbose_name="Archivo 3MF")
    nombre  = models.CharField(max_length=255, blank=True, verbose_name="Nombre / descripción")
    orden   = models.PositiveSmallIntegerField(default=0, verbose_name="Orden")

    class Meta:
        ordering        = ["orden", "id"]
        verbose_name    = "Archivo 3MF de figura"
        verbose_name_plural = "Archivos 3MF de figura"

    def __str__(self):
        return self.nombre or f"3MF #{self.orden} — {self.figura.nombre}"

    @property
    def descarga_url(self):
        if not self.archivo:
            return None
        name = self.archivo.name
        # IDs de Drive no tienen "/" ni "."; con ese ID, .url() usa el dominio
        # de miniaturas de imágenes (lh3.googleusercontent.com), que no sirve
        # bien archivos binarios como .3mf. Se arma el link de descarga directa.
        if name and "/" not in name and "." not in name:
            return f"https://drive.google.com/uc?export=download&id={name}"
        return self.archivo.url

    def save(self, *args, **kwargs):
        if not self.pk and self.figura_id is not None:
            max_orden = FiguraArchivo3MF.objects.filter(figura_id=self.figura_id).aggregate(
                m=Max("orden")
            )["m"]
            self.orden = (max_orden + 1) if max_orden is not None else 0
        super().save(*args, **kwargs)


@receiver(post_delete, sender=FiguraArchivo3MF)
def borrar_archivo_3mf_figura(sender, instance, **kwargs):
    _borrar_campo_drive(instance.archivo)


class FiguraColor(models.Model):
    """Opción de color de una figura, con su propia foto representativa."""
    figura    = models.ForeignKey(Figura, on_delete=models.CASCADE,
                                  related_name="colores", verbose_name="Figura")
    nombre    = models.CharField(max_length=100, verbose_name="Nombre del color")
    color_hex = models.CharField(max_length=7, blank=True, verbose_name="Color (hex)",
                                 help_text="Opcional, solo para mostrar una muestra. Ej: #FF6B35")
    imagen    = models.ImageField(upload_to=upload_figura_color, verbose_name="Imagen de este color")
    orden     = models.PositiveSmallIntegerField(default=0, verbose_name="Orden")

    class Meta:
        ordering        = ["orden", "id"]
        verbose_name    = "Color de figura"
        verbose_name_plural = "Colores de figura"

    def __str__(self):
        return f"{self.nombre} — {self.figura.nombre}"

    def save(self, *args, **kwargs):
        if not self.pk and self.figura_id is not None:
            max_orden = FiguraColor.objects.filter(figura_id=self.figura_id).aggregate(
                m=Max("orden")
            )["m"]
            self.orden = (max_orden + 1) if max_orden is not None else 0

        imagen_anterior = None
        imagen_cambio = True
        if self.pk:
            try:
                anterior_obj = FiguraColor.objects.only("imagen").get(pk=self.pk)
                imagen_anterior = anterior_obj.imagen
                imagen_cambio = imagen_anterior.name != self.imagen.name
            except FiguraColor.DoesNotExist:
                pass
        super().save(*args, **kwargs)
        if imagen_cambio and imagen_anterior:
            _borrar_campo_drive(imagen_anterior)


@receiver(post_delete, sender=FiguraColor)
def borrar_imagen_figura_color(sender, instance, **kwargs):
    _borrar_campo_drive(instance.imagen)


class FiguraTipo(models.Model):
    """Variante/tipo de una figura (ej. 'Para NES', 'Para Super Nintendo')."""
    figura      = models.ForeignKey(Figura, on_delete=models.CASCADE,
                                    related_name="tipos", verbose_name="Figura")
    nombre      = models.CharField(max_length=100, verbose_name="Nombre del tipo",
                                   help_text='Ej: "Para NES", "Para Super Nintendo".')
    descripcion = models.CharField(max_length=255, blank=True, verbose_name="Descripción / notas")
    imagen      = models.ImageField(upload_to=upload_figura_tipo, null=True, blank=True,
                                    verbose_name="Imagen de este tipo",
                                    help_text="Se muestra en el carrusel de imágenes de la figura.")
    orden       = models.PositiveSmallIntegerField(default=0, verbose_name="Orden")

    class Meta:
        ordering        = ["orden", "id"]
        verbose_name    = "Tipo de figura"
        verbose_name_plural = "Tipos de figura"

    def __str__(self):
        return f"{self.nombre} — {self.figura.nombre}"

    def save(self, *args, **kwargs):
        if not self.pk and self.figura_id is not None:
            max_orden = FiguraTipo.objects.filter(figura_id=self.figura_id).aggregate(
                m=Max("orden")
            )["m"]
            self.orden = (max_orden + 1) if max_orden is not None else 0

        imagen_anterior = None
        imagen_cambio = True
        if self.pk:
            try:
                anterior_obj = FiguraTipo.objects.only("imagen").get(pk=self.pk)
                imagen_anterior = anterior_obj.imagen
                imagen_cambio = imagen_anterior.name != self.imagen.name
            except FiguraTipo.DoesNotExist:
                pass
        super().save(*args, **kwargs)
        if imagen_cambio and imagen_anterior:
            _borrar_campo_drive(imagen_anterior)


@receiver(post_delete, sender=FiguraTipo)
def borrar_imagen_figura_tipo(sender, instance, **kwargs):
    _borrar_campo_drive(instance.imagen)


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
