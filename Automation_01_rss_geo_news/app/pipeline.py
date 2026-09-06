"""Pipeline orchestration.

Ties the collector and storage layers together into a single run and
logs a clear summary at the end — feeds processed, articles found,
duplicates skipped, files written, warnings, and errors — so a run's
outcome is visible at a glance without piecing it together from
scattered per-feed log lines.
"""

from __future__ import annotations

import logging
import time

from app.collectors.rss_collector import RSSCollector
from app.logger import get_logger
from app.storage.writer import write_articles
from app.utils import LogOutcomeCounter

logger = get_logger(__name__)


def run() -> None:
    """Run one full collect-and-store cycle, logging a summary at the end."""
    counter = LogOutcomeCounter()
    root_logger = logging.getLogger()
    root_logger.addHandler(counter)

    start = time.monotonic()
    logger.info("Run started")

    try:
        collector = RSSCollector()
        articles = collector.collect()
        written = write_articles(articles)
    finally:
        root_logger.removeHandler(counter)

    duration = time.monotonic() - start
    logger.info(
        "Run complete: %d feed(s) processed, %d article(s) found, %d written, "
        "%d skipped (duplicate), %d warning(s), %d error(s), %.1fs",
        len(collector.sources),
        len(articles),
        len(written),
        len(articles) - len(written),
        counter.warnings,
        counter.errors,
        duration,
    )
