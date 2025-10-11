"""Network helper utilities."""
from __future__ import annotations

import json
import socket
import shutil
from dataclasses import dataclass
from typing import Dict, List

import psutil

from ..config import Settings
from ..utils.shell import CommandResult, run_cmd


@dataclass(slots=True)
class IPInterface:
    name: str
    addresses: List[str]


async def ip_info() -> List[IPInterface]:
    interfaces: list[IPInterface] = []
    for name, addrs in psutil.net_if_addrs().items():
        addresses: list[str] = []
        for addr in addrs:
            if addr.family in {socket.AF_INET, socket.AF_INET6}:
                addresses.append(addr.address)
        if addresses:
            interfaces.append(IPInterface(name=name, addresses=addresses))
    return interfaces


async def ping(host: str, *, count: int = 4, deadline: int = 20) -> CommandResult:
    return await run_cmd(
        (
            "ping",
            "-c",
            str(count),
            "-w",
            str(deadline),
            host,
        ),
        check=False,
    )


async def tailscale_status() -> str:
    if shutil.which("tailscale") is None:
        return "Tailscale belum terpasang. Lewati langkah ini jika tidak perlu."
    result = await run_cmd(("tailscale", "status"), check=False)
    return result.stdout or result.stderr


async def speed_quick() -> str:
    if shutil.which("speedtest"):
        result = await run_cmd(
            (
                "speedtest",
                "--accept-license",
                "--accept-gdpr",
                "-f",
                "json",
            ),
            check=False,
        )
        if result.stdout:
            try:
                data = json.loads(result.stdout)
                download = data.get("download", {}).get("bandwidth", 0) * 8 / 1_000_000
                upload = data.get("upload", {}).get("bandwidth", 0) * 8 / 1_000_000
                ping_ms = data.get("ping", {}).get("latency", 0)
                return f"Download {download:.1f} Mbps | Upload {upload:.1f} Mbps | Ping {ping_ms:.0f} ms"
            except json.JSONDecodeError:
                pass
        return result.stdout or result.stderr or "Speedtest tidak memberikan hasil."

    if shutil.which("fast"):
        result = await run_cmd(("fast", "--upload"), check=False)
        return result.stdout or result.stderr

    return (
        "Tidak ada utilitas speedtest. Install 'speedtest-cli' atau 'fast-cli' untuk fitur ini."
    )


async def default_gateway() -> str:
    net_io = psutil.net_if_stats()
    lines = [f"{name}: up" if stats.isup else f"{name}: down" for name, stats in net_io.items()]
    return "\n".join(lines)


__all__ = ["ip_info", "ping", "tailscale_status", "speed_quick", "IPInterface", "default_gateway"]
