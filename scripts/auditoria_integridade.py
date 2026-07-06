#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auditoria de integridade usada antes dos builds e releases do CUMA."""
from __future__ import annotations

import argparse
import ast
import json
import py_compile
import re
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SHA_RE = re.compile(r"^[A-Fa-f0-9]{64}$")


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("raiz JSON não é um objeto")
    return data


def version_tuple(value: str) -> tuple[int, int, int]:
    if not VERSION_RE.fullmatch(value):
        raise ValueError(f"versão inválida: {value!r}")
    return tuple(int(part) for part in value.split("."))  # type: ignore[return-value]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="")
    parser.add_argument("--require-published-manifest", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    def fail(message: str) -> None:
        errors.append(message)
        print(f"[ERRO] {message}")

    def warn(message: str) -> None:
        warnings.append(message)
        print(f"[AVISO] {message}")

    def ok(message: str) -> None:
        print(f"[OK] {message}")

    required = [
        "cuma.py",
        "cuma_updater.py",
        "requirements.txt",
        "cuma_build_info.json",
        "cuma_windows.spec",
        "cuma_linux.spec",
        "cuma_macos.spec",
        "cuma_settings_template.json",
        "updates/stable.json",
        ".github/workflows/publicar_release.yml",
        "compilacao/Windows/criar_windows.bat",
        "compilacao/Linux/criar_linux_tar.sh",
        "compilacao/macOS/criar_macos_zip.sh",
        "scripts/release_pipeline.py",
        "scripts/smoke_interface.py",
        "scripts/testes_regressao_debug.py",
        "scripts/testar_bats_windows.py",
        "rodar_cuma.bat",
        "criar_exe_windows_e_zip.bat",
        "compilacao/Windows/rodar_cuma_windows.bat",
    ]
    for relative in required:
        if not (ROOT / relative).is_file():
            fail(f"Arquivo obrigatório ausente: {relative}")
    if errors:
        return 1
    ok("Estrutura obrigatória presente")

    for path in sorted(ROOT.rglob("*.py")):
        if any(part in {".venv", "build", "dist", "__pycache__"} for part in path.parts):
            continue
        try:
            source_text = path.read_text(encoding="utf-8")
            compile(source_text, str(path), "exec")
        except Exception as exc:
            fail(f"Sintaxe Python inválida em {path.relative_to(ROOT)}: {exc}")
    if not errors:
        ok("Sintaxe de todos os arquivos Python")

    json_files = [
        ROOT / "cuma_build_info.json",
        ROOT / "cuma_settings_template.json",
        ROOT / "updates/stable.json",
    ]
    for path in sorted((ROOT / "release").rglob("*.json")):
        json_files.append(path)
    parsed: dict[Path, dict] = {}
    for path in json_files:
        try:
            parsed[path] = load_json(path)
        except Exception as exc:
            fail(f"JSON inválido em {path.relative_to(ROOT)}: {exc}")
    if not errors:
        ok("Arquivos JSON válidos")

    source = (ROOT / "cuma.py").read_text(encoding="utf-8")
    updater = (ROOT / "cuma_updater.py").read_text(encoding="utf-8")
    expected = args.version.strip() or str(parsed[ROOT / "cuma_build_info.json"].get("version") or "")
    try:
        version_tuple(expected)
    except Exception as exc:
        fail(f"Versão fonte inválida: {exc}")
        expected = ""

    first = re.search(r'^APP_VERSION\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)\s+CUMA"\s*$', source, re.M)
    displays = re.findall(r'^APP_DISPLAY_VERSION\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"\s*$', source, re.M)
    final_constants = re.findall(
        r'^CUMA_[0-9]+_VERSION\s*=\s*["\']([0-9]+\.[0-9]+\.[0-9]+)["\']\s*$',
        source,
        re.M,
    )
    actuals = {
        "cuma.py/APP_VERSION": first.group(1) if first else "",
        "cuma.py/APP_DISPLAY_VERSION final": displays[-1] if displays else "",
        "cuma.py/camada final": final_constants[-1] if final_constants else "",
        "cuma_build_info.json": str(parsed[ROOT / "cuma_build_info.json"].get("version") or ""),
    }
    settings = parsed[ROOT / "cuma_settings_template.json"]
    actuals.update(
        {
            "settings/version_state": str(settings.get("version_state", {}).get("current_version") or ""),
            "settings/versioning": str(settings.get("versioning", {}).get("current_version") or ""),
            "settings/app": str(settings.get("app", {}).get("version") or ""),
        }
    )
    for label, actual in actuals.items():
        if expected and actual != expected:
            fail(f"Versão divergente em {label}: {actual!r}; esperado {expected!r}")
    if not errors:
        ok(f"Versão fonte sincronizada: {expected}")

    try:
        tree = ast.parse(source)
        entrypoints = []
        for node in tree.body:
            if isinstance(node, ast.If):
                segment = ast.get_source_segment(source, node.test) or ""
                if "__name__" in segment and "__main__" in segment:
                    entrypoints.append(node)
        if len(entrypoints) != 1:
            fail(f"Esperado um único entrypoint em cuma.py; encontrados {len(entrypoints)}")
        elif tree.body[-1] is not entrypoints[0]:
            fail("O entrypoint de cuma.py não é o último bloco do módulo")
        else:
            ok("Entrypoint único e no final de cuma.py")
    except Exception as exc:
        fail(f"Falha ao analisar AST de cuma.py: {exc}")

    if "self.resume_processing = tk.BooleanVar" in source:
        fail("Conflito conhecido: BooleanVar sobrescreve o método resume_processing")
    if "self.resume_processing_enabled = tk.BooleanVar" not in source:
        fail("A variável resume_processing_enabled não foi encontrada")
    if not errors:
        ok("Conflito dos botões Play corrigido")

    unsafe_patterns = [
        "zf.extractall(",
        "tf.extractall(",
        "ZipFile.extractall(",
        "TarFile.extractall(",
    ]
    for pattern in unsafe_patterns:
        if pattern in updater:
            fail(f"Extração insegura detectada no atualizador: {pattern}")
    for required_pattern in (
        "MAX_DOWNLOAD_BYTES",
        "MAX_ARCHIVE_MEMBERS",
        "MAX_ARCHIVE_UNCOMPRESSED_BYTES",
        'request.get("schema") != "CUMA_UPDATE_REQUEST"',
    ):
        if required_pattern not in updater:
            fail(f"Proteção esperada ausente no atualizador: {required_pattern}")
    if not errors:
        ok("Atualizador contém validações de download, request e arquivo compactado")

    stable = parsed[ROOT / "updates/stable.json"]
    stable_version = str(stable.get("version") or "")
    try:
        if expected and version_tuple(stable_version) > version_tuple(expected):
            fail(f"stable.json ({stable_version}) está à frente do código ({expected})")
    except Exception as exc:
        fail(f"Versão inválida em updates/stable.json: {exc}")

    platforms = stable.get("platforms", {})
    complete_manifest = True
    for platform in ("windows", "linux", "macos"):
        item = platforms.get(platform, {}) if isinstance(platforms, dict) else {}
        sha = str(item.get("sha256") or "")
        size = int(item.get("size_bytes") or 0)
        if not SHA_RE.fullmatch(sha) or size <= 0:
            complete_manifest = False
    if complete_manifest:
        ok(f"Manifesto publicado completo: {stable_version}")
    elif args.require_published_manifest:
        fail("stable.json ainda contém SHA/tamanho incompletos")
    else:
        warn(
            "stable.json ainda não está publicável; isso é permitido no código-fonte, "
            "mas a release automática precisa substituí-lo antes do update."
        )

    # Ambientes virtuais e saídas locais são deliberadamente ignorados.
    # O erro anterior percorria .venv depois que o próprio BAT a criava e
    # classificava milhares de .pyc de dependências como artefatos do projeto.
    ignored_generated_dirs = {
        ".git",
        ".venv",
        "venv",
        "env",
        "build",
        "dist",
        "ZIP final",
        ".release-runtime",
    }
    generated: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in ignored_generated_dirs for part in rel.parts):
            continue
        # __pycache__ e *.pyc são produtos locais normais e já estão no
        # .gitignore. A auditoria antiga os tratava como erro e impedia o
        # próprio BAT de continuar depois de criar/importar o ambiente.
        if "__pycache__" in rel.parts or path.suffix.lower() in {".pyc", ".pyo"}:
            continue
        if (
            rel.name.startswith("CUMA_")
            and rel.suffix.lower() in {".zip", ".rar", ".7z"}
            and not (len(rel.parts) >= 3 and rel.parts[:2] == ("release", "inbox"))
        ):
            generated.append(rel.as_posix())
    if generated:
        unique = sorted(set(generated))
        preview = ", ".join(unique[:20])
        remainder = len(unique) - 20
        if remainder > 0:
            preview += f" ... e mais {remainder} arquivo(s)"
        fail("Artefatos gerados dentro do código-fonte: " + preview)
    else:
        ok("Nenhum pacote de build indevido na árvore de código-fonte")

    bat_test = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "testar_bats_windows.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if bat_test.stdout:
        print(bat_test.stdout.rstrip())
    if bat_test.stderr and bat_test.returncode:
        print(bat_test.stderr.rstrip(), file=sys.stderr)
    if bat_test.returncode:
        fail(f"Auditoria dos BATs falhou com código {bat_test.returncode}")
    else:
        ok("Launchers BAT passaram na auditoria dedicada")

    workflow = (ROOT / ".github/workflows/publicar_release.yml").read_text(encoding="utf-8")
    for token in (
        "release/inbox/**",
        "CUMA_windows.zip",
        "CUMA_linux.tar.gz",
        "CUMA_macos.zip",
        "updates/stable.json",
        "gh release",
    ):
        if token not in workflow:
            fail(f"Workflow de release não contém etapa esperada: {token}")
    if not errors:
        ok("Workflow automático contém gatilho, três builds, Release e manifesto")

    print()
    print(f"Resultado: {len(errors)} erro(s), {len(warnings)} aviso(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
