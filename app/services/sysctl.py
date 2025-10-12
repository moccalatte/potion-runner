"""Wrappers around systemctl and journalctl with whitelist validation."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Sequence

from ..config import Settings
from ..utils.format import human_datetime
from ..utils.logging import get_logger
from ..utils.shell import CommandResult, ShellCommandError, run_cmd

logger = get_logger(__name__)


@dataclass(slots=True)
class ServiceStatus:
    name: str
    active_state: str
    sub_state: str
    description: str
    since: str

    def is_healthy(self) -> bool:
        return self.active_state == "active" and self.sub_state in {"running", "listening"}


def _validate_service(settings: Settings, name: str) -> str:
    name = name.strip()
    if name not in settings.services_whitelist:
        raise ValueError(f"Service {name} tidak ada di whitelist. Update .env bila perlu.")
    return name


def _systemctl_command(*args: str, require_root: bool = False) -> tuple[str, ...]:
    base = ("systemctl",) + args
    try:
        need_sudo = require_root and os.geteuid() != 0
    except AttributeError:  # platform tanpa geteuid
        need_sudo = require_root
    if need_sudo:
        return ("sudo", "-n", *base)
    return base


async def _systemctl_show(service: str, properties: Sequence[str] | None = None) -> dict[str, str]:
    properties = properties or ["ActiveState", "SubState", "Description", "ActiveEnterTimestamp"]
    result = await run_cmd(
        _systemctl_command(
            "show",
            service,
            f"--property={','.join(properties)}",
            "--no-page",
        ),
        check=False,
    )
    if result.returncode != 0:
        raise ShellCommandError(tuple(result.command), result.returncode, result.stdout, result.stderr)
    data: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()
    return data


async def list_services(settings: Settings) -> List[ServiceStatus]:
    statuses: list[ServiceStatus] = []
    for service in settings.services_whitelist:
        try:
            data = await _systemctl_show(service)
        except ShellCommandError as exc:
            logger.warning("systemctl show gagal untuk %s: %s", service, exc)
            statuses.append(
                ServiceStatus(
                    name=service,
                    active_state="unknown",
                    sub_state="unknown",
                    description="Tidak dapat membaca status",
                    since=human_datetime(),
                )
            )
            continue
        statuses.append(
            ServiceStatus(
                name=service,
                active_state=data.get("ActiveState", "unknown"),
                sub_state=data.get("SubState", "unknown"),
                description=data.get("Description", ""),
                since=data.get("ActiveEnterTimestamp", ""),
            )
        )
    return statuses


async def control_service(settings: Settings, service: str, action: str) -> CommandResult:
    service = _validate_service(settings, service)
    if action not in {"start", "stop", "restart", "reload"}:
        raise ValueError("Aksi tidak valid. Gunakan start/stop/restart/reload.")

    logger.info("Menjalankan systemctl %s untuk %s", action, service)
    return await run_cmd(_systemctl_command(action, service, require_root=True))


async def service_status(settings: Settings, service: str) -> ServiceStatus:
    service = _validate_service(settings, service)
    data = await _systemctl_show(service)
    return ServiceStatus(
        name=service,
        active_state=data.get("ActiveState", "unknown"),
        sub_state=data.get("SubState", "unknown"),
        description=data.get("Description", ""),
        since=data.get("ActiveEnterTimestamp", ""),
    )


async def tail_journal(service: str, lines: int = 50) -> str:
    result = await run_cmd(
        (
            "journalctl",
            "-u",
            service,
            "-n",
            str(lines),
            "-o",
            "short-iso",
        ),
        check=False,
    )
    return result.stdout or result.stderr


async def check_failed_services(settings: Settings) -> List[ServiceStatus]:
    statuses = await list_services(settings)
    return [status for status in statuses if not status.is_healthy()]


__all__ = [
    "ServiceStatus",
    "list_services",
    "service_status",
    "control_service",
    "tail_journal",
    "check_failed_services",
]
