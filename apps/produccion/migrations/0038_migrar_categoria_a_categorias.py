from django.db import migrations


def copiar_categoria(apps, schema_editor):
    Figura = apps.get_model("produccion", "Figura")
    for figura in Figura.objects.exclude(categoria__isnull=True):
        figura.categorias.add(figura.categoria_id)


def revertir_categoria(apps, schema_editor):
    Figura = apps.get_model("produccion", "Figura")
    for figura in Figura.objects.exclude(categoria__isnull=True):
        figura.categorias.remove(figura.categoria_id)


class Migration(migrations.Migration):

    dependencies = [
        ("produccion", "0037_figura_categorias_alter_figura_categoria"),
    ]

    operations = [
        migrations.RunPython(copiar_categoria, revertir_categoria),
    ]
