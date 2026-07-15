import os

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect
from django.urls import reverse
from google_auth_oauthlib.flow import Flow

from config.google_drive_storage import SCOPES


def _build_flow(request):
    flow = Flow.from_client_secrets_file(
        settings.GOOGLE_DRIVE_CREDENTIALS_FILE,
        scopes=SCOPES,
    )
    flow.redirect_uri = request.build_absolute_uri(reverse("google-drive-callback"))
    return flow


@staff_member_required
def google_drive_connect(request):
    flow = _build_flow(request)
    auth_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )
    request.session["google_drive_oauth_state"] = state
    request.session["google_drive_code_verifier"] = flow.code_verifier
    return redirect(auth_url)


@staff_member_required
def google_drive_callback(request):
    state = request.session.pop("google_drive_oauth_state", None)
    code_verifier = request.session.pop("google_drive_code_verifier", None)
    if not state or state != request.GET.get("state"):
        messages.error(request, "Estado OAuth inválido, intenta reconectar de nuevo.")
        return redirect("/admin/")

    if request.GET.get("error"):
        messages.error(request, f"Google Drive no autorizado: {request.GET['error']}")
        return redirect("/admin/")

    flow = _build_flow(request)
    flow.code_verifier = code_verifier
    try:
        flow.fetch_token(authorization_response=request.build_absolute_uri())
    except Exception as exc:
        messages.error(request, f"No se pudo completar la conexión con Google Drive: {exc}")
        return redirect("/admin/")

    token_path = settings.GOOGLE_DRIVE_TOKEN_FILE
    os.makedirs(os.path.dirname(token_path), exist_ok=True)
    with open(token_path, "w") as f:
        f.write(flow.credentials.to_json())

    messages.success(request, "Google Drive reconectado correctamente.")
    return redirect("/admin/")
