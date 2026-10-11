#!/usr/bin/env bash
set -e

DEST_FILE="${HOME}/.local/bin/qjackett"

if [ -f "$DEST_FILE" ]; then
    rm -f "$DEST_FILE"
    echo "🗑️  qjackett ha sido desinstalado de $DEST_FILE."
else
    echo "qjackett no se encontró en $DEST_FILE."
fi
