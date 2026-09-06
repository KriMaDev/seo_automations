"""Processed/output writers.

write_scored_article(s) persists individual ScoredArticle records to
data/processed/YYYY-MM-DD/, one JSON file per article, named by the
same URL hash used in raw storage so each processed record can be
traced back to its raw source. Unlike raw storage, this always
overwrites — scoring is a pure function of the raw article plus
topics.yaml, so reprocessing (e.g. after tuning topics) is expected
and safe to repeat.

write_ranked_output writes the aggregate ranked view to data/outputs/
instead — one current snapshot, always overwritten, since ranking is
about the relationship between all articles, not a single one.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, Tuple

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


def write_ranked_output(
    ranked_articles: List[ScoredArticle], outputs_dir: Optional[Path] = None
) -> Tuple[Path, Path]:
    """Write the current ranked list to data/outputs/, overwriting each run.

    Writes two files reflecting the same ranking:
    - ranked_articles.json: the full list with an explicit rank field,
      machine-readable for whatever consumes it next.
    - ranked_articles.md: a plain-text summary (rank, score, title,
      matched topics, link) meant to be opened and read directly.
    """
    root = outputs_dir if outputs_dir is not None else settings.outputs_dir
    root.mkdir(parents=True, exist_ok=True)

    json_path = root / "ranked_articles.json"
    payload = [
        {"rank": i, **json.loads(article.model_dump_json())}
        for i, article in enumerate(ranked_articles, start=1)
    ]
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    summary_path = root / "ranked_articles.md"
    lines = ["# Ranked Articles", ""]
    for i, article in enumerate(ranked_articles, start=1):
        topics = ", ".join(article.matched_topics) or "—"
        lines.append(f"{i}. [{article.relevance_score}] {article.title} — {topics}")
        lines.append(f"   {article.url}")
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    logger.info(
        "Ranked output: %d article(s) written to %s and %s",
        len(ranked_articles),
        json_path,
        summary_path,
    )
    return json_path, summary_path
