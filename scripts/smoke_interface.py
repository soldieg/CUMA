#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smoke test da interface: abre o App e valida comandos dos controles."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMP = Path(tempfile.mkdtemp(prefix="cuma_gui_smoke_"))
os.environ["CUMA_USER_DATA_DIR"] = str(TEMP / "user_data")
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

import tkinter as tk  # noqa: E402
import cuma  # noqa: E402


def main() -> int:
    root = tk.Tk()
    root.withdraw()
    try:
        app = cuma.App(root)
        root.update_idletasks()

        controls: list[dict[str, str | bool]] = []

        def walk(widget) -> None:
            for child in widget.winfo_children():
                try:
                    keys = set(child.keys())
                    command = str(child.cget("command")) if "command" in keys else ""
                    if command:
                        exists = bool(root.tk.call("info", "commands", command))
                        controls.append(
                            {
                                "class": str(child.winfo_class()),
                                "text": str(child.cget("text")) if "text" in keys else "",
                                "command": command,
                                "valid": exists,
                            }
                        )
                finally:
                    walk(child)

        walk(root)
        invalid = [item for item in controls if not item["valid"]]
        expected_version = json.loads((ROOT / "cuma_build_info.json").read_text(encoding="utf-8"))["version"]
        actual_version = str(getattr(cuma, "APP_DISPLAY_VERSION", ""))

        result = {
            "expected_version": expected_version,
            "actual_version": actual_version,
            "commands_checked": len(controls),
            "invalid_commands": invalid,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))

        if actual_version != expected_version:
            raise RuntimeError(
                f"Versão visual divergente: {actual_version!r}; esperado {expected_version!r}."
            )
        if invalid:
            labels = ", ".join(str(item.get("text") or item.get("class")) for item in invalid)
            raise RuntimeError(f"Controles com command inválido: {labels}")
        return 0
    finally:
        try:
            root.destroy()
        except Exception:
            pass
        shutil.rmtree(TEMP, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
