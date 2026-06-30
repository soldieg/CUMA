#!/usr/bin/env bash
set -euo pipefail
TOOLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(cd "$TOOLS_DIR/../.." && pwd)/GitHub"
cd "$SRC_DIR"
if [ ! -x ".venv/bin/python" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install -r requirements.txt
python cuma.py
