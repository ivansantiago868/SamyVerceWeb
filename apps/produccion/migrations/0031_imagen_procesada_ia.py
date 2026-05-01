from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("produccion", "0030_pedido_trigger_estado"),
    ]

    operations = [
        migrations.AddField(
            model_name="inventariopieza",
            name="imagen_procesada",
            field=models.ImageField(blank=True, null=True, upload_to="piezas/procesadas/", verbose_name="Imagen IA (estudio)"),
        ),
        migrations.AddField(
            model_name="piezaimagen",
            name="imagen_procesada",
            field=models.ImageField(blank=True, null=True, upload_to="piezas/procesadas/", verbose_name="Imagen IA (estudio)"),
        ),
        migrations.AddField(
            model_name="figuraimagen",
            name="imagen_procesada",
            field=models.ImageField(blank=True, null=True, upload_to="figuras/procesadas/", verbose_name="Imagen IA (estudio)"),
        ),
    ]
