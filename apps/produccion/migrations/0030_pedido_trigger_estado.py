from django.db import migrations


SQL_CREATE_PG = """
CREATE OR REPLACE FUNCTION pedido_sync_estado()
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

CREATE TRIGGER pedido_auto_estado
BEFORE UPDATE ON produccion_pedido
FOR EACH ROW EXECUTE FUNCTION pedido_sync_estado();
"""

SQL_DROP_PG = """
DROP TRIGGER IF EXISTS pedido_auto_estado ON produccion_pedido;
DROP FUNCTION IF EXISTS pedido_sync_estado();
"""

SQL_CREATE_SQLITE = """
CREATE TRIGGER IF NOT EXISTS pedido_auto_estado
BEFORE UPDATE ON produccion_pedido
FOR EACH ROW
WHEN NEW.realizados != OLD.realizados
  AND NEW.estado NOT IN ('Entregado', 'Cancelado')
BEGIN
    UPDATE produccion_pedido
    SET estado = CASE
        WHEN NEW.cantidad > 0 AND NEW.realizados >= NEW.cantidad THEN 'Listo'
        WHEN NEW.realizados > 0 THEN 'En cola'
        ELSE NEW.estado
    END
    WHERE id = NEW.id;
END;
"""

SQL_DROP_SQLITE = "DROP TRIGGER IF EXISTS pedido_auto_estado;"


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
        ("produccion", "0029_tarea_trigger_estado"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
