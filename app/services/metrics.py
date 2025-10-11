"""System metrics collection and health monitoring."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Sequence

import psutil

from ..config import Settings, Thresholds
from ..utils.format import human_bytes
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class Temperature:
    label: str
    current: float


@dataclass(slots=True)
class SystemMetrics:
    timestamp: dt.datetime
    cpu_percent: float
    load_avg: Sequence[float]
    mem_total: int
    mem_available: int
    mem_percent: float
    swap_percent: float
    disk_root_percent: float
    disk_root_free: int
    disk_hdd_percent: float | None
    disk_hdd_free: int | None
    uptime_seconds: float
    temperatures: List[Temperature] = field(default_factory=list)

    def mem_available_mb(self) -> float:
        return self.mem_available / (1024 * 1024)


@dataclass(slots=True)
class Alert:
    code: str
    message: str


class HealthMonitor:
    """Track metric breaches and emit alerts with hysteresis."""

    def __init__(self, thresholds: Thresholds):
        self.thresholds = thresholds
        self._breach_started: Dict[str, dt.datetime] = {}
        self._active_alerts: Dict[str, dt.datetime] = {}
        self._cooldown: Dict[str, dt.datetime] = {}
        self._last_snapshot: SystemMetrics | None = None

    def evaluate(self, metrics: SystemMetrics, failed_services: Sequence[str]) -> tuple[List[Alert], List[str]]:
        now = metrics.timestamp
        triggered: List[Alert] = []
        recovered: List[str] = []

        checks = [
            (
                metrics.cpu_percent >= self.thresholds.cpu_percent,
                "cpu_high",
                f"CPU tinggi {metrics.cpu_percent:.1f}%",
                dt.timedelta(minutes=5),
            ),
            (
                metrics.mem_available_mb() <= self.thresholds.ram_free_mb,
                "ram_low",
                f"RAM tersisa {metrics.mem_available_mb():.0f} MB",
                dt.timedelta(minutes=2),
            ),
            (
                metrics.disk_root_percent >= self.thresholds.disk_percent,
                "disk_root",
                f"Disk / mencapai {metrics.disk_root_percent:.1f}%",
                dt.timedelta(minutes=1),
            ),
            (
                (metrics.disk_hdd_percent or 0) >= self.thresholds.disk_percent,
                "disk_hdd",
                f"Disk HDD mencapai {metrics.disk_hdd_percent:.1f}%",
                dt.timedelta(minutes=1),
            ),
        ]

        if metrics.temperatures:
            max_temp = max(temp.current for temp in metrics.temperatures)
            checks.append(
                (
                    max_temp >= self.thresholds.temperature_c,
                    "temp_high",
                    f"Suhu CPU {max_temp:.0f}°C",
                    dt.timedelta(minutes=3),
                )
            )

        for condition, code, message, delay in checks:
            self._process_condition(condition, code, message, delay, now, triggered, recovered)

        for service in failed_services:
            message = f"Service {service} gagal"
            self._process_condition(
                True,
                f"svc_{service}",
                message,
                dt.timedelta(seconds=0),
                now,
                triggered,
                recovered,
            )

        # Recovery when metrics back to normal but alert is active
        for code in list(self._active_alerts.keys()):
            if any(alert.code == code for alert in triggered):
                continue
            if self._is_condition_resolved(code, checks, failed_services):
                logger.info("Alert %s pulih", code)
                self._active_alerts.pop(code, None)
                recovered.append(code)

        self._last_snapshot = metrics
        return triggered, recovered

    def _process_condition(
        self,
        condition: bool,
        code: str,
        message: str,
        delay: dt.timedelta,
        now: dt.datetime,
        triggered: List[Alert],
        recovered: List[str],
    ) -> None:
        cooldown_until = self._cooldown.get(code)
        if not condition:
            self._breach_started.pop(code, None)
            return

        start = self._breach_started.get(code)
        if not start:
            self._breach_started[code] = now
            logger.debug("Breach %s mulai pada %s", code, now)
            return

        if now - start < delay:
            return

        if cooldown_until and now < cooldown_until:
            return

        if code in self._active_alerts:
            return

        logger.warning("Alert %s dipicu: %s", code, message)
        self._active_alerts[code] = now
        self._cooldown[code] = now + dt.timedelta(minutes=self.thresholds.hysteresis_minutes)
        triggered.append(Alert(code=code, message=message))

    def _is_condition_resolved(
        self,
        code: str,
        checks: Sequence[tuple[bool, str, str, dt.timedelta]],
        failed_services: Sequence[str],
    ) -> bool:
        if code.startswith("svc_"):
            name = code.split("_", 1)[1]
            return name not in failed_services
        for condition, chk_code, *_rest in checks:
            if chk_code == code:
                return not condition
        return True


def collect_metrics(settings: Settings) -> SystemMetrics:
    timestamp = dt.datetime.now(dt.timezone.utc)
    cpu_percent = psutil.cpu_percent(interval=0.5)
    load_avg = psutil.getloadavg() if hasattr(psutil, "getloadavg") else (0.0, 0.0, 0.0)
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk_root = psutil.disk_usage("/")

    try:
        disk_hdd = psutil.disk_usage(str(settings.hdd_mount))
        disk_hdd_percent = disk_hdd.percent
        disk_hdd_free = disk_hdd.free
    except FileNotFoundError:
        disk_hdd_percent = None
        disk_hdd_free = None

    uptime_seconds = timestamp.timestamp() - psutil.boot_time()

    temps: list[Temperature] = []
    if hasattr(psutil, "sensors_temperatures"):
        try:
            temperatures = psutil.sensors_temperatures()
            for label, entries in temperatures.items():
                for entry in entries:
                    if entry.current is not None:
                        temps.append(Temperature(label=f"{label} {entry.label or ''}".strip(), current=entry.current))
        except Exception as exc:  # pragma: no cover - library dependent
            logger.debug("Tidak dapat membaca suhu: %s", exc)

    metrics = SystemMetrics(
        timestamp=timestamp,
        cpu_percent=cpu_percent,
        load_avg=load_avg,
        mem_total=memory.total,
        mem_available=memory.available,
        mem_percent=memory.percent,
        swap_percent=swap.percent,
        disk_root_percent=disk_root.percent,
        disk_root_free=disk_root.free,
        disk_hdd_percent=disk_hdd_percent,
        disk_hdd_free=disk_hdd_free,
        uptime_seconds=uptime_seconds,
        temperatures=temps,
    )
    logger.debug("Metrics terkumpul: %s", metrics)
    return metrics


def metrics_summary(metrics: SystemMetrics) -> str:
    parts = [
        f"CPU {metrics.cpu_percent:.1f}% ({', '.join(f'{val:.2f}' for val in metrics.load_avg)} load)",
        f"RAM {metrics.mem_percent:.1f}% tersedia {human_bytes(metrics.mem_available)}",
        f"Disk / {metrics.disk_root_percent:.1f}% tersisa {human_bytes(metrics.disk_root_free)}",
    ]
    if metrics.disk_hdd_percent is not None and metrics.disk_hdd_free is not None:
        parts.append(
            f"Disk HDD {metrics.disk_hdd_percent:.1f}% tersisa {human_bytes(metrics.disk_hdd_free)}"
        )
    parts.append(f"Uptime {metrics.uptime_seconds/3600:.1f} jam")
    if metrics.temperatures:
        top = max(metrics.temperatures, key=lambda item: item.current)
        parts.append(f"Suhu {top.label} {top.current:.0f}°C")
    return " | ".join(parts)


def write_health_snapshot(metrics: SystemMetrics, path: Path) -> None:
    import json

    content = {
        "timestamp": metrics.timestamp.isoformat(),
        "cpu_percent": metrics.cpu_percent,
        "mem_available": metrics.mem_available,
        "disk_root_percent": metrics.disk_root_percent,
    }
    path.write_text(json.dumps(content, indent=2), encoding="utf-8")


__all__ = [
    "SystemMetrics",
    "collect_metrics",
    "metrics_summary",
    "HealthMonitor",
    "Alert",
    "write_health_snapshot",
]
