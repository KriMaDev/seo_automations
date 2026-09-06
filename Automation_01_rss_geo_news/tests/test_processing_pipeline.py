from app.models import Article, ScoredArticle, Topic
from app.processing import pipeline as pipeline_module


def _article(**overrides):
    fields = {
        "title": "Example Title",
        "url": "https://example.com/article",
        "source": "Example Feed",
    }
    fields.update(overrides)
    return Article(**fields)


def test_run_orchestrates_read_score_write_and_logs_summary(monkeypatch, caplog):
    topics = [Topic(name="SEO", keywords=["seo"])]
    articles = [_article(title="An SEO Article")]

    monkeypatch.setattr(pipeline_module, "load_topics", lambda: topics)
    monkeypatch.setattr(pipeline_module, "read_raw_articles", lambda: articles)

    written_paths = []

    def fake_write(scored_articles, processed_dir=None):
        written_paths.extend(scored_articles)
        return [f"/fake/{i}.json" for i in range(len(scored_articles))]

    monkeypatch.setattr(pipeline_module, "write_scored_articles", fake_write)

    with caplog.at_level("INFO"):
        pipeline_module.run()

    assert len(written_paths) == 1
    assert isinstance(written_paths[0], ScoredArticle)
    assert any("Processing run complete" in record.message for record in caplog.records)
    assert any("1 topic(s) loaded" in record.message for record in caplog.records)
    assert any("1 article(s) read" in record.message for record in caplog.records)


def test_run_handles_no_raw_articles_without_crashing(monkeypatch, caplog):
    monkeypatch.setattr(pipeline_module, "load_topics", lambda: [])
    monkeypatch.setattr(pipeline_module, "read_raw_articles", lambda: [])
    monkeypatch.setattr(pipeline_module, "write_scored_articles", lambda scored, processed_dir=None: [])

    with caplog.at_level("INFO"):
        pipeline_module.run()

    assert any("0 article(s) read" in record.message for record in caplog.records)
