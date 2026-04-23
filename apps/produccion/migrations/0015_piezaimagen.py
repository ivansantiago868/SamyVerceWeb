from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0014_pieza_imagen'),
    ]

    operations = [
        migrations.CreateModel(
            name='PiezaImagen',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('imagen', models.ImageField(upload_to='piezas/imagenes/', verbose_name='Imagen')),
                ('orden', models.PositiveSmallIntegerField(default=0, verbose_name='Orden')),
                ('pieza', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='imagenes',
                    to='produccion.inventariopieza',
                    verbose_name='Pieza',
                )),
            ],
            options={
                'verbose_name': 'Imagen de pieza',
                'verbose_name_plural': 'Imágenes de pieza',
                'ordering': ['orden', 'id'],
            },
        ),
    ]
