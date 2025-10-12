"""Backup and restore helpers built on rsync."""
from __future__ import annotations

import asyncio
import datetime as dt
import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List
from zoneinfo import ZoneInfo

from ..config import Settings
from ..utils.logging import get_logger
from ..utils.shell import run_cmd

logger = get_logger(__name__)


@dataclass(slots=True)
class BackupReport:
    snapshot: Path
    manifest: Path
    files_indexed: int
    rsync_output: List[str]


def _default_sources(settings: Settings) -> List[Path]:
    candidates = [
        settings.data_dir / "app",
        settings.log_dir,
        settings.data_dir / "requirements.lock",
        settings.data_dir / "ops",
        settings.data_dir / "scripts",
        settings.data_dir / ".env",
        *settings.backup_extra_sources,
    ]
    unique: dict[Path, None] = {}
    for path in candidates:
        if path.exists():
            unique.setdefault(path, None)
    return list(unique.keys())


async def perform_backup(settings: Settings, *, label: str | None = None) -> BackupReport:
    now = dt.datetime.now(ZoneInfo(settings.timezone))
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    label = label or timestamp
    snapshot_dir = settings.snapshots_dir / label
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    rsync_logs: list[str] = []
    sources = _default_sources(settings)
    loop = asyncio.get_running_loop()

    for source in sources:
        destination = snapshot_dir / source.name
        logger.info("Sinkron rsync %s -> %s", source, destination)
        if source.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            command = (
                "rsync",
                "-a",
                "--delete",
                str(source) + "/",
                str(destination),
            )
            result = await run_cmd(command, check=False)
            if result.stdout:
                rsync_logs.append(result.stdout)
            if result.stderr:
                rsync_logs.append(result.stderr)
        elif source.is_file():
            destination.parent.mkdir(parents=True, exist_ok=True)
            await loop.run_in_executor(None, shutil.copy2, source, destination)

    manifest_path = settings.manifests_dir / f"{label}.json"
    files_indexed = await _write_manifest(snapshot_dir, manifest_path)
    return BackupReport(snapshot=snapshot_dir, manifest=manifest_path, files_indexed=files_indexed, rsync_output=rsync_logs)


async def _write_manifest(snapshot_dir: Path, manifest_path: Path) -> int:
    loop = asyncio.get_running_loop()
    files: list[dict[str, str]] = []

    def _hash_path(path: Path) -> dict[str, str]:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        relative = path.relative_to(snapshot_dir)
        return {
            "path": str(relative),
            "sha256": digest.hexdigest(),
            "size": path.stat().st_size,
        }

    for file_path in snapshot_dir.rglob("*"):
        if file_path.is_file():
            data = await loop.run_in_executor(None, _hash_path, file_path)
            files.append(data)

    manifest = {
        "snapshot": snapshot_dir.name,
        "generated_at": dt.datetime.now(ZoneInfo(settings.timezone)).isoformat(),
        "files": files,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return len(files)


def list_snapshots(settings: Settings) -> List[Path]:
    if not settings.snapshots_dir.exists():
        return []
    return sorted(path for path in settings.snapshots_dir.iterdir() if path.is_dir())


async def verify_snapshot(manifest_path: Path) -> List[str]:
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest {manifest_path} tidak ditemukan")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    base_dir = manifest_path.parent.parent / "snapshots" / manifest["snapshot"]
    mismatches: list[str] = []

    for item in manifest.get("files", []):
        file_path = base_dir / item["path"]
        if not file_path.exists():
            mismatches.append(f"Hilang: {item['path']}")
            continue
        digest = hashlib.sha256()
        with file_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != item["sha256"]:
            mismatches.append(f"Berbeda: {item['path']}")
    return mismatches


def latest_backup_timestamp(settings: Settings) -> dt.datetime | None:
    if not settings.manifests_dir.exists():
        return None
    manifests = sorted(settings.manifests_dir.glob("*.json"), reverse=True)
    tz = ZoneInfo(settings.timezone)
    for manifest in manifests:
        label = manifest.stem
        try:
            parsed = dt.datetime.strptime(label, "%Y%m%d-%H%M%S")
        except ValueError:
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=tz)
        return parsed
    return None


def should_run_backup(settings: Settings, *, tolerance_minutes: int = 45) -> bool:
    latest = latest_backup_timestamp(settings)
    tz = ZoneInfo(settings.timezone)
    now = dt.datetime.now(tz)
    if latest is None:
        return True
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=tz)
    elapsed = now - latest
    return elapsed >= dt.timedelta(minutes=tolerance_minutes)


__all__ = [
    "perform_backup",
    "list_snapshots",
    "verify_snapshot",
    "BackupReport",
    "latest_backup_timestamp",
    "should_run_backup",
]
