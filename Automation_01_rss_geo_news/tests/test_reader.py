from app.models import Article
from app.storage.reader import read_raw_articles


def _make_article(**overrides):
    fields = {
        "title": "Example Title",
        "url": "https://example.com/article",
        "source": "Example Feed",
    }
    fields.update(overrides)
    return Article(**fields)


def test_read_raw_articles_returns_empty_list_when_dir_missing(tmp_path):
    missing = tmp_path / "does_not_exist"
    assert read_raw_articles(missing) == []


def test_read_raw_articles_returns_empty_list_when_dir_empty(tmp_path):
    assert read_raw_articles(tmp_path) == []


def test_read_raw_articles_reads_articles_across_date_folders(tmp_path):
    article_a = _make_article(url="https://example.com/a")
    article_b = _make_article(url="https://example.com/b")

    day1 = tmp_path / "2026-08-01"
    day2 = tmp_path / "2026-08-02"
    day1.mkdir()
    day2.mkdir()
    (day1 / "a.json").write_text(article_a.model_dump_json(), encoding="utf-8")
    (day2 / "b.json").write_text(article_b.model_dump_json(), encoding="utf-8")

    articles = read_raw_articles(tmp_path)

    assert {str(a.url) for a in articles} == {"https://example.com/a", "https://example.com/b"}


def test_read_raw_articles_skips_malformed_json(tmp_path, caplog):
    day_dir = tmp_path / "2026-08-01"
    day_dir.mkdir()
    (day_dir / "broken.json").write_text("{not valid json", encoding="utf-8")
    (day_dir / "good.json").write_text(_make_article().model_dump_json(), encoding="utf-8")

    with caplog.at_level("WARNING"):
        articles = read_raw_articles(tmp_path)

    assert len(articles) == 1
    assert any("broken.json" in record.message for record in caplog.records)


def test_read_raw_articles_skips_file_failing_validation(tmp_path, caplog):
    day_dir = tmp_path / "2026-08-01"
    day_dir.mkdir()
    # Valid JSON, but missing required fields (title/url/source).
    (day_dir / "invalid.json").write_text('{"summary": "no required fields"}', encoding="utf-8")

    with caplog.at_level("WARNING"):
        articles = read_raw_articles(tmp_path)

    assert articles == []
    assert any("invalid.json" in record.message for record in caplog.records)


def test_read_raw_articles_logs_summary_with_read_and_skipped_counts(tmp_path, caplog):
    day_dir = tmp_path / "2026-08-01"
    day_dir.mkdir()
    (day_dir / "good.json").write_text(_make_article().model_dump_json(), encoding="utf-8")
    (day_dir / "broken.json").write_text("{not valid json", encoding="utf-8")

    with caplog.at_level("INFO"):
        read_raw_articles(tmp_path)

    summary_lines = [r.message for r in caplog.records if r.message.startswith("Read ")]
    assert len(summary_lines) == 1
    assert "Read 1 article(s)" in summary_lines[0]
    assert "1 skipped" in summary_lines[0]
