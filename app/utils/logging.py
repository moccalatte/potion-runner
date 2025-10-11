"""Logging utilities for Potion Runner Bot."""
from __future__ import annotations

import logging
from logging import Logger
from pathlib import Path

from .format import human_datetime


def _configure_handler(handler: logging.Handler) -> None:
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)


def setup_logging(runtime_log: Path, actions_log: Path) -> None:
    runtime_log.parent.mkdir(parents=True, exist_ok=True)
    actions_log.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    file_handler = logging.FileHandler(runtime_log, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    _configure_handler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    _configure_handler(console_handler)

    root.addHandler(file_handler)
    root.addHandler(console_handler)

    actions_logger = logging.getLogger("potion.actions")
    actions_logger.setLevel(logging.INFO)
    actions_logger.propagate = False
    actions_logger.handlers.clear()

    actions_file_handler = logging.FileHandler(actions_log, encoding="utf-8")
    _configure_handler(actions_file_handler)
    actions_logger.addHandler(actions_file_handler)

    logging.getLogger(__name__).info(
        "Logging initialised. runtime_log=%s actions_log=%s",
        runtime_log,
        actions_log,
    )


def get_logger(name: str | None = None) -> Logger:
    return logging.getLogger(name or "potion")


def log_action(action: str, *, user_id: int | None, result: str, detail: str = "") -> None:
    logger = logging.getLogger("potion.actions")
    logger.info(
        "user=%s action=%s result=%s detail=%s at=%s",
        user_id,
        action,
        result,
        detail,
        human_datetime(),
    )


__all__ = ["setup_logging", "get_logger", "log_action"]
