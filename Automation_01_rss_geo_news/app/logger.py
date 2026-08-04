"""Logging configuration for the SEO/GEO automation project.

Provides a single get_logger() factory so every module logs to the same
rotating file handler (and the console) with a consistent format.

Handlers are attached to the root logger, so genuine warnings/errors
from third-party libraries (e.g. the HTTP layer retrying a failed
request) are captured too — that's real signal worth having when
debugging a failed run. Only this app's own loggers ("app.*") have
their level explicitly raised to settings.log_level; third-party
loggers keep Python's default (WARNING), so their routine INFO/DEBUG
chatter is suppressed while real warnings/errors still come through.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.config import settings

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_BACKUP_COUNT = 5
_APP_LOGGER_NAME = "app"


def _configure_logging() -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return  # already configured

    settings.logs_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(_LOG_FORMAT)

    file_handler = RotatingFileHandler(
        settings.log_file,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.getLogger(_APP_LOGGER_NAME).setLevel(settings.log_level)


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger, configuring shared handlers on first use."""
    _configure_logging()
    return logging.getLogger(name)
