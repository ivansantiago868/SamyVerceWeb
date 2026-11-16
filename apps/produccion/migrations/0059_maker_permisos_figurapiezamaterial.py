from django.db import migrations


def asignar_permisos(apps, schema_editor):
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
        ("produccion", "0058_figurapiezamaterial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(asignar_permisos, revocar_permisos),
    ]
