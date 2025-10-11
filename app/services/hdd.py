"""Helpers for HDD mount and storage checks."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import psutil

from ..config import Settings
from ..utils.format import human_bytes


def is_mounted(path: Path) -> bool:
    for part in psutil.disk_partitions(all=False):
        if Path(part.mountpoint) == path:
            return True
    return False


def hdd_status(settings: Settings) -> Dict[str, str]:
    mount = settings.hdd_mount
    info = {
        "mount": str(mount),
        "mounted": "yes" if is_mounted(mount) else "no",
    }
    try:
        usage = psutil.disk_usage(str(mount))
        info.update(
            {
                "total": human_bytes(usage.total),
                "used": human_bytes(usage.used),
                "percent": f"{usage.percent:.1f}%",
            }
        )
    except FileNotFoundError:
        info["error"] = "Mount point tidak ditemukan"
    except PermissionError:
        info["error"] = "Tidak dapat membaca status mount (izin)"
    return info


def list_partitions() -> List[dict[str, str]]:
    partitions = []
    for part in psutil.disk_partitions(all=True):
        partitions.append(
            {
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "opts": part.opts,
            }
        )
    return partitions


__all__ = ["hdd_status", "list_partitions", "is_mounted"]
