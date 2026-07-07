#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pipeline local do release automatizado do CUMA.

Comandos:
  prepare       valida release/inbox, aplica payload, sincroniza versão e gera contexto
  verify-asset  valida pacote gerado por uma plataforma
  manifest      gera updates/stable.json usando os três pacotes já compilados
  finalize      registra publicação e remove a pasta processada do inbox
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tarfile
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
PLATFORMS = {
    "windows": {
        "asset_name": "CUMA_windows.zip",
        "archive_type": "zip",
        "main_exe_name": "cuma.exe",
        "folder": "CUMA_windows",
        "receipt_name": "CUMA_windows.asset.json",
    },
    "linux": {
        "asset_name": "CUMA_linux.tar.gz",
        "archive_type": "tar.gz",
        "main_exe_name": "cuma",
        "folder": "CUMA_linux",
        "receipt_name": "CUMA_linux.asset.json",
    },
    "macos": {
        "asset_name": "CUMA_macos.zip",
        "archive_type": "zip",
        "main_exe_name": "cuma",
        "folder": "CUMA_macos",
        "receipt_name": "CUMA_macos.asset.json",
    },
}
FORBIDDEN_PAYLOAD_PREFIXES = (
    ".git",
    ".github/workflows",
    "release",
    "updates/stable.json",
)
MAX_PAYLOAD_FILES = 5000
MAX_PAYLOAD_BYTES = 200 * 1024 * 1024


class ReleaseError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReleaseError(f"Arquivo obrigatório ausente: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReleaseError(f"JSON inválido em {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ReleaseError(f"O JSON precisa conter um objeto: {path}")
    return data


def write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
    ) as handle:
        tmp = Path(handle.name)
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def version_tuple(value: str) -> tuple[int, int, int]:
    if not VERSION_RE.fullmatch(value):
        raise ReleaseError(f"Versão inválida: {value!r}. Use o formato 1.100.37.")
    return tuple(int(part) for part in value.split("."))  # type: ignore[return-value]


def normalize_relative_path(value: str, *, field: str) -> Path:
    raw = str(value or "").replace("\\", "/").strip()
    pure = PurePosixPath(raw)
    if not raw or pure.is_absolute() or ".." in pure.parts:
        raise ReleaseError(f"Caminho inseguro em {field}: {value!r}")
    if any(part in ("", ".") for part in pure.parts):
        raise ReleaseError(f"Caminho inválido em {field}: {value!r}")
    normalized = pure.as_posix()
    lower = normalized.lower()
    for prefix in FORBIDDEN_PAYLOAD_PREFIXES:
        if lower == prefix or lower.startswith(prefix + "/"):
            raise ReleaseError(f"O payload não pode alterar {normalized!r}")
    return Path(*pure.parts)


def validate_release_metadata(data: dict[str, Any], folder_name: str) -> dict[str, Any]:
    allowed = {
        "version",
        "summary",
        "notes",
        "mandatory",
        "minimum_supported_version",
        "prerelease",
        "delete",
    }
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise ReleaseError(f"Campos desconhecidos em release.json: {', '.join(unknown)}")

    version = str(data.get("version") or "").strip().lstrip("v")
    version_tuple(version)
    if folder_name and folder_name.lstrip("v") != version:
        raise ReleaseError(
            f"A pasta {folder_name!r} diverge da versão {version!r} informada no release.json."
        )

    summary = str(data.get("summary") or "").strip()
    if not summary or len(summary) > 240:
        raise ReleaseError("summary é obrigatório e deve ter no máximo 240 caracteres.")

    notes = data.get("notes")
    if not isinstance(notes, list) or not notes:
        raise ReleaseError("notes precisa ser uma lista não vazia.")
    cleaned_notes: list[str] = []
    for index, item in enumerate(notes, 1):
        note = str(item or "").strip()
        if not note:
            raise ReleaseError(f"notes[{index}] está vazio.")
        if len(note) > 500:
            raise ReleaseError(f"notes[{index}] excede 500 caracteres.")
        cleaned_notes.append(note)
    if len(cleaned_notes) > 50:
        raise ReleaseError("notes aceita no máximo 50 itens.")

    minimum = str(data.get("minimum_supported_version") or "1.080.0").strip().lstrip("v")
    version_tuple(minimum)
    mandatory = data.get("mandatory", False)
    prerelease = data.get("prerelease", False)
    if not isinstance(mandatory, bool) or not isinstance(prerelease, bool):
        raise ReleaseError("mandatory e prerelease precisam ser booleanos.")

    delete = data.get("delete", [])
    if not isinstance(delete, list):
        raise ReleaseError("delete precisa ser uma lista de caminhos.")
    cleaned_delete = [normalize_relative_path(str(item), field="delete").as_posix() for item in delete]

    return {
        "version": version,
        "summary": summary,
        "notes": cleaned_notes,
        "mandatory": mandatory,
        "minimum_supported_version": minimum,
        "prerelease": prerelease,
        "delete": cleaned_delete,
    }


def find_release_dir(requested: str) -> Path:
    inbox = ROOT / "release" / "inbox"
    if requested:
        candidate = Path(requested)
        if not candidate.is_absolute():
            if len(candidate.parts) == 1:
                candidate = inbox / candidate
            else:
                candidate = ROOT / candidate
        candidate = candidate.resolve()
        try:
            candidate.relative_to(inbox.resolve())
        except ValueError as exc:
            raise ReleaseError("A pasta de release precisa ficar dentro de release/inbox.") from exc
        if not candidate.is_dir():
            raise ReleaseError(f"Pasta de release não encontrada: {candidate}")
        return candidate

    candidates = sorted(
        p for p in inbox.iterdir()
        if p.is_dir() and (p / "release.json").is_file()
    ) if inbox.is_dir() else []
    if not candidates:
        raise ReleaseError("Nenhuma release pendente encontrada em release/inbox.")
    if len(candidates) > 1:
        names = ", ".join(p.name for p in candidates)
        raise ReleaseError(
            "Há mais de uma release no inbox. Processe uma por vez ou informe --release-dir: " + names
        )
    return candidates[0]


def safe_zip_members(path: Path) -> list[zipfile.ZipInfo]:
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        total = 0
        for info in infos:
            pure = PurePosixPath(info.filename.replace("\\", "/"))
            if pure.is_absolute() or ".." in pure.parts:
                raise ReleaseError(f"ZIP contém caminho inseguro: {info.filename!r}")
            mode = (info.external_attr >> 16) & 0o170000
            if mode == stat.S_IFLNK:
                raise ReleaseError(f"ZIP contém link simbólico: {info.filename!r}")
            total += int(info.file_size or 0)
        if len(infos) > MAX_PAYLOAD_FILES or total > MAX_PAYLOAD_BYTES:
            raise ReleaseError("payload.zip excede os limites de quantidade ou tamanho.")
        return infos


def collect_payload(release_dir: Path) -> list[tuple[Path, Path]]:
    """Retorna pares (origem, destino relativo)."""
    payload_dir = release_dir / "payload"
    payload_zip = release_dir / "payload.zip"
    if payload_dir.exists() and payload_zip.exists():
        raise ReleaseError("Use payload/ ou payload.zip, não os dois ao mesmo tempo.")

    pairs: list[tuple[Path, Path]] = []
    temp_dir: Path | None = None
    source_root: Path | None = None

    if payload_zip.exists():
        safe_zip_members(payload_zip)
        temp_dir = Path(tempfile.mkdtemp(prefix="cuma_release_payload_"))
        with zipfile.ZipFile(payload_zip) as archive:
            archive.extractall(temp_dir)
        children = [p for p in temp_dir.iterdir() if p.name != "__MACOSX"]
        if len(children) == 1 and children[0].is_dir():
            source_root = children[0]
        else:
            source_root = temp_dir
    elif payload_dir.exists():
        if payload_dir.is_symlink() or not payload_dir.is_dir():
            raise ReleaseError("payload precisa ser uma pasta real.")
        source_root = payload_dir
    else:
        return []

    total = 0
    try:
        for source in sorted(source_root.rglob("*")):
            if source.is_symlink():
                raise ReleaseError(f"Link simbólico não permitido no payload: {source}")
            if not source.is_file():
                continue
            relative = source.relative_to(source_root)
            target = normalize_relative_path(relative.as_posix(), field="payload")
            total += source.stat().st_size
            if len(pairs) >= MAX_PAYLOAD_FILES or total > MAX_PAYLOAD_BYTES:
                raise ReleaseError("Payload excede os limites de quantidade ou tamanho.")
            pairs.append((source, target))
        # Copia arquivos temporários antes de apagar a extração.
        if temp_dir is not None:
            persisted: list[tuple[Path, Path]] = []
            hold = Path(tempfile.mkdtemp(prefix="cuma_release_hold_"))
            for source, target in pairs:
                copy = hold / target
                copy.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, copy)
                persisted.append((copy, target))
            pairs = persisted
    finally:
        if temp_dir is not None:
            shutil.rmtree(temp_dir, ignore_errors=True)
    return pairs


def apply_payload(release_dir: Path, metadata: dict[str, Any]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for relative_text in metadata.get("delete", []):
        relative = normalize_relative_path(relative_text, field="delete")
        target = ROOT / relative
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
            changes.append({"path": relative.as_posix(), "action": "deleted"})
        elif target.exists() or target.is_symlink():
            target.unlink()
            changes.append({"path": relative.as_posix(), "action": "deleted"})

    for source, relative in collect_payload(release_dir):
        target = ROOT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        changes.append(
            {
                "path": relative.as_posix(),
                "action": "updated",
                "size_bytes": target.stat().st_size,
                "sha256": sha256_file(target),
            }
        )
    return changes


def replace_required(text: str, pattern: str, replacement: str, label: str, *, count: int = 0) -> str:
    result, hits = re.subn(pattern, replacement, text, count=count, flags=re.MULTILINE)
    if hits == 0:
        raise ReleaseError(f"Não foi possível atualizar a versão em {label}.")
    return result


def update_source_version(version: str) -> None:
    source_path = ROOT / "cuma.py"
    source = source_path.read_text(encoding="utf-8")

    source = replace_required(
        source,
        r'^APP_VERSION\s*=\s*"[0-9]+\.[0-9]+\.[0-9]+\s+CUMA"\s*$',
        f'APP_VERSION = "{version} CUMA"',
        "cuma.py/APP_VERSION",
        count=1,
    )
    source = replace_required(
        source,
        r'^APP_DISPLAY_VERSION\s*=\s*"[0-9]+\.[0-9]+\.[0-9]+"\s*$',
        f'APP_DISPLAY_VERSION = "{version}"',
        "cuma.py/APP_DISPLAY_VERSION",
    )
    source = replace_required(
        source,
        r'^CUMA_CONVERTER_DEVICE_UPDATE_VERSION\s*=\s*"[0-9]+\.[0-9]+\.[0-9]+"\s*$',
        f'CUMA_CONVERTER_DEVICE_UPDATE_VERSION = "{version}"',
        "cuma.py/CUMA_CONVERTER_DEVICE_UPDATE_VERSION",
        count=1,
    )

    # A última camada de patch é a fonte efetiva da versão no fim da importação.
    assignments = list(
        re.finditer(
            r'^(CUMA_[0-9]+_VERSION)\s*=\s*["\'][0-9]+\.[0-9]+\.[0-9]+["\']\s*$',
            source,
            flags=re.MULTILINE,
        )
    )
    if not assignments:
        raise ReleaseError("Nenhuma constante final CUMA_*_VERSION encontrada.")
    last = assignments[-1]
    source = source[: last.start()] + f'{last.group(1)} = "{version}"' + source[last.end() :]
    source_path.write_text(source, encoding="utf-8")

    settings_path = ROOT / "cuma_settings_template.json"
    settings = read_json(settings_path)
    for key in ("version_state", "version_history", "versioning"):
        if isinstance(settings.get(key), dict):
            settings[key]["current_version"] = version
    for key in ("version", "version_metadata"):
        if isinstance(settings.get(key), dict):
            settings[key]["version"] = version
            settings[key]["current_version"] = version
    if isinstance(settings.get("app"), dict):
        settings["app"]["version"] = version
        settings["app"]["display_version"] = version
    if isinstance(settings.get("metadata_system"), dict):
        settings["metadata_system"]["auto_volume_detection_version"] = version
    write_json_atomic(settings_path, settings)

    for relative in (
        "compilacao/Windows/criar_windows.bat",
        "compilacao/Linux/criar_linux_tar.sh",
        "compilacao/macOS/criar_macos_zip.sh",
    ):
        path = ROOT / relative
        if not path.exists():
            raise ReleaseError(f"Script de build ausente: {relative}")
        text = path.read_text(encoding="utf-8", errors="replace")
        text, hits = re.subn(
            r'(?:set\s+")?APP_VERSION\s*=\s*"?[0-9]+\.[0-9]+\.[0-9]+"?',
            (f'set "APP_VERSION={version}"' if path.suffix.lower() == ".bat" else f'APP_VERSION="{version}"'),
            text,
            count=1,
            flags=re.IGNORECASE,
        )
        if hits != 1:
            raise ReleaseError(f"Não foi possível sincronizar APP_VERSION em {relative}.")
        path.write_text(text, encoding="utf-8")

    version_file = ROOT / "cuma_build_info.json"
    write_json_atomic(
        version_file,
        {
            "name": "CUMA",
            "version": version,
            "updated_at": utc_now(),
        },
    )


def write_release_documents(metadata: dict[str, Any]) -> tuple[Path, Path]:
    version = metadata["version"]
    notes_lines = "\n".join(f"- {item}" for item in metadata["notes"])
    notes_text = (
        f"# CUMA {version}\n\n"
        f"{metadata['summary']}\n\n"
        f"## Alterações\n\n{notes_lines}\n"
    )
    notes_path = ROOT / "NOTAS_RELEASE.md"
    notes_path.write_text(notes_text, encoding="utf-8")

    changelog_path = ROOT / "CHANGELOG.md"
    if changelog_path.exists():
        old = changelog_path.read_text(encoding="utf-8")
    else:
        old = "# Histórico de versões do CUMA\n"
    marker = f"## {version}"
    section = f"\n## {version} — {datetime.now(timezone.utc).date().isoformat()}\n\n{metadata['summary']}\n\n{notes_lines}\n"
    if marker not in old:
        first_newline = old.find("\n")
        if first_newline < 0:
            old += "\n"
            first_newline = len(old) - 1
        old = old[: first_newline + 1] + section + old[first_newline + 1 :]
        changelog_path.write_text(old, encoding="utf-8")
    return notes_path, changelog_path


def read_published_version() -> str:
    stable_path = ROOT / "updates" / "stable.json"
    if not stable_path.exists():
        return "0.0.0"
    stable = read_json(stable_path)
    value = str(stable.get("version") or "0.0.0").strip().lstrip("v")
    version_tuple(value)
    return value


def prepare(args: argparse.Namespace) -> int:
    release_dir = find_release_dir(args.release_dir or "")
    raw = read_json(release_dir / "release.json")
    metadata = validate_release_metadata(raw, release_dir.name)

    published = read_published_version()
    if version_tuple(metadata["version"]) <= version_tuple(published):
        history = ROOT / "release" / "history" / metadata["version"] / "release.json"
        if not history.exists():
            raise ReleaseError(
                f"A versão {metadata['version']} precisa ser maior que a publicada ({published})."
            )

    changes = apply_payload(release_dir, metadata)
    update_source_version(metadata["version"])
    notes_path, _ = write_release_documents(metadata)

    history_dir = ROOT / "release" / "history" / metadata["version"]
    history_dir.mkdir(parents=True, exist_ok=True)
    history_release = {
        **metadata,
        "source": release_dir.relative_to(ROOT).as_posix(),
        "prepared_at": utc_now(),
        "payload_changes": changes,
        "status": "prepared",
    }
    write_json_atomic(history_dir / "release.json", history_release)
    shutil.copy2(notes_path, history_dir / "release-notes.md")

    context = {
        **metadata,
        "tag": f"v{metadata['version']}",
        "release_dir": release_dir.relative_to(ROOT).as_posix(),
        "history_dir": history_dir.relative_to(ROOT).as_posix(),
        "prepared_at": utc_now(),
        "published_version_before": published,
    }
    context_path = Path(args.context).resolve()
    write_json_atomic(context_path, context)
    notes_output = Path(args.notes_output).resolve()
    notes_output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(notes_path, notes_output)

    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            for key in ("version", "tag", "release_dir", "history_dir"):
                handle.write(f"{key}={context[key]}\n")
            handle.write(f"prerelease={'true' if context['prerelease'] else 'false'}\n")

    print(json.dumps(context, ensure_ascii=False, indent=2))
    return 0


def _archive_path(name: str, *, field: str = "entrada") -> PurePosixPath:
    """Normaliza um caminho interno sem permitir absoluto, drive ou traversal."""
    if "\\x00" in name:
        raise ReleaseError(f"{field.capitalize()} contém byte NUL: {name!r}")
    normalized = name.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if (
        not pure.parts
        or pure.is_absolute()
        or re.match(r"^[A-Za-z]:", normalized)
        or ".." in pure.parts
    ):
        raise ReleaseError(f"{field.capitalize()} contém caminho inseguro: {name!r}")
    return pure


def _validate_archive_member(name: str) -> None:
    _archive_path(name, field="arquivo compactado")


def _resolve_safe_link(
    member_name: str,
    link_target: str,
    *,
    hardlink: bool = False,
) -> PurePosixPath:
    """Resolve lexicalmente um link e exige que permaneça na raiz do pacote.

    Distribuições ``onedir`` do PyInstaller usam links simbólicos legítimos
    para bibliotecas e frameworks em Linux/macOS. Eles podem ser aceitos sem
    abrir traversal desde que sejam relativos e continuem sob a mesma pasta
    de topo do pacote (``CUMA_linux`` ou ``CUMA_macos``).
    """
    member = _archive_path(member_name, field="nome do link")
    if "\\x00" in link_target:
        raise ReleaseError(f"Destino de link contém byte NUL: {member_name!r}")
    normalized = link_target.replace("\\", "/")
    target = PurePosixPath(normalized)
    if (
        not target.parts
        or target.is_absolute()
        or re.match(r"^[A-Za-z]:", normalized)
    ):
        raise ReleaseError(
            f"Link possui destino absoluto ou inválido: {member_name!r} -> {link_target!r}"
        )

    package_root = member.parts[0]
    if hardlink:
        # Em TAR, hard links normalmente referenciam um nome a partir da raiz
        # do arquivo. Aceitamos também a forma relativa à pasta de topo.
        resolved: list[str] = [] if target.parts[0] == package_root else [package_root]
    else:
        resolved = list(member.parent.parts)

    for part in target.parts:
        if part in ("", "."):
            continue
        if part == "..":
            # Nunca permita remover a pasta de topo do pacote.
            if len(resolved) <= 1:
                raise ReleaseError(
                    f"Link escapa da raiz do pacote: {member_name!r} -> {link_target!r}"
                )
            resolved.pop()
            continue
        resolved.append(part)

    if not resolved or resolved[0] != package_root:
        raise ReleaseError(
            f"Link escapa da raiz do pacote: {member_name!r} -> {link_target!r}"
        )
    return PurePosixPath(*resolved)


def _zip_symlink_target(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> str:
    if info.file_size <= 0 or info.file_size > 4096:
        raise ReleaseError(f"ZIP contém link com destino inválido: {info.filename!r}")
    raw = archive.read(info)
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ReleaseError(
            f"ZIP contém link com destino não UTF-8: {info.filename!r}"
        ) from exc


def list_asset_members(path: Path) -> list[tuple[str, int]]:
    members: list[tuple[str, int]] = []
    lower = path.name.lower()
    if lower.endswith(".tar.gz") or lower.endswith(".tgz"):
        with tarfile.open(path, "r:gz") as archive:
            for member in archive.getmembers():
                _validate_archive_member(member.name)
                if member.isdev():
                    raise ReleaseError(f"TAR contém dispositivo ou FIFO: {member.name!r}")
                if member.issym():
                    _resolve_safe_link(member.name, member.linkname)
                    members.append((member.name.rstrip("/"), 0))
                elif member.islnk():
                    _resolve_safe_link(member.name, member.linkname, hardlink=True)
                    members.append((member.name.rstrip("/"), 0))
                elif member.isfile():
                    members.append((member.name.rstrip("/"), int(member.size or 0)))
                elif not member.isdir():
                    raise ReleaseError(f"TAR contém tipo especial: {member.name!r}")
    else:
        with zipfile.ZipFile(path) as archive:
            bad = archive.testzip()
            if bad:
                raise ReleaseError(f"ZIP corrompido; primeira entrada inválida: {bad}")
            for info in archive.infolist():
                _validate_archive_member(info.filename)
                mode = (info.external_attr >> 16) & 0o170000
                if mode == stat.S_IFLNK:
                    target = _zip_symlink_target(archive, info)
                    _resolve_safe_link(info.filename, target)
                    members.append((info.filename.rstrip("/"), 0))
                elif mode not in (0, stat.S_IFREG, stat.S_IFDIR):
                    raise ReleaseError(f"ZIP contém tipo especial: {info.filename!r}")
                elif not info.is_dir():
                    members.append((info.filename.rstrip("/"), int(info.file_size or 0)))
    return members


def verify_asset(args: argparse.Namespace) -> int:
    platform = args.platform
    if platform not in PLATFORMS:
        raise ReleaseError(f"Plataforma desconhecida: {platform}")
    path = Path(args.path).resolve()
    if not path.is_file() or path.stat().st_size <= 0:
        raise ReleaseError(f"Pacote ausente ou vazio: {path}")
    expected_name = PLATFORMS[platform]["asset_name"]
    if path.name != expected_name:
        raise ReleaseError(f"Nome incorreto: {path.name}; esperado {expected_name}.")

    members = list_asset_members(path)
    names = {name for name, _ in members}
    main = PLATFORMS[platform]["main_exe_name"]
    updater = "cuma_updater.exe" if platform == "windows" else "cuma_updater"

    def present(basename: str) -> bool:
        return any(PurePosixPath(name).name == basename for name in names)

    if not present(main):
        raise ReleaseError(f"{main} não foi encontrado dentro de {path.name}.")
    if not present(updater):
        raise ReleaseError(f"{updater} não foi encontrado dentro de {path.name}.")
    if not any("_internal" in PurePosixPath(name).parts for name in names):
        raise ReleaseError(f"A pasta _internal não foi encontrada em {path.name}.")

    result = {
        "platform": platform,
        "asset_name": path.name,
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "members": len(members),
    }
    if args.output:
        write_json_atomic(Path(args.output).resolve(), result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def find_asset(assets_dir: Path, name: str) -> Path:
    """Localiza exatamente um arquivo pelo nome dentro da árvore de artifacts."""
    direct = assets_dir / name
    if direct.is_file():
        return direct
    matches = sorted(path for path in assets_dir.rglob(name) if path.is_file())
    if len(matches) != 1:
        found = ", ".join(str(path.relative_to(assets_dir)) for path in matches[:10])
        detail = f" ({found})" if found else ""
        raise ReleaseError(
            f"Esperado exatamente um {name} em {assets_dir}; "
            f"encontrados {len(matches)}{detail}."
        )
    return matches[0]


def validate_asset_receipt(
    assets_dir: Path,
    platform: str,
    asset: Path,
    defaults: dict[str, Any],
) -> dict[str, Any]:
    """Confirma que o artifact baixado é idêntico ao validado no runner nativo.

    A inspeção estrutural completa ocorre no job de build da própria plataforma.
    O job final roda em Linux e não deve reinterpretar novamente ZIPs/TARs
    produzidos em Windows/macOS. Em vez disso, compara SHA-256 e tamanho com o
    recibo assinado pelo fluxo do mesmo job.
    """
    receipt_path = find_asset(assets_dir, str(defaults["receipt_name"]))
    receipt = read_json(receipt_path)

    expected_fields = {
        "platform": platform,
        "asset_name": defaults["asset_name"],
    }
    for field, expected in expected_fields.items():
        actual = receipt.get(field)
        if actual != expected:
            raise ReleaseError(
                f"Recibo inválido para {platform}: {field}={actual!r}; "
                f"esperado {expected!r}."
            )

    try:
        receipt_size = int(receipt.get("size_bytes"))
        receipt_members = int(receipt.get("members"))
    except (TypeError, ValueError) as exc:
        raise ReleaseError(f"Recibo inválido para {platform}: tamanho/membros inválidos.") from exc

    receipt_sha = str(receipt.get("sha256") or "").strip().upper()
    if not re.fullmatch(r"[0-9A-F]{64}", receipt_sha):
        raise ReleaseError(f"Recibo inválido para {platform}: SHA-256 ausente ou inválido.")
    if receipt_size <= 0 or receipt_members <= 0:
        raise ReleaseError(f"Recibo inválido para {platform}: pacote vazio.")

    actual_size = asset.stat().st_size
    actual_sha = sha256_file(asset)
    if actual_size != receipt_size:
        raise ReleaseError(
            f"Artifact {asset.name} mudou após a validação: "
            f"tamanho {actual_size}, esperado {receipt_size}."
        )
    if actual_sha != receipt_sha:
        raise ReleaseError(
            f"Artifact {asset.name} mudou após a validação: SHA-256 divergente."
        )

    return {
        "platform": platform,
        "asset_name": asset.name,
        "size_bytes": actual_size,
        "sha256": actual_sha,
        "members": receipt_members,
        "receipt": receipt_path.relative_to(assets_dir).as_posix(),
    }


def manifest(args: argparse.Namespace) -> int:
    context = read_json(Path(args.context).resolve())
    release_fields = {
        key: context[key]
        for key in (
            "version",
            "summary",
            "notes",
            "mandatory",
            "minimum_supported_version",
            "prerelease",
            "delete",
        )
        if key in context
    }
    metadata = validate_release_metadata(release_fields, "")
    tag = str(context.get("tag") or f"v{metadata['version']}").strip()
    repository = str(args.repository or "").strip().strip("/")
    if "/" not in repository:
        raise ReleaseError("--repository deve usar o formato owner/repo.")
    assets_dir = Path(args.assets_dir).resolve()
    base_url = f"https://github.com/{repository}/releases/download/{tag}"

    platforms: dict[str, Any] = {}
    sums: list[str] = []
    for platform, defaults in PLATFORMS.items():
        asset = find_asset(assets_dir, defaults["asset_name"])
        receipt = validate_asset_receipt(assets_dir, platform, asset, defaults)
        sha = receipt["sha256"]
        platforms[platform] = {
            "asset_name": asset.name,
            "download_url": f"{base_url}/{asset.name}",
            "sha256": sha,
            "size_bytes": receipt["size_bytes"],
            "archive_type": defaults["archive_type"],
            "main_exe_name": defaults["main_exe_name"],
        }
        sums.append(f"{sha}  {asset.name}")

    win = platforms["windows"]
    stable = {
        "app_id": "cuma",
        "channel": "stable",
        "version": metadata["version"],
        "minimum_supported_version": metadata["minimum_supported_version"],
        "mandatory": metadata["mandatory"],
        "published_at": utc_now(),
        "release_url": f"https://github.com/{repository}/releases/tag/{tag}",
        "release_notes": metadata["notes"],
        "platforms": platforms,
        # Compatibilidade com versões antigas do atualizador.
        "download_url": win["download_url"],
        "sha256": win["sha256"],
        "size_bytes": win["size_bytes"],
        "archive_type": win["archive_type"],
        "main_exe_name": win["main_exe_name"],
    }
    output = Path(args.output).resolve()
    write_json_atomic(output, stable)
    sums_path = Path(args.sums_output).resolve()
    sums_path.parent.mkdir(parents=True, exist_ok=True)
    sums_path.write_text("\n".join(sums) + "\n", encoding="utf-8")
    print(json.dumps(stable, ensure_ascii=False, indent=2))
    return 0


def finalize(args: argparse.Namespace) -> int:
    context = read_json(Path(args.context).resolve())
    manifest_data = read_json(Path(args.manifest).resolve())
    version = str(context["version"])
    history_dir = ROOT / str(context["history_dir"])
    publication = {
        "version": version,
        "tag": context["tag"],
        "published_at": manifest_data.get("published_at") or utc_now(),
        "release_url": manifest_data.get("release_url") or str(args.release_url or ""),
        "platforms": manifest_data.get("platforms", {}),
        "status": "published",
    }
    write_json_atomic(history_dir / "publication.json", publication)
    release_record = read_json(history_dir / "release.json")
    release_record["status"] = "published"
    release_record["published_at"] = publication["published_at"]
    write_json_atomic(history_dir / "release.json", release_record)

    release_dir = ROOT / str(context["release_dir"])
    if release_dir.exists():
        shutil.rmtree(release_dir)
    print(json.dumps(publication, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Automação de releases do CUMA")
    sub = parser.add_subparsers(dest="command", required=True)

    p_prepare = sub.add_parser("prepare")
    p_prepare.add_argument("--release-dir", default="")
    p_prepare.add_argument("--context", required=True)
    p_prepare.add_argument("--notes-output", required=True)
    p_prepare.set_defaults(func=prepare)

    p_verify = sub.add_parser("verify-asset")
    p_verify.add_argument("--platform", choices=sorted(PLATFORMS), required=True)
    p_verify.add_argument("--path", required=True)
    p_verify.add_argument("--output", default="")
    p_verify.set_defaults(func=verify_asset)

    p_manifest = sub.add_parser("manifest")
    p_manifest.add_argument("--context", required=True)
    p_manifest.add_argument("--assets-dir", required=True)
    p_manifest.add_argument("--repository", required=True)
    p_manifest.add_argument("--output", required=True)
    p_manifest.add_argument("--sums-output", required=True)
    p_manifest.set_defaults(func=manifest)

    p_finalize = sub.add_parser("finalize")
    p_finalize.add_argument("--context", required=True)
    p_finalize.add_argument("--manifest", required=True)
    p_finalize.add_argument("--release-url", default="")
    p_finalize.set_defaults(func=finalize)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except ReleaseError as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
