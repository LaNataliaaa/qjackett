#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_DIR="${HOME}/.local/bin"
mkdir -p "$DEST_DIR"

install -m 755 "$SCRIPT_DIR/qjackett" "$DEST_DIR/qjackett"

echo "✅ qjackett se ha instalado con éxito en $DEST_DIR/qjackett"
echo "Asegúrate de que $DEST_DIR esté en tu \$PATH."
