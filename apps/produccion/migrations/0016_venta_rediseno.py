from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0015_piezaimagen'),
    ]

    operations = [
        migrations.RemoveField(model_name='venta', name='articulo'),
        migrations.RemoveField(model_name='venta', name='cantidad'),
        migrations.RemoveField(model_name='venta', name='cliente'),
        migrations.AddField(
            model_name='venta',
            name='notas',
            field=models.TextField(blank=True, verbose_name='Notas adicionales'),
        ),
        migrations.AlterField(
            model_name='venta',
            name='fecha',
            field=models.DateField(verbose_name='Fecha de cotización'),
        ),
        migrations.AlterField(
            model_name='venta',
            name='pedido',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='ventas',
                to='produccion.pedido',
                verbose_name='Pedido',
            ),
        ),
    ]
