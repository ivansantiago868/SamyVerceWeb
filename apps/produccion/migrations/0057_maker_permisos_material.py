from django.db import migrations


def asignar_permisos_material(apps, schema_editor):
    Group      = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    maker = Group.objects.filter(name="Maker").first()
    if not maker:
        return

    codenames = [
        "add_material", "change_material", "view_material",
        "add_tipomaterial", "change_tipomaterial", "view_tipomaterial",
    ]
    permisos = Permission.objects.filter(
        content_type__app_label="produccion",
        codename__in=codenames,
    )
    maker.permissions.add(*permisos)


def revocar_permisos_material(apps, schema_editor):
    Group      = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    maker = Group.objects.filter(name="Maker").first()
    if not maker:
        return

    codenames = [
        "add_material", "change_material", "view_material",
        "add_tipomaterial", "change_tipomaterial", "view_tipomaterial",
    ]
    permisos = Permission.objects.filter(
        content_type__app_label="produccion",
        codename__in=codenames,
    )
    maker.permissions.remove(*permisos)


class Migration(migrations.Migration):

    dependencies = [
        ("produccion", "0056_insumo_color"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(asignar_permisos_material, revocar_permisos_material),
    ]
