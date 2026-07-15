from django.db import migrations


def asignar_permisos_categoria(apps, schema_editor):
    Group      = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    maker = Group.objects.filter(name="Maker").first()
    if not maker:
        return

    codenames = [
        "add_categoriafigura", "change_categoriafigura",
        "delete_categoriafigura", "view_categoriafigura",
    ]
    permisos = Permission.objects.filter(
        content_type__app_label="produccion",
        codename__in=codenames,
    )
    maker.permissions.add(*permisos)


def revocar_permisos_categoria(apps, schema_editor):
    Group      = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    maker = Group.objects.filter(name="Maker").first()
    if not maker:
        return

    codenames = [
        "add_categoriafigura", "change_categoriafigura",
        "delete_categoriafigura", "view_categoriafigura",
    ]
    permisos = Permission.objects.filter(
        content_type__app_label="produccion",
        codename__in=codenames,
    )
    maker.permissions.remove(*permisos)


class Migration(migrations.Migration):

    dependencies = [
        ("produccion", "0035_categoriafigura_figura_categoria"),
    ]

    operations = [
        migrations.RunPython(asignar_permisos_categoria, revocar_permisos_categoria),
    ]
