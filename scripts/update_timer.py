#!/usr/bin/env python3
"""Update systemd timer schedule for potion backups."""

import argparse
import datetime as dt
import subprocess
from pathlib import Path


def run(cmd: list[str]) -> None:
    completed = subprocess.run(cmd, check=True, text=True, capture_output=True)
    if completed.stdout:
        print(completed.stdout.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Update jadwal potion-backup.timer")
    parser.add_argument("--time", required=True, help="Format HH:MM (24 jam)")
    parser.add_argument(
        "--timer",
        default="potion-backup.timer",
        help="Nama unit timer yang akan diperbarui",
    )
    args = parser.parse_args()

    try:
        parsed = dt.datetime.strptime(args.time, "%H:%M")
    except ValueError as exc:
        raise SystemExit(f"Format waktu tidak valid: {args.time}") from exc

    time_formatted = parsed.strftime("%H:%M:00")
    timer_name = args.timer
    dropin_dir = Path("/etc/systemd/system") / f"{timer_name}.d"
    dropin_dir.mkdir(parents=True, exist_ok=True)
    dropin_file = dropin_dir / "override.conf"
    dropin_file.write_text(
        "[Timer]\nOnCalendar=*-*-* {time}\n".format(time=time_formatted),
        encoding="utf-8",
    )
    run(["systemctl", "daemon-reload"])
    run(["systemctl", "restart", timer_name])
    print(f"Timer {timer_name} diperbarui ke {time_formatted}")


if __name__ == "__main__":
    main()
