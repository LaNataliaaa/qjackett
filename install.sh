#!/usr/bin/env bash
set -e

DEST_DIR="${HOME}/.local/bin"
mkdir -p "$DEST_DIR"

install -m 755 qjackett "$DEST_DIR/qjackett"

echo "✅ qjackett se ha instalado con éxito en $DEST_DIR/qjackett"
echo "Asegúrate de que $DEST_DIR esté en tu \$PATH."
