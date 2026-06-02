import os
import mimetypes
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from config.google_drive_storage import _get_drive_service, get_or_create_folder_path
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError


def subir_archivo(service, folder_id, filepath):
    """Sube un archivo a `folder_id`. Reutiliza si ya existe con ese nombre."""
    name = os.path.basename(filepath)
    existing = service.files().list(
        q=f"name='{name}' and '{folder_id}' in parents and trashed=false",
        fields="files(id)",
    ).execute().get("files", [])
    if existing:
        return existing[0]["id"], False

    mimetype, _ = mimetypes.guess_type(filepath)
    mimetype = mimetype or "application/octet-stream"
    file = (
        service.files()
        .create(
            body={"name": name, "parents": [folder_id]},
            media_body=MediaFileUpload(filepath, mimetype=mimetype, resumable=True),
            fields="id",
        )
        .execute()
    )
    service.permissions().create(
        fileId=file["id"], body={"type": "anyone", "role": "reader"}
    ).execute()
    return file["id"], True


class Command(BaseCommand):
    help = "Sube todas las imágenes de /media a Google Drive (con estructura de carpetas) y actualiza la BD"

    def handle(self, *args, **options):
        media_root = Path(settings.MEDIA_ROOT)
        root_folder_id = settings.GOOGLE_DRIVE_FOLDER_ID
        service = _get_drive_service()

        extensiones = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
        archivos = [
            p for p in media_root.rglob("*")
            if p.is_file() and p.suffix.lower() in extensiones
        ]

        self.stdout.write(f"Encontrados {len(archivos)} archivos de imagen.\n")

        # Caché de carpetas para no recrear en cada iteración
        folder_cache = {}

        def get_folder(rel_dir):
            if rel_dir not in folder_cache:
                folder_cache[rel_dir] = get_or_create_folder_path(
                    service, rel_dir, root_folder_id
                )
            return folder_cache[rel_dir]

        mapa = {}
        for i, filepath in enumerate(archivos, 1):
            rel = str(filepath.relative_to(media_root))
            rel_dir = str(filepath.relative_to(media_root).parent)
            self.stdout.write(f"[{i}/{len(archivos)}] {rel}...")
            try:
                folder_id = get_folder(rel_dir) if rel_dir != "." else root_folder_id
                drive_id, nuevo = subir_archivo(service, folder_id, str(filepath))
                mapa[rel] = drive_id
                estado = "subido" if nuevo else "ya existía"
                self.stdout.write(self.style.SUCCESS(f"  ✓ {estado}: {drive_id}"))
            except HttpError as e:
                self.stdout.write(self.style.ERROR(f"  ✗ Error: {e}"))

        self.stdout.write("\nActualizando base de datos...")
        self._actualizar_bd(mapa)
        self.stdout.write(self.style.SUCCESS(f"\nListo. {len(mapa)} archivos en Drive con estructura de carpetas."))

    def _actualizar_bd(self, mapa):
        from apps.produccion.models.empresa import Empresa
        from apps.produccion.models.inventario_pieza import InventarioPieza, PiezaImagen
        from apps.produccion.models.figura import FiguraImagen

        updated = 0

        def _update_field(model, field):
            nonlocal updated
            for obj in model.objects.exclude(**{field: ""}).exclude(**{field: None}):
                val = str(getattr(obj, field))
                if val in mapa:
                    model.objects.filter(pk=obj.pk).update(**{field: mapa[val]})
                    updated += 1

        with transaction.atomic():
            _update_field(Empresa, "logo")
            for field in ["imagen", "imagen_procesada"]:
                _update_field(InventarioPieza, field)
                _update_field(PiezaImagen, field)
                _update_field(FiguraImagen, field)

        self.stdout.write(f"  {updated} registros actualizados en la BD.")
