"""Raw article writer.

Persists collected Article objects to data/raw_articles/YYYY-MM-DD/,
one JSON file per article, partitioned by the date each article was
collected. Existing files are never overwritten — an article whose URL
has already been saved (anywhere, any date) is skipped.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from app.config import settings
from app.logger import get_logger
from app.models import Article
from app.storage.dedup import is_duplicate, url_hash

logger = get_logger(__name__)


def write_article(article: Article, raw_articles_dir: Optional[Path] = None) -> Optional[Path]:
    """Write a single article to disk.

    Returns the path written to, or None if it was skipped as a
    duplicate (an article with this URL already exists on disk).
    """
    root = raw_articles_dir if raw_articles_dir is not None else settings.raw_articles_dir
    url = str(article.url)

    if is_duplicate(url, root):
        logger.info("Skipping duplicate article: %s", url)
        return None

    day_dir = root / article.collected_at.strftime("%Y-%m-%d")
    day_dir.mkdir(parents=True, exist_ok=True)
    path = day_dir / f"{url_hash(url)}.json"

    if path.exists():
        # Belt-and-suspenders: never overwrite, even if is_duplicate somehow missed it.
        logger.info("Skipping already-written article: %s", url)
        return None

    path.write_text(article.model_dump_json(indent=2), encoding="utf-8")
    logger.info("Wrote article: %s -> %s", url, path)
    return path


def write_articles(
    articles: List[Article], raw_articles_dir: Optional[Path] = None
) -> List[Path]:
    """Write multiple articles, skipping duplicates. Returns the paths actually written."""
    written: List[Path] = []
    for article in articles:
        path = write_article(article, raw_articles_dir)
        if path is not None:
            written.append(path)

    logger.info(
        "Storage: %d written, %d skipped (duplicate)",
        len(written),
        len(articles) - len(written),
    )
    return written
