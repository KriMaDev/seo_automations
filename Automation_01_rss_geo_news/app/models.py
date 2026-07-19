"""Article data model.

Represents a single piece of content collected from a source (RSS feeds
for now, other source types later). This module only defines the
schema — collection, deduplication, and storage live elsewhere.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class Article(BaseModel):
    """A single collected article/news item.

    Only title/url/source are required to construct an Article — feeds
    are inconsistent about categories, keywords, and summaries, and
    rejecting an article outright for missing them would silently lose
    otherwise valid data at collection time. Use `is_quality_candidate`
    as a soft completeness signal instead of a construction gate.
    """

    model_config = ConfigDict(frozen=True)

    title: str
    url: HttpUrl
    source: str
    categories: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    published_at: Optional[datetime] = None
    summary: Optional[str] = None
    author: Optional[str] = None
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("title", "source")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("summary", "author", mode="before")
    @classmethod
    def _blank_to_none(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("categories", "keywords", mode="before")
    @classmethod
    def _clean_string_list(cls, value: Optional[List[str]]) -> List[str]:
        if not value:
            return []
        seen: dict[str, None] = {}
        for raw in value:
            cleaned = raw.strip()
            if cleaned:
                seen.setdefault(cleaned, None)
        return list(seen)

    @property
    def is_quality_candidate(self) -> bool:
        """Soft completeness signal: has a summary and at least one category/keyword.

        Not a construction requirement — an Article missing these is
        still valid, just lower priority for discovery purposes.
        """
        return bool(self.summary) and bool(self.categories or self.keywords)


class FeedSource(BaseModel):
    """A single configured RSS feed to collect from."""

    name: str
    url: HttpUrl

    @field_validator("name")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped
