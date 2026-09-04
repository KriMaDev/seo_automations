"""Topic/relevance scoring.

Scores a single Article against the configured topic list by
case-insensitive keyword matching against the article's own text
(title, summary, categories, keywords) — no network calls, no external
services, fully deterministic. See FUTURE_IDEAS.md for the known
ceiling of this approach and the planned upgrade path.
"""

from __future__ import annotations

import re
from typing import List, Set

from app.models import Article, ScoredArticle, Topic

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _searchable_text(article: Article) -> str:
    """Combine the article's own text fields into one lowercased blob to search.

    Deliberately excludes url and source: a URL slug or publisher name
    isn't "about" a topic the way the title/summary/tags are, and
    matching against them risks noisy false positives (e.g. a keyword
    substring turning up inside a boilerplate link URL).
    """
    summary_text = _HTML_TAG_RE.sub(" ", article.summary or "")
    parts = [
        article.title,
        summary_text,
        " ".join(article.categories),
        " ".join(article.keywords),
    ]
    return " ".join(parts).lower()


def score_article(article: Article, topics: List[Topic]) -> ScoredArticle:
    """Score one article against the configured topics.

    matched_topics lists every topic with at least one keyword hit.
    relevance_score is the count of distinct keywords matched across
    all topics combined (not per-topic), so a topic with more
    configured keywords isn't automatically favored over one with
    fewer — this is a simple, explainable v1 signal, not a weighted
    quality score.
    """
    text = _searchable_text(article)

    matched_topics: List[str] = []
    matched_keywords: Set[str] = set()

    for topic in topics:
        topic_matched = False
        for keyword in topic.keywords:
            if keyword.lower() in text:
                matched_keywords.add(keyword.lower())
                topic_matched = True
        if topic_matched:
            matched_topics.append(topic.name)

    relevance_score = len(matched_keywords)

    return ScoredArticle(
        **article.model_dump(),
        matched_topics=matched_topics,
        relevance_score=relevance_score,
        is_relevant=relevance_score > 0,
    )


def score_articles(articles: List[Article], topics: List[Topic]) -> List[ScoredArticle]:
    """Score a batch of articles against the configured topics."""
    return [score_article(article, topics) for article in articles]
