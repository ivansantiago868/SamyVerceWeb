from django.db import migrations


def asignar_permisos_figura(apps, schema_editor):
    Group      = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    maker = Group.objects.filter(name="Maker").first()
    if not maker:
        return

    codenames = [
        "add_figura", "change_figura", "delete_figura", "view_figura",
        "add_figuraimagen", "change_figuraimagen", "delete_figuraimagen", "view_figuraimagen",
        "add_figurapieza", "change_figurapieza", "delete_figurapieza", "view_figurapieza",
    ]
    permisos = Permission.objects.filter(
        content_type__app_label="produccion",
        codename__in=codenames,
    )
    maker.permissions.add(*permisos)


def revocar_permisos_figura(apps, schema_editor):
    Group      = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    maker = Group.objects.filter(name="Maker").first()
    if not maker:
        return

    codenames = [
        "add_figura", "change_figura", "delete_figura", "view_figura",
        "add_figuraimagen", "change_figuraimagen", "delete_figuraimagen", "view_figuraimagen",
        "add_figurapieza", "change_figurapieza", "delete_figurapieza", "view_figurapieza",
    ]
    permisos = Permission.objects.filter(
        content_type__app_label="produccion",
        codename__in=codenames,
    )
    maker.permissions.remove(*permisos)


class Migration(migrations.Migration):

    dependencies = [
        ("produccion", "0023_figuraimagen"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(asignar_permisos_figura, revocar_permisos_figura),
    ]
