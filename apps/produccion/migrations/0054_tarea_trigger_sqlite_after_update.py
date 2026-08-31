# El trigger SQLite de tarea_auto_estado usaba BEFORE UPDATE con un UPDATE
# anidado. En SQLite eso NO sobrescribe el valor final: la sentencia UPDATE
# original (la que disparó el trigger) igual aplica su propio SET después
# de que el trigger BEFORE termina, así que si esa sentencia ya incluye
# `estado` en su SET —como hace cualquier guardado completo de fila,
# instance.save() sin update_fields, que es justo como guarda el admin de
# Django al editar una Tarea (formulario completo o lista editable)— el
# valor que puso el trigger queda pisado por el valor viejo del formulario.
#
# La solución en SQLite es usar AFTER UPDATE: el UPDATE anidado corre
# después de que la sentencia original ya escribió su fila, así que su
# valor es el que realmente queda. El WHEN evita recursión infinita: la
# sentencia anidada solo cambia `estado`, así que en su propio disparo
# recursivo `cantidad`/`realizados` no cambian y el WHEN da falso.
#
# PostgreSQL no tiene este problema (BEFORE ROW ahí sí permite reasignar
# NEW.campo y que eso sea lo que se escribe), así que su trigger no cambia.
from django.db import migrations


SQL_DROP_SQLITE = "DROP TRIGGER IF EXISTS tarea_auto_estado;"

SQL_CREATE_SQLITE_AFTER = """
CREATE TRIGGER IF NOT EXISTS tarea_auto_estado
AFTER UPDATE ON produccion_tarea
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

SQL_CREATE_SQLITE_BEFORE_ANTERIOR = """
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


def forwards(apps, schema_editor):
    if schema_editor.connection.vendor == "sqlite":
        schema_editor.execute(SQL_DROP_SQLITE)
        schema_editor.execute(SQL_CREATE_SQLITE_AFTER)


def backwards(apps, schema_editor):
    if schema_editor.connection.vendor == "sqlite":
        schema_editor.execute(SQL_DROP_SQLITE)
        schema_editor.execute(SQL_CREATE_SQLITE_BEFORE_ANTERIOR)


class Migration(migrations.Migration):

    dependencies = [
        ("produccion", "0053_tarea_trigger_estado_cantidad"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
