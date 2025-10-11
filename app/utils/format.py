"""Formatting helpers for human-readable bot messages."""
from __future__ import annotations

import datetime as _dt
from typing import Iterable, Sequence

SI_UNITS = ["B", "KB", "MB", "GB", "TB"]


def human_bytes(value: float) -> str:
    magnitude = 0
    while value >= 1024 and magnitude < len(SI_UNITS) - 1:
        value /= 1024
        magnitude += 1
    return f"{value:.1f} {SI_UNITS[magnitude]}"


def human_duration(seconds: float) -> str:
    delta = _dt.timedelta(seconds=int(seconds))
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, sec = divmod(remainder, 60)
    parts: list[str] = []
    if days:
        parts.append(f"{days} hari")
    if hours:
        parts.append(f"{hours} jam")
    if minutes:
        parts.append(f"{minutes} menit")
    if sec or not parts:
        parts.append(f"{sec} detik")
    return ", ".join(parts)


def human_datetime(dt: _dt.datetime | None = None) -> str:
    dt = dt or _dt.datetime.now(_dt.timezone.utc).astimezone()
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z")


def emoji_gauge(percent: float) -> str:
    bands = [
        (0, "🟢"),
        (60, "🟡"),
        (80, "🟠"),
        (90, "🔴"),
    ]
    emoji = "🟢"
    for threshold, symbol in bands:
        if percent >= threshold:
            emoji = symbol
    return emoji


def format_percentage(value: float, precision: int = 1) -> str:
    return f"{value:.{precision}f}%"


def render_table(rows: Sequence[Sequence[str]]) -> str:
    if not rows:
        return ""
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    lines: list[str] = []
    for row in rows:
        parts = [cell.ljust(widths[index]) for index, cell in enumerate(row)]
        lines.append(" | ".join(parts))
    return "\n".join(lines)


def join_bullets(items: Iterable[str]) -> str:
    return "\n".join(f"• {item}" for item in items)


__all__ = [
    "human_bytes",
    "human_duration",
    "human_datetime",
    "emoji_gauge",
    "format_percentage",
    "render_table",
    "join_bullets",
]
