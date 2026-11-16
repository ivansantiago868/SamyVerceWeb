from django.db import migrations


def backfill(apps, schema_editor):
    FiguraPieza = apps.get_model("produccion", "FiguraPieza")
    FiguraPiezaMaterial = apps.get_model("produccion", "FiguraPiezaMaterial")

    for fp in FiguraPieza.objects.filter(insumo__isnull=False).select_related("pieza"):
        if not fp.pieza.peso_gramos:
            continue
        FiguraPiezaMaterial.objects.get_or_create(
            figura=fp.figura,
            pieza=fp.pieza,
            insumo=fp.insumo,
            defaults={"gramos": fp.pieza.peso_gramos},
        )


def revertir(apps, schema_editor):
    # No se revierte: no hay forma segura de distinguir las filas creadas por
    # este backfill de las que el usuario haya agregado manualmente después.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("produccion", "0060_fix_maker_permisos_figurapiezamaterial"),
    ]

    operations = [
        migrations.RunPython(backfill, revertir),
    ]
