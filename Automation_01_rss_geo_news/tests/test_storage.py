import json
from datetime import datetime, timezone

from app.models import Article
from app.storage.writer import write_article, write_articles


def _make_article(**overrides):
    fields = {
        "title": "Example Title",
        "url": "https://example.com/article",
        "source": "Example Feed",
    }
    fields.update(overrides)
    return Article(**fields)


def test_write_article_creates_date_partitioned_file(tmp_path):
    collected_at = datetime(2026, 8, 4, 12, 0, tzinfo=timezone.utc)
    article = _make_article(collected_at=collected_at)

    path = write_article(article, raw_articles_dir=tmp_path)

    assert path is not None
    assert path.parent.name == "2026-08-04"
    assert path.exists()


def test_write_article_content_matches_article(tmp_path):
    article = _make_article(title="A Real Title", summary="A summary.", categories=["SEO"])

    path = write_article(article, raw_articles_dir=tmp_path)

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["title"] == "A Real Title"
    assert saved["summary"] == "A summary."
    assert saved["categories"] == ["SEO"]
    assert saved["url"] == "https://example.com/article"


def test_write_article_skips_duplicate_and_does_not_overwrite(tmp_path):
    first = _make_article(title="Original Title", url="https://example.com/a")
    second = _make_article(title="Different Title", url="https://example.com/a")

    path1 = write_article(first, raw_articles_dir=tmp_path)
    path2 = write_article(second, raw_articles_dir=tmp_path)

    assert path1 is not None
    assert path2 is None

    files = list(tmp_path.rglob("*.json"))
    assert len(files) == 1
    saved = json.loads(files[0].read_text(encoding="utf-8"))
    assert saved["title"] == "Original Title"


def test_write_article_duplicate_across_different_dates_is_still_detected(tmp_path):
    url = "https://example.com/a"
    first = _make_article(url=url, collected_at=datetime(2026, 8, 1, tzinfo=timezone.utc))
    second = _make_article(url=url, collected_at=datetime(2026, 8, 4, tzinfo=timezone.utc))

    path1 = write_article(first, raw_articles_dir=tmp_path)
    path2 = write_article(second, raw_articles_dir=tmp_path)

    assert path1 is not None
    assert path2 is None
    assert len(list(tmp_path.rglob("*.json"))) == 1


def test_write_articles_writes_only_new_articles(tmp_path):
    articles = [
        _make_article(url="https://example.com/a"),
        _make_article(url="https://example.com/a"),  # duplicate within the same batch
        _make_article(url="https://example.com/b"),
    ]

    written = write_articles(articles, raw_articles_dir=tmp_path)

    assert len(written) == 2
    assert len(list(tmp_path.rglob("*.json"))) == 2


def test_write_articles_returns_empty_list_for_no_articles(tmp_path):
    assert write_articles([], raw_articles_dir=tmp_path) == []
