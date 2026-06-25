import environ
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY    = env("SECRET_KEY")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.forms",
    # Third party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    # Docs
    "drf_spectacular",
    # Local
    "apps.produccion",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF    = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# Fly Postgres inyecta DATABASE_URL automáticamente al hacer `fly postgres attach`.
# Si no existe, se construye a partir de las vars DB_* (usadas en docker-compose local).
_database_url = env("DATABASE_URL", default="")
if not _database_url and "postgresql" in env("DB_ENGINE", default=""):
    _database_url = (
        f"postgres://{env('DB_USER', default='')}:{env('DB_PASSWORD', default='')}"
        f"@{env('DB_HOST', default='localhost')}:{env('DB_PORT', default='5432')}"
        f"/{env('DB_NAME', default='postgres')}"
    )

DATABASES = {
    "default": env.db_url_config(_database_url)
    if _database_url
    else {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME":   BASE_DIR / "db.sqlite3",
    }
}

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {
        "context_processors": [
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
        ],
    },
}]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
FORM_RENDERER     = "django.forms.renderers.TemplatesSetting"
LANGUAGE_CODE      = "es-co"
TIME_ZONE          = "America/Bogota"
USE_I18N           = True
USE_TZ             = True
STATIC_URL         = "/static/"
STATIC_ROOT        = BASE_DIR / "staticfiles"
STATICFILES_DIRS   = [BASE_DIR / "static"]
MEDIA_URL          = "/media/"
MEDIA_ROOT         = BASE_DIR / "media"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "SamyVerce API",
    "DESCRIPTION": (
        "API de gestión para negocios de impresión 3D (roll makers).\n\n"
        "## Autenticación\n"
        "Usa JWT Bearer token. Obtén tu token en `/api/auth/token/` y "
        "envíalo en el header: `Authorization: Bearer <token>`"
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "TAGS": [
        {"name": "Auth",         "description": "Registro, login y perfil de usuario"},
        {"name": "Cotizador",    "description": "Cálculo de precios de piezas 3D"},
        {"name": "Piezas",       "description": "Inventario de piezas"},
        {"name": "Pedidos",      "description": "Gestión de pedidos de clientes"},
        {"name": "Tareas",       "description": "Tareas de producción"},
        {"name": "Ventas",       "description": "Cotizaciones y ventas"},
        {"name": "Clientes",     "description": "Directorio de clientes"},
        {"name": "Impresoras",   "description": "Inventario de impresoras"},
        {"name": "Insumos",      "description": "Stock de materiales"},
        {"name": "Gastos",       "description": "Registro de compras"},
        {"name": "Materiales",   "description": "Variables fijas y parámetros"},
    ],
}

# ── Email / SMTP ──────────────────────────────────────────────
EMAIL_BACKEND      = env("EMAIL_BACKEND",      default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST         = env("EMAIL_HOST",         default="smtp.gmail.com")
EMAIL_PORT         = env.int("EMAIL_PORT",     default=587)
EMAIL_USE_TLS      = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER    = env("EMAIL_HOST_USER",    default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER)
SERVER_EMAIL       = DEFAULT_FROM_EMAIL

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":  timedelta(minutes=env.int("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", default=60)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_TOKEN_LIFETIME_DAYS",    default=7)),
    "ROTATE_REFRESH_TOKENS":  True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}
PHOTOROOM_API_KEY = env("PHOTOROOM_API_KEY", default="")

# ── Vertex AI Imagen ───────────────────────────────────────────────────────────
VERTEX_AI_PROJECT  = env("VERTEX_AI_PROJECT",  default="")
VERTEX_AI_LOCATION = env("VERTEX_AI_LOCATION", default="us-central1")
VERTEX_AI_KEY_FILE = env("VERTEX_AI_KEY_FILE", default="")

# ── Google Imagen (google-genai SDK) ───────────────────────────────────────────
GEMINI_API_KEY = env("GEMINI_API_KEY", default="")

# ── Tripo AI (generación de modelos 3D) ───────────────────────────────────────
TRIPO_API_KEY     = env("TRIPO_API_KEY",     default="")
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", default="")

# ── Google Drive Storage ───────────────────────────────────────────────────────
GOOGLE_DRIVE_CREDENTIALS_FILE = env("GOOGLE_DRIVE_CREDENTIALS_FILE", default=str(BASE_DIR / "google_credentials.json"))
GOOGLE_DRIVE_TOKEN_FILE       = env("GOOGLE_DRIVE_TOKEN_FILE",       default=str(BASE_DIR / "google_token.json"))
GOOGLE_DRIVE_FOLDER_ID        = env("GOOGLE_DRIVE_FOLDER_ID",        default="")

if GOOGLE_DRIVE_FOLDER_ID:
    DEFAULT_FILE_STORAGE = "config.google_drive_storage.GoogleDriveStorage"
