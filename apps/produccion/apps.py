from django.apps import AppConfig


class ProduccionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name               = "apps.produccion"
    verbose_name       = "Producción 3D"

    def ready(self):
        import apps.produccion.signals  # noqa: F401
