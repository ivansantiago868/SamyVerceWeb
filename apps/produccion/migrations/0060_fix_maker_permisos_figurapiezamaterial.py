from django.apps import apps as global_apps
from django.contrib.auth.management import create_permissions
from django.db import migrations


def asignar_permisos(apps, schema_editor):
    Group      = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    # En un `migrate` que crea el modelo y le asigna permisos en la misma corrida,
    # los permisos automáticos de Django (add_/change_/delete_/view_) todavía no
    # existen en ese punto (se crean via post_migrate, al final de TODA la corrida).
    # Los forzamos a existir ya mismo antes de intentar asignarlos.
    app_config = global_apps.get_app_config("produccion")
    create_permissions(app_config, verbosity=0)

    maker = Group.objects.filter(name="Maker").first()
    if not maker:
        return

    codenames = [
        "add_figurapiezamaterial", "change_figurapiezamaterial",
        "delete_figurapiezamaterial", "view_figurapiezamaterial",
    ]
    permisos = Permission.objects.filter(
        content_type__app_label="produccion",
        codename__in=codenames,
    )
    maker.permissions.add(*permisos)


def revocar_permisos(apps, schema_editor):
    Group      = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    maker = Group.objects.filter(name="Maker").first()
    if not maker:
        return

    codenames = [
        "add_figurapiezamaterial", "change_figurapiezamaterial",
        "delete_figurapiezamaterial", "view_figurapiezamaterial",
    ]
    permisos = Permission.objects.filter(
        content_type__app_label="produccion",
        codename__in=codenames,
    )
    maker.permissions.remove(*permisos)


class Migration(migrations.Migration):

    dependencies = [
        ("produccion", "0059_maker_permisos_figurapiezamaterial"),
    ]

    operations = [
        migrations.RunPython(asignar_permisos, revocar_permisos),
    ]
