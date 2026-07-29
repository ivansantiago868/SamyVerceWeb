from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from apps.produccion.controllers.auth_controller import (
    RegistroView,
    LogoutView,
    PerfilView,
    TokenFromSessionView,
)
from config.google_drive_views import google_drive_connect, google_drive_callback
from config.backup_db_views import (
    iniciar_backup_db, estado_backup_db,
    listar_backups, iniciar_restaurar_backup, estado_restaurar_backup,
)
from apps.produccion.views.pdf_catalogo_figuras import exportar_catalogo_pdf_publico

urlpatterns = [
    # Admin
    path("admin/google-drive/connect/",  google_drive_connect,  name="google-drive-connect"),
    path("admin/google-drive/callback/", google_drive_callback, name="google-drive-callback"),
    path("admin/backup-db/iniciar/",           iniciar_backup_db,       name="backup-db-iniciar"),
    path("admin/backup-db/estado/",            estado_backup_db,        name="backup-db-estado"),
    path("admin/backup-db/listar/",            listar_backups,          name="backup-db-listar"),
    path("admin/backup-db/restaurar/",         iniciar_restaurar_backup, name="backup-db-restaurar"),
    path("admin/backup-db/restaurar-estado/",  estado_restaurar_backup,  name="backup-db-restaurar-estado"),
    path("admin/", admin.site.urls),

    # ── JWT Auth ──────────────────────────────────────────────────
    # POST /api/auth/token/          → login → obtener access + refresh token
    # POST /api/auth/token/refresh/  → renovar access token con refresh token
    # POST /api/auth/token/verify/   → verificar si un token es válido
    # POST /api/auth/registro/       → registrar nuevo usuario
    # POST /api/auth/logout/         → revocar refresh token (blacklist)
    # GET  /api/auth/perfil/         → ver perfil del usuario autenticado
    # PATCH /api/auth/perfil/        → actualizar perfil
    path("api/auth/token/",         TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(),    name="token_refresh"),
    path("api/auth/token/verify/",  TokenVerifyView.as_view(),     name="token_verify"),
    path("api/auth/registro/",      RegistroView.as_view(),        name="registro"),
    path("api/auth/logout/",        LogoutView.as_view(),          name="logout"),
    path("api/auth/perfil/",        PerfilView.as_view(),           name="perfil"),
    path("api/auth/token-session/", TokenFromSessionView.as_view(), name="token-from-session"),

    # ── API v1 ────────────────────────────────────────────────────
    path("api/v1/", include("apps.produccion.urls")),

    # ── Interfaces gráficas ───────────────────────────────────────
    path("",                TemplateView.as_view(template_name="catalogo/index.html"), name="home"),
    path("catalogo.pdf",     exportar_catalogo_pdf_publico,                            name="catalogo-pdf-publico"),
    path("cotizador/",   TemplateView.as_view(template_name="cotizador/index.html"),   name="cotizador-ui"),
    path("figuras/",     TemplateView.as_view(template_name="figuras/index.html"),     name="figuras-ui"),
    path("cotizador3d/", TemplateView.as_view(template_name="cotizador3d/index.html"), name="cotizador3d-ui"),

    # ── Documentación API (Swagger / ReDoc) ───────────────────────
    path("api/schema/",     SpectacularAPIView.as_view(permission_classes=[]),                             name="schema"),
    path("api/docs/",       SpectacularSwaggerView.as_view(url_name="schema", permission_classes=[]),      name="swagger-ui"),
    path("api/docs/redoc/", SpectacularRedocView.as_view(url_name="schema",   permission_classes=[]),      name="redoc"),
]

# Agrega este bloque de código al final del archivo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    try:
        import debug_toolbar
        urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass