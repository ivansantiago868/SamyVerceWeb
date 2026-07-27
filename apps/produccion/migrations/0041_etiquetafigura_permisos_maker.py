from django.db import migrations


def asignar_permisos_etiqueta(apps, schema_editor):
    # Los Permission de un modelo recién creado se generan en la señal
    # post_migrate, que Django dispara al FINAL de todo el comando `migrate`
    # (no tras cada migración individual). Si esta migración se aplica en la
    # misma invocación que crea el modelo (entorno fresco: BD nueva, CI),
    # esas filas todavía no existen. Se fuerza su creación aquí para que la
    # asignación sea confiable sin importar el orden de aplicación.
    from django.apps import apps as global_apps
    from django.contrib.auth.management import create_permissions
    create_permissions(global_apps.get_app_config("produccion"), verbosity=0)

    Group      = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    maker = Group.objects.filter(name="Maker").first()
    if not maker:
        return

    codenames = [
        "add_etiquetafigura", "change_etiquetafigura",
        "delete_etiquetafigura", "view_etiquetafigura",
    ]
    permisos = Permission.objects.filter(
        content_type__app_label="produccion",
        codename__in=codenames,
    )
    maker.permissions.add(*permisos)


def revocar_permisos_etiqueta(apps, schema_editor):
    Group      = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    maker = Group.objects.filter(name="Maker").first()
    if not maker:
        return

    codenames = [
        "add_etiquetafigura", "change_etiquetafigura",
        "delete_etiquetafigura", "view_etiquetafigura",
    ]
    permisos = Permission.objects.filter(
        content_type__app_label="produccion",
        codename__in=codenames,
    )
    maker.permissions.remove(*permisos)


class Migration(migrations.Migration):

    dependencies = [
        ("produccion", "0040_etiquetafigura_figura_etiquetas"),
    ]

    operations = [
        migrations.RunPython(asignar_permisos_etiqueta, revocar_permisos_etiqueta),
    ]
