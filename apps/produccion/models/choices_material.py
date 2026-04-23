TIPOS_FDM = [
    ("PLA",      "PLA (Ácido Poliláctico)"),
    ("PETG",     "PETG (Tereftalato de Polietileno Glicol)"),
    ("TPU_TPE",  "TPU / TPE (Flexibles)"),
    ("ABS",      "ABS (Acrilonitrilo Butadieno Estireno)"),
    ("ASA",      "ASA (Acrilonitrilo Estireno Acrilato)"),
    ("Nylon",    "Nylon (Poliamida)"),
    ("PC",       "PC (Policarbonato)"),
    ("Especial", "Filamentos Estéticos / Especiales (Seda, Fibra de carbono, Madera, etc.)"),
]

TIPOS_RESINA = [
    ("R_Estandar", "Resina Estándar"),
    ("R_WW",       "Resina Lavable con Agua (Water Washable)"),
    ("R_ABS",      "Resina Tipo ABS / Alta Resistencia (ABS-like / Tough)"),
    ("R_Flex",     "Resina Flexible / Elástica"),
    ("R_Clear",    "Resina Transparente (Clear)"),
    ("R_Castable", "Resina Calcinable (Castable)"),
    ("R_HiTemp",   "Resina de Alta Temperatura"),
    ("R_Eco",      "Resina Basada en Plantas (Eco / Plant-based)"),
    ("R_Fast",     "Resina Rápida (Fast / Rapid)"),
    ("R_Dental",   "Resinas Dentales / Biocompatibles"),
]

TIPOS_CHOICES = TIPOS_FDM + TIPOS_RESINA

# Mapa usado por el JS para filtrar opciones según categoría
TIPOS_POR_CATEGORIA = {
    "FDM":    [k for k, _ in TIPOS_FDM],
    "Resina": [k for k, _ in TIPOS_RESINA],
}
