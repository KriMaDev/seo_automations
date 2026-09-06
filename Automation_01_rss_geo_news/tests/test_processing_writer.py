import json
from datetime import datetime, timezone

from app.models import ScoredArticle
from app.processing.writer import write_scored_article, write_scored_articles


def _make_scored(**overrides):
    fields = {
        "title": "Example Title",
        "url": "https://example.com/article",
        "source": "Example Feed",
        "matched_topics": ["SEO"],
        "relevance_score": 1,
        "is_relevant": True,
    }
    fields.update(overrides)
    return ScoredArticle(**fields)


def test_write_scored_article_creates_date_partitioned_file(tmp_path):
    collected_at = datetime(2026, 8, 4, 12, 0, tzinfo=timezone.utc)
    scored = _make_scored(collected_at=collected_at)

    path = write_scored_article(scored, processed_dir=tmp_path)

    assert path.parent.name == "2026-08-04"
    assert path.exists()


def test_write_scored_article_content_matches(tmp_path):
    scored = _make_scored(matched_topics=["SEO", "GEO"], relevance_score=3)

    path = write_scored_article(scored, processed_dir=tmp_path)

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["matched_topics"] == ["SEO", "GEO"]
    assert saved["relevance_score"] == 3
    assert saved["is_relevant"] is True


def test_write_scored_article_overwrites_existing_file(tmp_path):
    # Unlike raw storage, reprocessing the same article must update the
    # file — it's a pure function of raw data + topics.yaml, so a
    # retuned topics.yaml should be reflected on the next run.
    url = "https://example.com/article"
    first = _make_scored(url=url, relevance_score=1)
    second = _make_scored(url=url, relevance_score=5, matched_topics=["SEO", "GEO", "Video SEO"])

    path1 = write_scored_article(first, processed_dir=tmp_path)
    path2 = write_scored_article(second, processed_dir=tmp_path)

    assert path1 == path2
    saved = json.loads(path1.read_text(encoding="utf-8"))
    assert saved["relevance_score"] == 5
    assert len(list(tmp_path.rglob("*.json"))) == 1


def test_write_scored_articles_writes_all_including_reprocessed(tmp_path):
    scored_articles = [
        _make_scored(url="https://example.com/a"),
        _make_scored(url="https://example.com/a"),  # reprocessed, not a "duplicate" to skip
        _make_scored(url="https://example.com/b"),
    ]

    written = write_scored_articles(scored_articles, processed_dir=tmp_path)

    assert len(written) == 3
    assert len(list(tmp_path.rglob("*.json"))) == 2
