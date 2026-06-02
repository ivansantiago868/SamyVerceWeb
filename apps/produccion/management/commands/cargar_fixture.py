from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db.models.signals import post_save
from django.contrib.auth.models import User

from apps.produccion.signals import crear_perfil_usuario, crear_insumo_desde_gasto, crear_tarea_desde_pedido
from apps.produccion.models.gasto import Gasto
from apps.produccion.models.pedido import Pedido


class Command(BaseCommand):
    help = "Carga un fixture desconectando signals para evitar duplicados"

    def add_arguments(self, parser):
        parser.add_argument("fixture", nargs="+", type=str)

    def handle(self, *args, **options):
        post_save.disconnect(crear_perfil_usuario, sender=User)
        post_save.disconnect(crear_insumo_desde_gasto, sender=Gasto)
        post_save.disconnect(crear_tarea_desde_pedido, sender=Pedido)
        try:
            for fixture in options["fixture"]:
                self.stdout.write(f"Cargando {fixture}...")
                call_command("loaddata", fixture, verbosity=1)
        finally:
            post_save.connect(crear_perfil_usuario, sender=User)
            post_save.connect(crear_insumo_desde_gasto, sender=Gasto)
            post_save.connect(crear_tarea_desde_pedido, sender=Pedido)
        self.stdout.write(self.style.SUCCESS("Fixture cargado exitosamente."))
