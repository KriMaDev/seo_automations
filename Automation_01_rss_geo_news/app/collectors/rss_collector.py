"""RSS feed collector.

Reads all configured RSS feeds and parses their entries into Article
objects. A problem with one feed or one entry is logged and skipped —
it never stops collection of the rest.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional, Tuple

import feedparser
from pydantic import ValidationError

from app.collectors.base import BaseCollector
from app.config import load_collection_window_days, load_feed_sources
from app.logger import get_logger
from app.models import Article, FeedSource

logger = get_logger(__name__)


class RSSCollector(BaseCollector):
    """Collects articles from a configured list of RSS feeds."""

    def __init__(
        self,
        sources: Optional[List[FeedSource]] = None,
        max_age_days: Optional[int] = None,
    ) -> None:
        self.sources = sources if sources is not None else load_feed_sources()
        self.max_age_days = (
            max_age_days if max_age_days is not None else load_collection_window_days()
        )

    def collect(self) -> List[Article]:
        articles: List[Article] = []
        for source in self.sources:
            articles.extend(self._collect_feed(source))
        return articles

    def _collect_feed(self, source: FeedSource) -> List[Article]:
        logger.info("Fetching feed: %s (%s)", source.name, source.url)

        try:
            parsed = feedparser.parse(str(source.url))
        except Exception:
            logger.exception("Failed to fetch/parse feed: %s (%s)", source.name, source.url)
            return []

        if parsed.get("bozo"):
            logger.warning(
                "Feed parse issue for %s: %s", source.name, parsed.get("bozo_exception")
            )

        cutoff = datetime.now(timezone.utc) - timedelta(days=self.max_age_days)
        articles: List[Article] = []
        skipped_old = 0
        for entry in parsed.get("entries", []):
            article = self._parse_entry(source, entry)
            if article is None:
                continue
            if article.published_at and article.published_at < cutoff:
                skipped_old += 1
                continue
            articles.append(article)

        logger.info(
            "Parsed %d article(s) from %s (%d outside %d-day window)",
            len(articles),
            source.name,
            skipped_old,
            self.max_age_days,
        )
        return articles

    def _parse_entry(self, source: FeedSource, entry: Any) -> Optional[Article]:
        categories, keywords = self._split_categories_and_keywords(entry)
        try:
            return Article(
                title=entry.get("title", ""),
                url=entry.get("link", ""),
                source=source.name,
                categories=categories,
                keywords=keywords,
                published_at=self._parse_published(entry),
                summary=entry.get("summary"),
                author=entry.get("author"),
            )
        except ValidationError as exc:
            logger.warning(
                "Skipping invalid entry from %s (%s): %s",
                source.name,
                entry.get("link", "unknown url"),
                exc,
            )
            return None

    @staticmethod
    def _split_categories_and_keywords(entry: Any) -> Tuple[List[str], List[str]]:
        """Sort feed tags into categories vs. keywords using the tag's scheme.

        Some feeds (e.g. WordPress) mark taxonomy categories and post
        tags with different domain/scheme URLs. When a feed doesn't
        distinguish them (most don't), everything falls back to
        categories rather than being dropped.
        """
        categories: List[str] = []
        keywords: List[str] = []
        for tag in entry.get("tags", []) or []:
            term = tag.get("term")
            if not term:
                continue
            scheme = (tag.get("scheme") or "").lower()
            if "tag" in scheme:
                keywords.append(term)
            else:
                categories.append(term)
        return categories, keywords

    @staticmethod
    def _parse_published(entry: Any) -> Optional[datetime]:
        parsed_time = entry.get("published_parsed") or entry.get("updated_parsed")
        if not parsed_time:
            return None
        return datetime(*parsed_time[:6], tzinfo=timezone.utc)
