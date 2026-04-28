from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """Agrega FiguraImagen para el carrusel de imágenes de cada figura."""

    dependencies = [
        ('produccion', '0022_figura_figurapieza'),
    ]

    operations = [
        migrations.CreateModel(
            name='FiguraImagen',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('imagen', models.ImageField(upload_to='figuras/imagenes/', verbose_name='Imagen')),
                ('orden', models.PositiveSmallIntegerField(default=0, verbose_name='Orden')),
                ('figura', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                             related_name='imagenes', to='produccion.figura', verbose_name='Figura')),
            ],
            options={'ordering': ['orden', 'id'], 'verbose_name': 'Imagen de figura',
                     'verbose_name_plural': 'Imágenes de figura'},
        ),
    ]
