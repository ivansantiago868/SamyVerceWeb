#!/bin/sh
set -e

# El backend de Google Drive (config/google_drive_storage.py) lee credenciales
# desde archivos en disco. Como el filesystem de Fly es efímero, se reconstruyen
# en cada arranque a partir de los secrets GOOGLE_DRIVE_CREDENTIALS_JSON / GOOGLE_DRIVE_TOKEN_JSON.
if [ -n "$GOOGLE_DRIVE_CREDENTIALS_JSON" ]; then
  printf '%s' "$GOOGLE_DRIVE_CREDENTIALS_JSON" > "${GOOGLE_DRIVE_CREDENTIALS_FILE:-/app/google_credentials.json}"
fi
if [ -n "$GOOGLE_DRIVE_TOKEN_JSON" ]; then
  printf '%s' "$GOOGLE_DRIVE_TOKEN_JSON" > "${GOOGLE_DRIVE_TOKEN_FILE:-/app/google_token.json}"
fi

# Con SQLite en un volumen local, las migraciones corren aquí (en la misma
# máquina que tiene el volumen montado) en vez de en un release_command,
# que se ejecuta en una máquina efímera sin acceso al volumen.
if [ -n "$SQLITE_PATH" ]; then
  mkdir -p "$(dirname "$SQLITE_PATH")"
fi
python manage.py migrate --noinput

exec "$@"
