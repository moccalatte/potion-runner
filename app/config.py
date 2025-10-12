"""Application configuration management."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set

from dotenv import dotenv_values


@dataclass(slots=True)
class Thresholds:
    """Configuration for resource alert thresholds."""

    cpu_percent: float = 90.0
    ram_free_mb: float = 500.0
    disk_percent: float = 90.0
    temperature_c: float = 85.0
    hysteresis_minutes: int = 15


@dataclass(slots=True)
class Settings:
    """Main configuration object loaded from environment variables."""

    bot_token: str
    admin_ids: Set[int]
    env_file: Path
    data_dir: Path
    log_dir: Path
    backup_dir: Path
    manifests_dir: Path
    snapshots_dir: Path
    hdd_mount: Path
    services_whitelist: List[str]
    self_service: str
    runtime_log: Path
    actions_log: Path
    health_file: Path
    ping_host: str = "1.1.1.1"
    backup_schedule: str = "02:30"
    timezone: str = "UTC"
    thresholds: Thresholds = field(default_factory=Thresholds)
    backup_extra_sources: List[Path] = field(default_factory=list)

    def is_admin(self, user_id: Optional[int]) -> bool:
        return bool(user_id and user_id in self.admin_ids)


def _parse_admin_ids(raw: str | Sequence[str]) -> Set[int]:
    if isinstance(raw, str):
        candidates = [part.strip() for part in raw.split(",") if part.strip()]
    else:
        candidates = [str(item).strip() for item in raw if str(item).strip()]
    ids: Set[int] = set()
    for item in candidates:
        try:
            ids.add(int(item))
        except ValueError:
            continue
    return ids


def _parse_services(raw: str | Iterable[str]) -> List[str]:
    if isinstance(raw, str):
        items = [part.strip() for part in raw.split(",")]
    else:
        items = [str(part).strip() for part in raw]
    return [item for item in items if item]


def _parse_extra_paths(raw: str | Iterable[str], base: Path) -> List[Path]:
    if not raw:
        return []
    if isinstance(raw, str):
        items = [part.strip() for part in raw.split(",")]
    else:
        items = [str(part).strip() for part in raw]
    paths: list[Path] = []
    for item in items:
        if not item:
            continue
        candidate = Path(item)
        if not candidate.is_absolute():
            candidate = base / candidate
        paths.append(candidate)
    return paths


def _load_raw_env(env_path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if env_path.exists():
        env.update({k: v for k, v in dotenv_values(env_path).items() if v is not None})
    for key, value in os.environ.items():
        if key not in env:
            env[key] = value
    return env


def _normalize_schedule(raw: str | None, default: str = "02:30") -> str:
    if raw is None:
        return default
    candidate = str(raw).strip()
    if not candidate:
        return default
    candidate = candidate.replace(".", ":")
    parts = candidate.split(":")
    if len(parts) != 2:
        return default
    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError:
        return default
    if not (0 <= hour < 24 and 0 <= minute < 60):
        return default
    return f"{hour:02d}:{minute:02d}"


def load_settings(env_path: Path | None = None) -> Settings:
    """Load configuration from ``.env`` and environment variables."""

    env_path = env_path or Path(".env")
    raw_env = _load_raw_env(env_path)

    data_dir = Path(raw_env.get("DATA_DIR", "/opt/potion-runner"))
    log_dir = Path(raw_env.get("LOG_DIR", str(data_dir / "logs")))
    backup_dir = Path(raw_env.get("BACKUP_DIR", str(data_dir / "backups")))
    manifests_dir = backup_dir / "manifests"
    snapshots_dir = backup_dir / "snapshots"

    for directory in (data_dir, log_dir, backup_dir, manifests_dir, snapshots_dir):
        directory.mkdir(parents=True, exist_ok=True)

    runtime_log = log_dir / "runtime.log"
    actions_log = log_dir / "actions.log"
    health_file = data_dir / "last_health.json"

    default_thresholds = Thresholds()
    thresholds = Thresholds(
        cpu_percent=float(raw_env.get("THRESHOLD_CPU", default_thresholds.cpu_percent)),
        ram_free_mb=float(
            raw_env.get("THRESHOLD_RAM_MB", default_thresholds.ram_free_mb)
        ),
        disk_percent=float(raw_env.get("THRESHOLD_DISK", default_thresholds.disk_percent)),
        temperature_c=float(
            raw_env.get("THRESHOLD_TEMP", default_thresholds.temperature_c)
        ),
        hysteresis_minutes=int(
            raw_env.get(
                "THRESHOLD_HYSTERESIS_MIN", default_thresholds.hysteresis_minutes
            )
        ),
    )

    bot_token = raw_env.get("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is required. Set it in .env or environment variables.")

    admin_ids = _parse_admin_ids(raw_env.get("ADMIN_IDS", ""))
    if not admin_ids:
        raise RuntimeError("ADMIN_IDS is required with at least one Telegram user id.")

    services_whitelist = _parse_services(raw_env.get("SERVICES_WHITELIST", ""))
    services_whitelist = list(dict.fromkeys(services_whitelist))
    self_service = raw_env.get("SELF_SERVICE", "potion-runner.service").strip()

    backup_schedule = _normalize_schedule(raw_env.get("BACKUP_SCHEDULE", "02:30"))
    backup_extra_sources = _parse_extra_paths(raw_env.get("BACKUP_INCLUDE", ""), data_dir)
    settings = Settings(
        bot_token=bot_token,
        admin_ids=admin_ids,
        env_file=env_path,
        data_dir=data_dir,
        log_dir=log_dir,
        backup_dir=backup_dir,
        manifests_dir=manifests_dir,
        snapshots_dir=snapshots_dir,
        hdd_mount=Path(raw_env.get("HDD_MOUNT", "/mnt/potion-data")),
        services_whitelist=services_whitelist,
        self_service=self_service,
        runtime_log=runtime_log,
        actions_log=actions_log,
        health_file=health_file,
        ping_host=raw_env.get("PING_HOST", "1.1.1.1"),
        backup_schedule=backup_schedule,
        timezone=raw_env.get("TIMEZONE", "Asia/Jakarta"),
        thresholds=thresholds,
        backup_extra_sources=backup_extra_sources,
    )

    return settings


__all__ = ["Settings", "Thresholds", "load_settings"]
