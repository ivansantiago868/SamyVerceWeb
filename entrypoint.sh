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

exec "$@"
