import io
import json
import os
import threading
from datetime import datetime

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import call_command
from django.http import HttpResponseNotAllowed, JsonResponse

from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

from config.google_drive_storage import GoogleDriveStorage, get_or_create_folder

# Se excluyen tablas que Django regenera solo (chocan entre entornos) y las
# cuentas de usuario/perfiles: restaurar una foto vieja de auth.User /
# PerfilUsuario puede pisar altas o cambios de cuenta más recientes y romper
# la restricción única usuario_id de PerfilUsuario. Lo que interesa restaurar
# es la data de negocio (figuras, pedidos, piezas, etc.), no las cuentas.
_EXCLUIR = [
    "contenttypes", "auth.permission", "sessions.session", "admin.logentry",
    "auth.user", "produccion.perfilusuario",
    "token_blacklist.outstandingtoken", "token_blacklist.blacklistedtoken",
]

_ESTADO_INICIAL = {
    "en_progreso": False,
    "mensaje": "",
    "error": None,
    "drive_url": None,
    "terminado_en": None,
}


def _base_dir():
    return os.path.dirname(settings.DATABASES["default"]["NAME"])


def _estado_path(nombre_archivo):
    """Archivo de estado en el volumen persistente, visible para todos los
    workers (procesos distintos), no solo el que lanzó el hilo."""
    return os.path.join(_base_dir(), nombre_archivo)


def _leer_estado(nombre_archivo):
    try:
        with open(_estado_path(nombre_archivo)) as f:
            return json.load(f)
    except Exception:
        return dict(_ESTADO_INICIAL)


def _escribir_estado(nombre_archivo, data):
    try:
        with open(_estado_path(nombre_archivo), "w") as f:
            json.dump(data, f)
    except Exception:
        pass


def _carpeta_backups(storage):
    return get_or_create_folder(storage.service, "Backups", storage.root_folder_id)


def _hacer_backup():
    """Genera un dump JSON de los datos (dumpdata) y lo sube a Drive."""
    _escribir_estado("backup_status.json", {
        **_ESTADO_INICIAL, "en_progreso": True,
        "mensaje": "Generando backup de datos (JSON)…",
    })
    try:
        buf = io.StringIO()
        call_command(
            "dumpdata",
            exclude=_EXCLUIR,
            natural_foreign=True,
            natural_primary=True,
            indent=2,
            stdout=buf,
        )
        contenido = buf.getvalue().encode("utf-8")

        _escribir_estado("backup_status.json", {
            **_ESTADO_INICIAL, "en_progreso": True,
            "mensaje": "Subiendo backup a Google Drive…",
        })

        storage = GoogleDriveStorage()
        folder_id = _carpeta_backups(storage)
        nombre = f"backup_db_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        media = MediaIoBaseUpload(io.BytesIO(contenido), mimetype="application/json", resumable=True)
        archivo = (
            storage.service.files()
            .create(body={"name": nombre, "parents": [folder_id]}, media_body=media, fields="id, webViewLink")
            .execute()
        )

        _escribir_estado("backup_status.json", {
            "en_progreso": False,
            "mensaje": f"Backup completado: {nombre}",
            "error": None,
            "drive_url": archivo.get("webViewLink"),
            "terminado_en": datetime.now().isoformat(),
        })
    except Exception as exc:
        _escribir_estado("backup_status.json", {
            "en_progreso": False,
            "mensaje": "",
            "error": f"Error al generar/subir el backup: {exc}",
            "drive_url": None,
            "terminado_en": datetime.now().isoformat(),
        })


@staff_member_required
def iniciar_backup_db(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    estado_actual = _leer_estado("backup_status.json")
    if estado_actual.get("en_progreso"):
        return JsonResponse({"iniciado": False, **estado_actual})

    threading.Thread(target=_hacer_backup, daemon=True).start()
    return JsonResponse({"iniciado": True, "en_progreso": True})


@staff_member_required
def estado_backup_db(request):
    return JsonResponse(_leer_estado("backup_status.json"))


@staff_member_required
def listar_backups(request):
    """Lista los backups JSON disponibles en Drive, más reciente primero."""
    try:
        storage = GoogleDriveStorage()
        folder_id = _carpeta_backups(storage)
        resultados = storage.service.files().list(
            q=f"'{folder_id}' in parents and trashed=false and name contains '.json'",
            fields="files(id, name, createdTime, webViewLink)",
            orderBy="createdTime desc",
            pageSize=30,
        ).execute()
        archivos = resultados.get("files", [])
    except Exception as exc:
        return JsonResponse({"error": str(exc), "archivos": []}, status=500)
    return JsonResponse({"archivos": archivos})


def _descargar_de_drive(file_id):
    storage = GoogleDriveStorage()
    descarga_request = storage.service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, descarga_request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buf.seek(0)
    return buf.read()


# Modelos de cuentas/perfiles que nunca deben restaurarse desde un backup,
# ni siquiera uno viejo generado antes de excluirlos de _hacer_backup(): el
# usuario_id de PerfilUsuario es único y una foto vieja puede chocar contra
# altas/cambios de cuenta más recientes.
_MODELOS_A_FILTRAR = {
    "auth.user", "produccion.perfilusuario",
    "token_blacklist.outstandingtoken", "token_blacklist.blacklistedtoken",
}


def _filtrar_datos_usuario(contenido_bytes):
    """Quita del dump JSON los objetos de auth.user / PerfilUsuario, sin
    tocar el resto (así se puede restaurar cualquier backup, viejo o nuevo)."""
    datos = json.loads(contenido_bytes.decode("utf-8"))
    filtrado = [obj for obj in datos if obj.get("model") not in _MODELOS_A_FILTRAR]
    return json.dumps(filtrado, indent=2).encode("utf-8")


def _restaurar(file_id=None, contenido_subido=None):
    """Restaura desde un backup en Drive (file_id) o desde un archivo JSON
    subido directamente por el usuario (contenido_subido, bytes)."""
    origen_mensaje = "Descargando backup desde Drive…" if file_id else "Leyendo archivo subido…"
    _escribir_estado("restore_status.json", {
        **_ESTADO_INICIAL, "en_progreso": True,
        "mensaje": origen_mensaje,
    })
    tmp_path = None
    try:
        contenido = _descargar_de_drive(file_id) if file_id else contenido_subido
        contenido = _filtrar_datos_usuario(contenido)

        tmp_path = os.path.join(_base_dir(), f"restore_tmp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(tmp_path, "wb") as f:
            f.write(contenido)

        # Respaldo de seguridad automático de los datos actuales antes de sobrescribir.
        _escribir_estado("restore_status.json", {
            **_ESTADO_INICIAL, "en_progreso": True,
            "mensaje": "Creando respaldo de seguridad de los datos actuales antes de restaurar…",
        })
        _hacer_backup()

        _escribir_estado("restore_status.json", {
            **_ESTADO_INICIAL, "en_progreso": True,
            "mensaje": "Restaurando datos…",
        })
        call_command("loaddata", tmp_path)

        _escribir_estado("restore_status.json", {
            "en_progreso": False,
            "mensaje": "Restauración completada correctamente.",
            "error": None,
            "drive_url": None,
            "terminado_en": datetime.now().isoformat(),
        })
    except Exception as exc:
        _escribir_estado("restore_status.json", {
            "en_progreso": False,
            "mensaje": "",
            "error": f"Error al restaurar: {exc}",
            "drive_url": None,
            "terminado_en": datetime.now().isoformat(),
        })
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


@staff_member_required
def iniciar_restaurar_backup(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    file_id = request.POST.get("file_id")
    archivo_subido = request.FILES.get("archivo")

    if not file_id and not archivo_subido:
        return JsonResponse({"iniciado": False, "error": "Elegí un backup de Drive o subí un archivo JSON."}, status=400)

    if archivo_subido and not archivo_subido.name.lower().endswith(".json"):
        return JsonResponse({"iniciado": False, "error": "El archivo debe ser un .json."}, status=400)

    estado_actual = _leer_estado("restore_status.json")
    if estado_actual.get("en_progreso"):
        return JsonResponse({"iniciado": False, **estado_actual})

    contenido_subido = archivo_subido.read() if archivo_subido else None
    threading.Thread(
        target=_restaurar,
        kwargs={"file_id": file_id, "contenido_subido": contenido_subido},
        daemon=True,
    ).start()
    return JsonResponse({"iniciado": True, "en_progreso": True})


@staff_member_required
def estado_restaurar_backup(request):
    return JsonResponse(_leer_estado("restore_status.json"))
