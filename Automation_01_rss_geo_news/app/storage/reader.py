"""Raw article reader.

Reads previously collected Article records back from
data/raw_articles/ (across all date folders) — the read-side
counterpart to writer.py. A malformed or unreadable file is logged and
skipped rather than raised, consistent with the rest of the pipeline.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pydantic import ValidationError

from app.config import settings
from app.logger import get_logger
from app.models import Article

logger = get_logger(__name__)


def read_raw_articles(raw_articles_dir: Optional[Path] = None) -> List[Article]:
    """Read every saved article back from data/raw_articles/ (all dates)."""
    root = raw_articles_dir if raw_articles_dir is not None else settings.raw_articles_dir
    if not root.exists():
        logger.info("Read 0 article(s) from %s (directory does not exist yet)", root)
        return []

    articles: List[Article] = []
    skipped = 0
    for path in sorted(root.glob("*/*.json")):
        try:
            articles.append(Article.model_validate_json(path.read_text(encoding="utf-8")))
        except (ValidationError, ValueError) as exc:
            logger.warning("Skipping unreadable article file %s: %s", path, exc)
            skipped += 1

    logger.info("Read %d article(s) from %s (%d skipped)", len(articles), root, skipped)
    return articles
