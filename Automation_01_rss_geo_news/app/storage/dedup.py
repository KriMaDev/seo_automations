"""Duplicate detection for collected articles.

Tracks which article URLs have already been saved to data/raw_articles
by hashing the URL into the filename an article would be saved under,
then checking the filesystem directly rather than maintaining a
separate index — the saved files are already the source of truth, and
a maintained index could drift out of sync with them (e.g. after a
manual file edit or a fresh clone missing history).
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

from app.config import settings


def url_hash(url: str) -> str:
    """Stable, filesystem-safe identifier for an article URL."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def find_existing(url: str, raw_articles_dir: Optional[Path] = None) -> Optional[Path]:
    """Return the path to an already-saved article with this URL, if any.

    Searches across all date-partitioned subfolders, since the same
    article could otherwise be re-saved under a different day.
    """
    root = raw_articles_dir if raw_articles_dir is not None else settings.raw_articles_dir
    if not root.exists():
        return None
    filename = f"{url_hash(url)}.json"
    matches = list(root.glob(f"*/{filename}"))
    return matches[0] if matches else None


def is_duplicate(url: str, raw_articles_dir: Optional[Path] = None) -> bool:
    """Whether an article with this URL has already been saved."""
    return find_existing(url, raw_articles_dir) is not None
