from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Crea Figura y FiguraPieza.
    Si ya existen en la BD, marcar como fake:
        python manage.py migrate produccion 0022 --fake
    """

    dependencies = [
        ('produccion', '0021_impresora_consumo_promedio'),
    ]

    operations = [
        migrations.CreateModel(
            name='Figura',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255, verbose_name='Nombre de la figura')),
                ('descripcion', models.TextField(blank=True, verbose_name='Descripción')),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('actualizado_en', models.DateTimeField(auto_now=True)),
                ('empresa', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                              related_name='figuras', to='produccion.empresa', verbose_name='Empresa')),
            ],
            options={'ordering': ['nombre'], 'verbose_name': 'Figura', 'verbose_name_plural': 'Figuras'},
        ),
        migrations.CreateModel(
            name='FiguraPieza',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.PositiveIntegerField(default=1, verbose_name='Cantidad')),
                ('figura', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                             related_name='figura_piezas', to='produccion.figura', verbose_name='Figura')),
                ('pieza', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                            related_name='en_figuras', to='produccion.inventariopieza', verbose_name='Pieza')),
            ],
            options={'ordering': ['pieza__nombre'], 'verbose_name': 'Pieza de figura',
                     'verbose_name_plural': 'Piezas de figura', 'unique_together': {('figura', 'pieza')}},
        ),
    ]
