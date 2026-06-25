import os
from django.conf import settings
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/drive"]


def _get_drive_service():
    creds = None
    token_path = settings.GOOGLE_DRIVE_TOKEN_FILE
    credentials_path = settings.GOOGLE_DRIVE_CREDENTIALS_FILE

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=8080)
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


def get_or_create_folder(service, name, parent_id):
    """Devuelve el ID de una carpeta en Drive, creándola si no existe."""
    q = (
        f"name='{name}' and '{parent_id}' in parents "
        f"and mimeType='application/vnd.google-apps.folder' and trashed=false"
    )
    results = service.files().list(q=q, fields="files(id)").execute()
    folders = results.get("files", [])
    if folders:
        return folders[0]["id"]
    folder = service.files().create(
        body={"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]},
        fields="id",
    ).execute()
    return folder["id"]


def get_or_create_folder_path(service, path, root_folder_id):
    """
    Recorre cada segmento de `path` y crea las carpetas necesarias en Drive.
    Ej: path='piezas/imagenes' crea piezas/ y dentro imagenes/.
    Devuelve el ID de la carpeta final.
    """
    folder_id = root_folder_id
    for segment in path.strip("/").split("/"):
        if segment:
            folder_id = get_or_create_folder(service, segment, folder_id)
    return folder_id


@deconstructible
class GoogleDriveStorage(Storage):

    def __init__(self):
        self.root_folder_id = settings.GOOGLE_DRIVE_FOLDER_ID
        self._service = None
        self._folder_cache = {}

    @property
    def service(self):
        if self._service is None:
            self._service = _get_drive_service()
        return self._service

    def _get_folder_id(self, path):
        """Obtiene (con caché) el ID de la carpeta para un path dado."""
        if path not in self._folder_cache:
            self._folder_cache[path] = get_or_create_folder_path(
                self.service, path, self.root_folder_id
            )
        return self._folder_cache[path]

    def _save(self, name, content):
        content.seek(0)
        mimetype = getattr(content, "content_type", "application/octet-stream")
        # Separar directorio y nombre de archivo
        directory = os.path.dirname(name)
        filename = os.path.basename(name)
        folder_id = self._get_folder_id(directory) if directory else self.root_folder_id

        file_metadata = {"name": filename, "parents": [folder_id]}
        media = MediaIoBaseUpload(content, mimetype=mimetype, resumable=True)
        file = (
            self.service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )
        self.service.permissions().create(
            fileId=file["id"],
            body={"type": "anyone", "role": "reader"},
        ).execute()
        # Guardar el ID de Drive como "name" para usar en url()
        return file["id"]

    def url(self, name):
        return f"https://lh3.googleusercontent.com/d/{name}"

    def exists(self, name):
        # Antes de guardar: name es un path de archivo (tiene / o .)
        # Después de guardar: name es un ID de Drive (sin / ni .)
        if "/" in name or "." in name:
            return False
        try:
            self.service.files().get(fileId=name, fields="id").execute()
            return True
        except HttpError:
            return False

    def delete(self, name):
        try:
            self.service.files().delete(fileId=name).execute()
        except HttpError:
            pass

    def size(self, name):
        try:
            f = self.service.files().get(fileId=name, fields="size").execute()
            return int(f.get("size", 0))
        except HttpError:
            return 0

    def listdir(self, path):
        folder_id = self._get_folder_id(path) if path else self.root_folder_id
        results = self.service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="files(id, name)",
        ).execute()
        return [], [f["name"] for f in results.get("files", [])]
