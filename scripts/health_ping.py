#!/usr/bin/env python3
"""One-shot health snapshot writer."""
from app.config import load_settings
from app.services.metrics import collect_metrics, write_health_snapshot
from app.utils.logging import setup_logging


def main() -> None:
    settings = load_settings()
    setup_logging(settings.runtime_log, settings.actions_log)
    metrics = collect_metrics(settings)
    write_health_snapshot(metrics, settings.health_file)
    print("Health snapshot diperbarui.")


if __name__ == "__main__":
    main()
