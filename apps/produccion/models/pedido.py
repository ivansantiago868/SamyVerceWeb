from django.db import models
from .cliente import Cliente
from .empresa import Empresa
from .insumo import Insumo
from .impresora import Impresora
from .inventario_pieza import InventarioPieza


class Pedido(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True, related_name="pedidos", verbose_name="Empresa")

    class Prioridad(models.TextChoices):
        ALTO  = "Alto",  "Alto"
        MEDIO = "Medio", "Medio"
        BAJO  = "Bajo",  "Bajo"

    class Estado(models.TextChoices):
        PENDIENTE   = "Pendiente",      "Pendiente"
        EN_COLA     = "En cola",        "En cola"
        IMPRIMIENDO = "Imprimiendo",    "Imprimiendo"
        POSTPROCESO = "Post-procesado", "Post-procesado"
        LISTO       = "Listo",          "Listo"
        ENTREGADO   = "Entregado",      "Entregado"
        CANCELADO   = "Cancelado",      "Cancelado"

    numero_pedido = models.CharField(max_length=50, blank=True, verbose_name="Número de pedido", db_index=True)
    prioridad     = models.CharField(max_length=10, choices=Prioridad.choices, default=Prioridad.MEDIO)
    cliente       = models.ForeignKey(Cliente,        on_delete=models.PROTECT,  null=True, blank=True)
    pieza         = models.ForeignKey(InventarioPieza, on_delete=models.PROTECT,  null=True, blank=True, verbose_name="Pieza")
    material      = models.ForeignKey(Insumo,          on_delete=models.PROTECT,  null=True, blank=True, verbose_name="Material")
    cantidad      = models.PositiveIntegerField(default=0)
    realizados    = models.PositiveIntegerField(default=0)
    gr_pieza      = models.DecimalField(max_digits=8,  decimal_places=2, default=0, verbose_name="Gramos por pieza")
    precio_unidad = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Precio unitario (COP)")
    fecha_entrega = models.DateField(null=True, blank=True)
    maquina       = models.ForeignKey(Impresora, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Máquina")
    estado        = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    descripcion   = models.TextField(blank=True)
    creado_en     = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.pieza_id:
            self.gr_pieza     = self.pieza.peso_gramos
            self.precio_unidad = self.pieza.precio_venta_sugerido
        super().save(*args, **kwargs)

    @property
    def restantes(self):
        return self.cantidad - self.realizados

    @property
    def peso_total(self):
        return round(float(self.gr_pieza) * self.cantidad, 2)

    @property
    def precio_total(self):
        return round(float(self.precio_unidad) * self.cantidad, 2)

    class Meta:
        ordering        = ["-creado_en"]
        verbose_name    = "Pedido"
        verbose_name_plural = "Pedidos"

    def __str__(self):
        nombre_cliente  = self.cliente.nombre if self.cliente else "Sin cliente"
        nombre_producto = self.pieza.nombre if self.pieza else "Sin pieza"
        prefijo = f"[{self.numero_pedido}] " if self.numero_pedido else ""
        return f"{prefijo}#{self.id} — {nombre_cliente} | {nombre_producto}"
