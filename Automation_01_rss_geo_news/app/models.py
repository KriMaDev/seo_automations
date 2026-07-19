"""Article data model.

Represents a single piece of content collected from a source (RSS feeds
for now, other source types later). This module only defines the
schema — collection, deduplication, and storage live elsewhere.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class Article(BaseModel):
    """A single collected article/news item."""

    model_config = ConfigDict(frozen=True)

    title: str
    url: HttpUrl
    source: str
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
