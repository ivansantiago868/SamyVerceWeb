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

urlpatterns = [
    # Admin
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