from django.db import migrations, connection


SQL_CREATE_PG = """
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

CREATE TRIGGER tarea_auto_estado
BEFORE UPDATE ON produccion_tarea
FOR EACH ROW EXECUTE FUNCTION tarea_sync_estado();
"""

SQL_DROP_PG = """
DROP TRIGGER IF EXISTS tarea_auto_estado ON produccion_tarea;
DROP FUNCTION IF EXISTS tarea_sync_estado();
"""

# SQLite trigger equivalent
SQL_CREATE_SQLITE = """
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

SQL_DROP_SQLITE = "DROP TRIGGER IF EXISTS tarea_auto_estado;"


def forwards(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    if vendor == "postgresql":
        schema_editor.execute(SQL_CREATE_PG)
    elif vendor == "sqlite":
        schema_editor.execute(SQL_CREATE_SQLITE)


def backwards(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    if vendor == "postgresql":
        schema_editor.execute(SQL_DROP_PG)
    elif vendor == "sqlite":
        schema_editor.execute(SQL_DROP_SQLITE)


class Migration(migrations.Migration):

    dependencies = [
        ("produccion", "0028_figurapieza_insumo"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
