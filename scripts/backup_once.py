#!/usr/bin/env python3
"""Run a single backup snapshot via command line."""
import asyncio

from app.config import load_settings
from app.services.backup_svc import perform_backup
from app.utils.logging import setup_logging


async def main() -> None:
    settings = load_settings()
    setup_logging(settings.runtime_log, settings.actions_log)
    report = await perform_backup(settings)
    print(f"Backup selesai: {report.snapshot} -> manifest {report.manifest}")


if __name__ == "__main__":
    asyncio.run(main())
