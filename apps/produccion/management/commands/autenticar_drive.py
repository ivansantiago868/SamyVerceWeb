from django.core.management.base import BaseCommand
from django.conf import settings
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive"]


class Command(BaseCommand):
    help = "Autentica con Google Drive y guarda el token. Ejecutar una sola vez."

    def handle(self, *args, **options):
        credentials_path = settings.GOOGLE_DRIVE_CREDENTIALS_FILE
        token_path = settings.GOOGLE_DRIVE_TOKEN_FILE

        self.stdout.write("Abriendo navegador para autenticación con Google Drive...")
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
        creds = flow.run_local_server(port=8080)

        with open(token_path, "w") as f:
            f.write(creds.to_json())

        self.stdout.write(self.style.SUCCESS(f"Token guardado en: {token_path}"))
        self.stdout.write("Ya puedes subir archivos a Google Drive desde el proyecto.")
