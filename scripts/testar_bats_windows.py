#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida os launchers BAT do CUMA sem executar comandos destrutivos.

No Windows, use ``--execute-checks`` para também chamar os modos ``--check``.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BAT_FILES = (
    Path("rodar_cuma.bat"),
    Path("criar_exe_windows_e_zip.bat"),
    Path("compilacao/Windows/rodar_cuma.bat"),
    Path("compilacao/Windows/rodar_cuma_windows.bat"),
    Path("compilacao/Windows/criar_windows.bat"),
)

WRAPPER_TARGETS = {
    Path("rodar_cuma.bat"): Path("compilacao/Windows/rodar_cuma.bat"),
    Path("criar_exe_windows_e_zip.bat"): Path("compilacao/Windows/criar_windows.bat"),
    Path("compilacao/Windows/rodar_cuma_windows.bat"): Path(
        "compilacao/Windows/rodar_cuma.bat"
    ),
}

LABEL_RE = re.compile(r"^\s*:([A-Za-z0-9_.-]+)\s*$", re.MULTILINE)
GOTO_RE = re.compile(r"\bgoto\s+:?([A-Za-z0-9_.-]+)", re.IGNORECASE)
CALL_LABEL_RE = re.compile(r"\bcall\s+:([A-Za-z0-9_.-]+)", re.IGNORECASE)


def fail(errors: list[str], message: str) -> None:
    errors.append(message)
    print(f"[ERRO] {message}")


def read_bat(relative: Path) -> str:
    data = (ROOT / relative).read_bytes()
    if b"\x00" in data:
        raise ValueError("arquivo contém byte NUL")
    # Os arquivos são gravados em UTF-8 sem BOM e usam apenas comandos ASCII.
    return data.decode("utf-8-sig")


def check_parentheses(text: str) -> tuple[int, int]:
    """Contagem conservadora, ignorando parênteses dentro de aspas."""
    opened = closed = 0
    in_quotes = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.lower().startswith("rem ") or line.startswith("::"):
            continue
        escaped = False
        for char in raw_line:
            if escaped:
                escaped = False
                continue
            if char == "^":
                escaped = True
                continue
            if char == '"':
                in_quotes = not in_quotes
                continue
            if not in_quotes:
                if char == "(":
                    opened += 1
                elif char == ")":
                    closed += 1
        in_quotes = False
    return opened, closed


def static_checks() -> int:
    errors: list[str] = []

    for relative in BAT_FILES:
        path = ROOT / relative
        if not path.is_file():
            fail(errors, f"BAT obrigatório ausente: {relative.as_posix()}")
            continue
        try:
            text = read_bat(relative)
        except Exception as exc:
            fail(errors, f"Não foi possível ler {relative.as_posix()}: {exc}")
            continue

        if "\r\n" not in text and os.name == "nt":
            fail(errors, f"{relative.as_posix()} não usa finais de linha CRLF")

        labels = {match.lower() for match in LABEL_RE.findall(text)}
        targets = {
            match.lower()
            for match in GOTO_RE.findall(text) + CALL_LABEL_RE.findall(text)
            if match.lower() != "eof"
        }
        missing = sorted(targets - labels)
        if missing:
            fail(
                errors,
                f"{relative.as_posix()} referencia labels inexistentes: {', '.join(missing)}",
            )

        opened, closed = check_parentheses(text)
        if opened != closed:
            fail(
                errors,
                f"{relative.as_posix()} tem parênteses desequilibrados: "
                f"{opened} abertos, {closed} fechados",
            )

        lowered = text.lower()
        if "activate.bat" in lowered:
            fail(errors, f"{relative.as_posix()} ativa venv; deve chamar python.exe diretamente")
        if r"\github\cuma.py" in lowered or "repositorio_github" in lowered:
            fail(errors, f"{relative.as_posix()} contém layout legado fixo")
        if "py_compile" in lowered:
            fail(
                errors,
                f"{relative.as_posix()} usa py_compile e pode criar __pycache__ no repositório",
            )

    for wrapper, target in WRAPPER_TARGETS.items():
        if not (ROOT / target).is_file():
            fail(errors, f"Destino do wrapper ausente: {target.as_posix()}")
            continue
        text = read_bat(wrapper).lower()
        path_text = text.replace("/", "\\")
        target_fragment = str(target).replace("/", "\\").lower()
        # Para wrapper dentro de compilacao/Windows, basta o basename.
        expected = target.name.lower() if wrapper.parent != Path(".") else target_fragment
        if expected not in path_text:
            fail(
                errors,
                f"{wrapper.as_posix()} não encaminha para {target.as_posix()}",
            )
        if "exit /b %cuma_rc%" not in text.lower():
            fail(errors, f"{wrapper.as_posix()} não propaga o código de saída")

    runner = read_bat(Path("compilacao/Windows/rodar_cuma.bat")).lower()
    builder = read_bat(Path("compilacao/Windows/criar_windows.bat")).lower()

    for token in (
        "--fonte",
        "--compilado",
        "--check",
        "--diagnostico",
        "pythondontwritebytecode",
        "auditoria_integridade.py",
    ):
        if token not in runner:
            fail(errors, f"Launcher de execução não contém recurso obrigatório: {token}")

    for token in (
        "--check",
        "--clean",
        "--diagnostico",
        "pythondontwritebytecode",
        "auditoria_integridade.py",
        "release_pipeline.py",
        "verify-asset",
        "compress-archive",
    ):
        if token not in builder:
            fail(errors, f"Launcher de build não contém recurso obrigatório: {token}")

    if errors:
        print(f"\nResultado: {len(errors)} erro(s) nos BATs.")
        return 1
    print(f"[OK] {len(BAT_FILES)} BATs passaram na auditoria estática.")
    return 0


def execute_checks() -> int:
    if os.name != "nt":
        print("[AVISO] Checks dinâmicos ignorados: cmd.exe só existe no Windows.")
        return 0
    commands = (
        [str(ROOT / "rodar_cuma.bat"), "--check"],
        [str(ROOT / "criar_exe_windows_e_zip.bat"), "--check"],
        [str(ROOT / "compilacao/Windows/rodar_cuma_windows.bat"), "--check"],
    )
    env = os.environ.copy()
    env["CI"] = "true"
    for command in commands:
        print(f"[TESTE] {' '.join(command)}")
        command_line = f'call "{command[0]}" ' + subprocess.list2cmdline(command[1:])
        result = subprocess.run(
            ["cmd.exe", "/d", "/s", "/c", command_line],
            cwd=ROOT,
            env=env,
            timeout=120,
            check=False,
        )
        if result.returncode != 0:
            print(f"[ERRO] Falha dinâmica ({result.returncode}): {command[0]}")
            return result.returncode or 1
    print("[OK] Checks dinâmicos dos wrappers concluídos.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-checks", action="store_true")
    args = parser.parse_args()
    result = static_checks()
    if result:
        return result
    if args.execute_checks:
        return execute_checks()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
