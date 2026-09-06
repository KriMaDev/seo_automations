"""Processed article writer.

Persists ScoredArticle records to data/processed/YYYY-MM-DD/, one JSON
file per article, named by the same URL hash used in raw storage so
each processed record can be traced back to its raw source. Unlike raw
storage, this always overwrites — scoring is a pure function of the
raw article plus topics.yaml, so reprocessing (e.g. after tuning
topics) is expected and safe to repeat.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from app.config import settings
from app.logger import get_logger
from app.models import ScoredArticle
from app.storage.dedup import url_hash

logger = get_logger(__name__)


def write_scored_article(scored: ScoredArticle, processed_dir: Optional[Path] = None) -> Path:
    """Write one scored article to disk, overwriting any previous version."""
    root = processed_dir if processed_dir is not None else settings.processed_dir
    day_dir = root / scored.collected_at.strftime("%Y-%m-%d")
    day_dir.mkdir(parents=True, exist_ok=True)

    path = day_dir / f"{url_hash(str(scored.url))}.json"
    path.write_text(scored.model_dump_json(indent=2), encoding="utf-8")
    return path


def write_scored_articles(
    scored_articles: List[ScoredArticle], processed_dir: Optional[Path] = None
) -> List[Path]:
    """Write multiple scored articles. Returns the paths written."""
    written = [write_scored_article(scored, processed_dir) for scored in scored_articles]
    logger.info("Processed storage: %d article(s) written", len(written))
    return written
