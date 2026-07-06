#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd -P)"
ZIP_DIR="$REPO_ROOT/ZIP final/macOS"
OUT_DIR="$REPO_ROOT/dist/CUMA_macos"
ZIP_PATH="$ZIP_DIR/CUMA_macos.zip"
VENV_PY="$REPO_ROOT/.venv/bin/python"
APP_VERSION="1.100.37"

fail() {
  echo
  echo "[FALHA] A compilação macOS não foi concluída." >&2
  exit 1
}
trap fail ERR

echo "============================================================"
echo "CUMA - COMPILAÇÃO macOS"
echo "Repositório: $REPO_ROOT"
echo "Saída:       $ZIP_PATH"
echo "============================================================"

for required in cuma.py cuma_updater.py requirements.txt cuma_macos.spec; do
  [[ -f "$REPO_ROOT/$required" ]] || { echo "[ERRO] Ausente: $REPO_ROOT/$required" >&2; exit 1; }
done

if [[ "${1:-}" == "--check" ]]; then
  echo "[OK] Estrutura macOS localizada corretamente."
  exit 0
fi

command -v python3 >/dev/null 2>&1 || { echo "[ERRO] Python 3 não encontrado no computador de compilação." >&2; exit 1; }
command -v zip >/dev/null 2>&1 || { echo "[ERRO] O comando zip não foi encontrado." >&2; exit 1; }

if [[ ! -x "$VENV_PY" ]]; then
  echo "Criando ambiente virtual..."
  python3 -m venv "$REPO_ROOT/.venv"
fi

"$VENV_PY" -m pip install --upgrade pip setuptools wheel
"$VENV_PY" -m pip install -r "$REPO_ROOT/requirements.txt"
"$VENV_PY" -m py_compile "$REPO_ROOT/cuma.py" "$REPO_ROOT/cuma_updater.py" "$REPO_ROOT/scripts/preparar_manifesto_release.py"
"$VENV_PY" "$REPO_ROOT/scripts/auditoria_integridade.py" --version "$APP_VERSION"

rm -rf "$REPO_ROOT/build" "$REPO_ROOT/dist"
mkdir -p "$ZIP_DIR"
cd "$REPO_ROOT"

"$VENV_PY" -m PyInstaller --noconfirm "$REPO_ROOT/cuma_macos.spec"

[[ -x "$OUT_DIR/cuma" ]] || { echo "[ERRO] Binário cuma não foi criado." >&2; exit 1; }
[[ -x "$OUT_DIR/cuma_updater" ]] || { echo "[ERRO] Binário cuma_updater não foi criado." >&2; exit 1; }

for doc in manual_do_programa.txt LEIA-ME.txt README.md LICENSE NOTAS_RELEASE.md CHANGELOG.md; do
  [[ -f "$REPO_ROOT/$doc" ]] && cp -f "$REPO_ROOT/$doc" "$OUT_DIR/$doc"
done
rm -f "$OUT_DIR"/CUMA.log "$OUT_DIR"/CUMA_update.log "$OUT_DIR"/erro.txt
rm -rf "$OUT_DIR"/.cuma_user_data "$OUT_DIR"/limpos

rm -f "$ZIP_PATH"
(cd "$REPO_ROOT/dist" && zip -qry "$ZIP_PATH" CUMA_macos)
[[ -f "$ZIP_PATH" ]] || { echo "[ERRO] Pacote final não foi criado." >&2; exit 1; }

if [[ "${CUMA_SKIP_MANIFEST:-0}" == "1" ]]; then
  echo "Manifesto local ignorado pelo pipeline de release."
elif [[ -f "$REPO_ROOT/scripts/preparar_manifesto_release.py" ]]; then
  "$VENV_PY" "$REPO_ROOT/scripts/preparar_manifesto_release.py" soldieg CUMA "$APP_VERSION" "$ZIP_PATH" Stable "$REPO_ROOT/NOTAS_RELEASE.md" macos || \
    echo "[AVISO] Pacote criado, mas stable.json não foi atualizado."
fi

echo "[OK] Compilação concluída: $ZIP_PATH"
