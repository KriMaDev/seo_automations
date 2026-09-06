"""Ranking scored articles by relevance.

A pure sorting function — no file I/O. Kept separate from scoring
(topic_matcher.py) and writing (writer.py) since ranking is about the
relationship between all articles in a batch, not any single article.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from app.models import ScoredArticle

_MIN_DATETIME = datetime.min.replace(tzinfo=timezone.utc)


def rank_articles(scored_articles: List[ScoredArticle]) -> List[ScoredArticle]:
    """Sort scored articles by relevance, most relevant first.

    Primary key: relevance_score descending. Tie-break: published_at
    descending (newer wins on an equal score); articles with no
    published date sort last within a tie rather than crashing the sort.
    """
    return sorted(
        scored_articles,
        key=lambda article: (article.relevance_score, article.published_at or _MIN_DATETIME),
        reverse=True,
    )
