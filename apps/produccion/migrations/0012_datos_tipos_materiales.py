from django.db import migrations


TIPOS_Y_MATERIALES = {
    "FDM": [
        "PLA (Ácido Poliláctico)",
        "PETG (Tereftalato de Polietileno Glicol)",
        "TPU / TPE (Flexibles)",
        "ABS (Acrilonitrilo Butadieno Estireno)",
        "ASA (Acrilonitrilo Estireno Acrilato)",
        "Nylon (Poliamida)",
        "PC (Policarbonato)",
        "Filamentos Estéticos / Especiales (Seda, Fibra de carbono, Madera, Fosforescentes, etc.)",
    ],
    "Resina": [
        "Resina Estándar",
        "Resina Lavable con Agua (Water Washable)",
        "Resina Tipo ABS / Alta Resistencia (ABS-like / Tough)",
        "Resina Flexible / Elástica",
        "Resina Transparente (Clear)",
        "Resina Calcinable (Castable)",
        "Resina de Alta Temperatura",
        "Resina Basada en Plantas (Eco / Plant-based)",
        "Resina Rápida (Fast / Rapid)",
        "Resinas Dentales / Biocompatibles",
    ],
}


def cargar_datos(apps, schema_editor):
    TipoMaterial = apps.get_model("produccion", "TipoMaterial")
    Material     = apps.get_model("produccion", "Material")

    for tipo_nombre, materiales in TIPOS_Y_MATERIALES.items():
        tipo, _ = TipoMaterial.objects.get_or_create(nombre=tipo_nombre)
        for mat_nombre in materiales:
            Material.objects.get_or_create(nombre=mat_nombre, tipo=tipo)


def borrar_datos(apps, schema_editor):
    apps.get_model("produccion", "Material").objects.all().delete()
    apps.get_model("produccion", "TipoMaterial").objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("produccion", "0011_tablas_tipo_material"),
    ]

    operations = [
        migrations.RunPython(cargar_datos, borrar_datos),
    ]
