from django.db import models
from .cliente import Cliente
from .empresa import Empresa
from .pedido import Pedido
from .impresora import Impresora



class Venta(models.Model):
    empresa   = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True, related_name="ventas", verbose_name="Empresa")
    pedidos   = models.ManyToManyField(Pedido, blank=True, related_name="ventas", verbose_name="Pedidos")
    fecha     = models.DateField(verbose_name="Fecha de cotización")
    notas     = models.TextField(blank=True, verbose_name="Notas adicionales")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ["-fecha"]
        verbose_name        = "Venta"
        verbose_name_plural = "Ventas"

    def __str__(self):
        nums = [p.numero_pedido for p in self.pedidos.all() if p.numero_pedido]
        if nums:
            return f"Cotización #{self.id} — {', '.join(nums)}"
        return f"Cotización #{self.id}"


class Tarea(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True, related_name="tareas", verbose_name="Empresa")

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

    prioridad     = models.CharField(max_length=10, choices=Prioridad.choices, default=Prioridad.MEDIO)
    pedido        = models.ForeignKey(Pedido,   on_delete=models.CASCADE,  null=True, blank=True, related_name="tareas")
    cliente       = models.ForeignKey(Cliente,  on_delete=models.SET_NULL, null=True, blank=True)
    cliente_texto = models.CharField(max_length=255, blank=True, verbose_name="Cliente (texto libre)")
    producto      = models.CharField(max_length=255)
    cantidad      = models.PositiveIntegerField(default=0)
    realizados    = models.PositiveIntegerField(default=0)
    precio_total  = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Precio total (COP)")
    fecha_entrega = models.DateField(null=True, blank=True)
    maquina       = models.ForeignKey(Impresora, on_delete=models.SET_NULL, null=True, blank=True)
    estado        = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    descripcion   = models.TextField(blank=True)
    creado_en     = models.DateTimeField(auto_now_add=True)

    @property
    def restantes(self):
        return self.cantidad - self.realizados

    class Meta:
        ordering        = ["fecha_entrega", "prioridad"]
        verbose_name    = "Tarea"
        verbose_name_plural = "Tareas"

    def __str__(self):
        return f"#{self.id} — {self.producto} [{self.estado}]"
