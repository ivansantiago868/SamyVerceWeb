import os
import random
import string


def _rand6():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))


def _ext(filename):
    return os.path.splitext(filename)[1].lower() or '.jpg'


# ── InventarioPieza (imagen principal del catálogo) ────────────────────────────

def upload_inventario_imagen(instance, filename):
    empresa = instance.empresa_id or 0
    pieza   = instance.pk or 0
    return f"piezas/empresa_{empresa}/pieza_{pieza}/{_rand6()}{_ext(filename)}"


def upload_inventario_procesada(instance, filename):
    empresa = instance.empresa_id or 0
    pieza   = instance.pk or 0
    return f"piezas/empresa_{empresa}/pieza_{pieza}/ia_{_rand6()}.jpg"


# ── PiezaImagen (galería de piezas) ────────────────────────────────────────────

def upload_pieza_imagen(instance, filename):
    try:
        empresa = instance.pieza.empresa_id or 0
    except Exception:
        empresa = 0
    pieza = instance.pieza_id or 0
    return f"piezas/empresa_{empresa}/pieza_{pieza}/{_rand6()}{_ext(filename)}"


def upload_pieza_procesada(instance, filename):
    try:
        empresa = instance.pieza.empresa_id or 0
    except Exception:
        empresa = 0
    pieza = instance.pieza_id or 0
    return f"piezas/empresa_{empresa}/pieza_{pieza}/ia_{_rand6()}.jpg"


# ── FiguraImagen (galería de figuras) ──────────────────────────────────────────

def upload_figura_imagen(instance, filename):
    try:
        empresa = instance.figura.empresa_id or 0
    except Exception:
        empresa = 0
    figura = instance.figura_id or 0
    return f"figuras/empresa_{empresa}/figura_{figura}/{_rand6()}{_ext(filename)}"


def upload_figura_procesada(instance, filename):
    try:
        empresa = instance.figura.empresa_id or 0
    except Exception:
        empresa = 0
    figura = instance.figura_id or 0
    return f"figuras/empresa_{empresa}/figura_{figura}/ia_{_rand6()}.jpg"
