"""Shared utility helpers used across pipeline stages.

Cross-cutting helpers that don't belong to any single stage (collector,
storage, processing) live here.
"""

from __future__ import annotations

import logging


class LogOutcomeCounter(logging.Handler):
    """Counts WARNING/ERROR-and-above records emitted during a run.

    Attach to the root logger for the duration of a pipeline run to get
    warning/error totals for an end-of-run summary line, then remove it
    — used by both app.pipeline and app.processing.pipeline.
    """

    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.warnings = 0
        self.errors = 0

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.ERROR:
            self.errors += 1
        else:
            self.warnings += 1
