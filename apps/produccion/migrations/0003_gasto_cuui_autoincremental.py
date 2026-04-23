from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("produccion", "0002_grupos_iniciales"),
    ]

    operations = [
        migrations.AlterField(
            model_name="gasto",
            name="cuui",
            field=models.PositiveIntegerField(
                editable=False,
                unique=True,
                verbose_name="CUUI",
            ),
        ),
    ]
