#!/usr/bin/env bash
set -euo pipefail
OS="$(uname -s)"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
case "$OS" in
  Linux*) exec "$DIR/Linux/criar_linux_tar.sh" ;;
  Darwin*) exec "$DIR/macOS/criar_macos_zip.sh" ;;
  *) echo "Sistema nao suportado por este script: $OS" >&2; exit 1 ;;
esac
