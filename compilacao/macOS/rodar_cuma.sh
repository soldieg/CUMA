#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd -P)"
VENV_PY="$REPO_ROOT/.venv/bin/python"
COMPILED_BIN="$REPO_ROOT/dist/CUMA_macos/cuma"

echo "============================================================"
echo "CUMA - EXECUÇÃO LOCAL macOS"
echo "Repositório: $REPO_ROOT"
echo "============================================================"

[[ -f "$REPO_ROOT/cuma.py" ]] || { echo "[ERRO] Ausente: $REPO_ROOT/cuma.py" >&2; exit 1; }
[[ -f "$REPO_ROOT/requirements.txt" ]] || { echo "[ERRO] Ausente: $REPO_ROOT/requirements.txt" >&2; exit 1; }

if [[ "${1:-}" == "--check" ]]; then
  echo "[OK] Estrutura de execução macOS localizada corretamente."
  exit 0
fi

if [[ "${1:-}" == "--compilado" ]]; then
  [[ -x "$COMPILED_BIN" ]] || { echo "[ERRO] Binário compilado não encontrado: $COMPILED_BIN" >&2; exit 1; }
  exec "$COMPILED_BIN"
fi

command -v python3 >/dev/null 2>&1 || { echo "[ERRO] Python 3 não encontrado." >&2; exit 1; }

if [[ ! -x "$VENV_PY" ]]; then
  python3 -m venv "$REPO_ROOT/.venv"
fi

if ! "$VENV_PY" -c "import fitz, numpy, PIL" >/dev/null 2>&1; then
  "$VENV_PY" -m pip install --upgrade pip
  "$VENV_PY" -m pip install -r "$REPO_ROOT/requirements.txt"
fi

cd "$REPO_ROOT"
exec "$VENV_PY" "$REPO_ROOT/cuma.py"
