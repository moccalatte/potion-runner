"""Helpers for updating dotenv-style configuration files."""
from __future__ import annotations

from pathlib import Path
from typing import Mapping


def _quote(value: str) -> str:
    escaped = value.replace("\"", "\\\"")
    return f'"{escaped}"'


def update_env_file(path: Path, updates: Mapping[str, str]) -> None:
    """Persist key/value pairs into a dotenv file while preserving other lines."""

    updates = {key: str(value) for key, value in updates.items()}
    lines: list[str] = []
    seen: set[str] = set()

    if path.exists():
        original = path.read_text(encoding="utf-8").splitlines()
    else:
        original = []

    for line in original:
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            lines.append(line)
            continue

        key, _sep, _value = line.partition("=")
        key = key.strip()
        if key in updates:
            lines.append(f"{key}={_quote(updates[key])}")
            seen.add(key)
        else:
            lines.append(line)

    for key, value in updates.items():
        if key not in seen:
            lines.append(f"{key}={_quote(value)}")

    path.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")


__all__ = ["update_env_file"]
