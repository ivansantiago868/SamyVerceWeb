from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models.empresa import PerfilUsuario
from .models.gasto import Gasto
from .models.insumo import Insumo
from .models.pedido import Pedido
from .models.venta_tarea import Tarea


@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.get_or_create(usuario=instance)


@receiver(post_save, sender=Gasto)
def crear_insumo_desde_gasto(sender, instance, created, **kwargs):
    if created:
        Insumo.objects.create(
            empresa=instance.empresa,
            producto=f"[CUUI-{instance.cuui}] {instance.articulo}",
            material=instance.material,
            precio=instance.costo,
            cantidad_inicial=0,
            cantidad_final=instance.peso,
        )


@receiver(post_save, sender=Pedido)
def crear_tarea_desde_pedido(sender, instance, created, **kwargs):
    if created:
        Tarea.objects.create(
            empresa       = instance.empresa,
            pedido        = instance,
            prioridad     = instance.prioridad,
            cliente       = instance.cliente,
            producto      = instance.pieza.nombre if instance.pieza else "",
            cantidad      = instance.cantidad,
            precio_total  = instance.precio_total,
            fecha_entrega = instance.fecha_entrega,
            maquina       = instance.maquina,
            estado        = Tarea.Estado.PENDIENTE,
            descripcion   = instance.descripcion,
        )
