from django.db import migrations

SQL_CREATE = """
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

SQL_DROP = """
DROP TRIGGER IF EXISTS tarea_auto_estado ON produccion_tarea;
DROP FUNCTION IF EXISTS tarea_sync_estado();
"""


class Migration(migrations.Migration):

    dependencies = [
        ("produccion", "0028_figurapieza_insumo"),
    ]

    operations = [
        migrations.RunSQL(sql=SQL_CREATE, reverse_sql=SQL_DROP),
    ]
