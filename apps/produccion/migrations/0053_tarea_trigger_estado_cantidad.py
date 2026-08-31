# El trigger de 0029_tarea_trigger_estado.py solo se disparaba cuando
# cambiaba `realizados`. Si en cambio baja `cantidad` (ej. al reducir la
# cantidad de un Pedido, que sincroniza hacia abajo la Tarea) hasta igualar
# un `realizados` ya existente, el estado se quedaba desactualizado en vez
# de pasar a "Listo". Se amplía la condición para cubrir ambos casos.
from django.db import migrations


SQL_CREATE_PG = """
CREATE OR REPLACE FUNCTION tarea_sync_estado()
RETURNS TRIGGER AS $$
BEGIN
    IF (NEW.realizados IS DISTINCT FROM OLD.realizados
        OR NEW.cantidad IS DISTINCT FROM OLD.cantidad) THEN
        IF NEW.estado NOT IN ('Entregado', 'Cancelado') THEN
            IF NEW.cantidad > 0 AND NEW.realizados >= NEW.cantidad THEN
                NEW.estado := 'Listo';
            ELSIF NEW.realizados > 0 THEN
                NEW.estado := 'En cola';
            END IF;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

SQL_DROP_PG = """
DROP TRIGGER IF EXISTS tarea_auto_estado ON produccion_tarea;
DROP FUNCTION IF EXISTS tarea_sync_estado();
"""

SQL_RECREATE_TRIGGER_PG = """
CREATE TRIGGER tarea_auto_estado
BEFORE UPDATE ON produccion_tarea
FOR EACH ROW EXECUTE FUNCTION tarea_sync_estado();
"""

SQL_CREATE_SQLITE = """
CREATE TRIGGER IF NOT EXISTS tarea_auto_estado
BEFORE UPDATE ON produccion_tarea
FOR EACH ROW
WHEN (NEW.realizados != OLD.realizados OR NEW.cantidad != OLD.cantidad)
  AND NEW.estado NOT IN ('Entregado', 'Cancelado')
BEGIN
    UPDATE produccion_tarea
    SET estado = CASE
        WHEN NEW.cantidad > 0 AND NEW.realizados >= NEW.cantidad THEN 'Listo'
        WHEN NEW.realizados > 0 THEN 'En cola'
        ELSE NEW.estado
    END
    WHERE id = NEW.id;
END;
"""

SQL_DROP_SQLITE = "DROP TRIGGER IF EXISTS tarea_auto_estado;"

# Versión anterior (solo `realizados`), usada para revertir la migración.
SQL_CREATE_PG_ANTERIOR = """
CREATE OR REPLACE FUNCTION tarea_sync_estado()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.realizados IS DISTINCT FROM OLD.realizados THEN
        IF NEW.estado NOT IN ('Entregado', 'Cancelado') THEN
            IF NEW.cantidad > 0 AND NEW.realizados >= NEW.cantidad THEN
                NEW.estado := 'Listo';
            ELSIF NEW.realizados > 0 THEN
                NEW.estado := 'En cola';
            END IF;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

SQL_CREATE_SQLITE_ANTERIOR = """
CREATE TRIGGER IF NOT EXISTS tarea_auto_estado
BEFORE UPDATE ON produccion_tarea
FOR EACH ROW
WHEN NEW.realizados != OLD.realizados
  AND NEW.estado NOT IN ('Entregado', 'Cancelado')
BEGIN
    UPDATE produccion_tarea
    SET estado = CASE
        WHEN NEW.cantidad > 0 AND NEW.realizados >= NEW.cantidad THEN 'Listo'
        WHEN NEW.realizados > 0 THEN 'En cola'
        ELSE NEW.estado
    END
    WHERE id = NEW.id;
END;
"""


def forwards(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    if vendor == "postgresql":
        schema_editor.execute(SQL_DROP_PG)
        schema_editor.execute(SQL_CREATE_PG)
        schema_editor.execute(SQL_RECREATE_TRIGGER_PG)
    elif vendor == "sqlite":
        schema_editor.execute(SQL_DROP_SQLITE)
        schema_editor.execute(SQL_CREATE_SQLITE)


def backwards(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    if vendor == "postgresql":
        schema_editor.execute(SQL_DROP_PG)
        schema_editor.execute(SQL_CREATE_PG_ANTERIOR)
        schema_editor.execute(SQL_RECREATE_TRIGGER_PG)
    elif vendor == "sqlite":
        schema_editor.execute(SQL_DROP_SQLITE)
        schema_editor.execute(SQL_CREATE_SQLITE_ANTERIOR)


class Migration(migrations.Migration):

    dependencies = [
        ("produccion", "0052_pedido_datos_comprador"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
