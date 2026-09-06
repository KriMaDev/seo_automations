"""Processing pipeline orchestration.

Reads collected articles from data/raw_articles/, scores them against
the configured topics, writes the enriched result to data/processed/,
then ranks the full scored set and writes the current top-ranked view
to data/outputs/. Logs a summary at the end, mirroring app/pipeline.py.
"""

from __future__ import annotations

import logging
import time
from collections import Counter
from typing import List

from app.config import load_topics
from app.logger import get_logger
from app.models import ScoredArticle, Topic
from app.processing.ranker import rank_articles
from app.processing.topic_matcher import score_articles
from app.processing.writer import write_ranked_output, write_scored_articles
from app.storage.reader import read_raw_articles
from app.utils import LogOutcomeCounter

logger = get_logger(__name__)


def _log_topic_breakdown(scored: List[ScoredArticle], topics: List[Topic]) -> None:
    """Log how many articles matched each configured topic, including zero-match topics.

    Showing every configured topic (not just ones that matched at
    least once) makes a silently-broken keyword list visible — if a
    topic never shows up here, that's worth investigating.
    """
    counts = Counter(topic.name for topic in topics)
    counts.subtract(counts)  # zero out, keeps every configured topic present
    for article in scored:
        counts.update(article.matched_topics)

    breakdown = ", ".join(
        f"{name}={count}" for name, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    )
    logger.info("Topic breakdown: %s", breakdown or "no topics configured")


def run() -> None:
    """Run one full read-score-write-rank cycle, logging a summary at the end."""
    counter = LogOutcomeCounter()
    root_logger = logging.getLogger()
    root_logger.addHandler(counter)

    start = time.monotonic()
    logger.info("Processing run started")

    try:
        topics = load_topics()
        articles = read_raw_articles()
        scored = score_articles(articles, topics)

        for article in scored:
            logger.debug(
                "Scored '%s': topics=%s score=%d",
                article.title,
                article.matched_topics,
                article.relevance_score,
            )

        written = write_scored_articles(scored)
        ranked = rank_articles(scored)
        write_ranked_output(ranked)
        _log_topic_breakdown(scored, topics)
    finally:
        root_logger.removeHandler(counter)

    relevant = sum(1 for article in scored if article.is_relevant)
    duration = time.monotonic() - start
    logger.info(
        "Processing run complete: %d topic(s) loaded, %d article(s) read, %d scored, "
        "%d relevant, %d written, %d warning(s), %d error(s), %.1fs",
        len(topics),
        len(articles),
        len(scored),
        relevant,
        len(written),
        counter.warnings,
        counter.errors,
        duration,
    )
