from django.apps import AppConfig


class ProduccionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name               = "apps.produccion"
    verbose_name       = "Producción 3D"

    def ready(self):
        import apps.produccion.signals  # noqa: F401
        self._activar_wal_sqlite()

    def _activar_wal_sqlite(self):
        """
        Activa el modo WAL en SQLite (persiste en el archivo, se hace una
        sola vez por conexión nueva pero el modo ya queda fijado). Permite
        lecturas concurrentes mientras un hilo en background escribe, lo que
        reduce mucho los "database is locked" con el procesamiento IA async.
        """
        from django.db import connection
        from django.db.backends.signals import connection_created

        if connection.vendor != "sqlite":
            return

        def _set_wal(sender, connection, **kwargs):
            if connection.vendor == "sqlite":
                connection.cursor().execute("PRAGMA journal_mode=WAL;")

        # weak=False: _set_wal es una función anidada sin otra referencia
        # fuerte — con el weakref por defecto de Signal.connect(), Python la
        # recolecta como basura apenas termina ready() y la señal deja de
        # disparar (silenciosamente, sin error).
        connection_created.connect(_set_wal, weak=False)
