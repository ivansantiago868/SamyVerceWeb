from django.db import migrations


def crear_grupos(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    User = apps.get_model("auth", "User")

    grupo_admin, _ = Group.objects.get_or_create(name="Admin")
    Group.objects.get_or_create(name="Vendor")
    Group.objects.get_or_create(name="Maker")

    try:
        kivandy = User.objects.get(username="kivandy")
        kivandy.groups.add(grupo_admin)
    except User.DoesNotExist:
        pass


def eliminar_grupos(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=["Admin", "Vendor", "Maker"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("produccion", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(crear_grupos, eliminar_grupos),
    ]
