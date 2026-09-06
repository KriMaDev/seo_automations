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


def test_run_orchestrates_read_score_write_rank_and_logs_summary(monkeypatch, caplog):
    topics = [Topic(name="SEO", keywords=["seo"])]
    articles = [_article(title="An SEO Article")]

    monkeypatch.setattr(pipeline_module, "load_topics", lambda: topics)
    monkeypatch.setattr(pipeline_module, "read_raw_articles", lambda: articles)

    written_paths = []
    ranked_output_calls = []

    def fake_write(scored_articles, processed_dir=None):
        written_paths.extend(scored_articles)
        return [f"/fake/{i}.json" for i in range(len(scored_articles))]

    def fake_write_ranked_output(ranked_articles, outputs_dir=None):
        ranked_output_calls.append(ranked_articles)
        return "/fake/ranked_articles.json", "/fake/ranked_articles.md"

    monkeypatch.setattr(pipeline_module, "write_scored_articles", fake_write)
    monkeypatch.setattr(pipeline_module, "write_ranked_output", fake_write_ranked_output)

    with caplog.at_level("INFO"):
        pipeline_module.run()

    assert len(written_paths) == 1
    assert isinstance(written_paths[0], ScoredArticle)
    assert len(ranked_output_calls) == 1
    assert len(ranked_output_calls[0]) == 1
    assert any("Processing run complete" in record.message for record in caplog.records)
    assert any("1 topic(s) loaded" in record.message for record in caplog.records)
    assert any("1 article(s) read" in record.message for record in caplog.records)


def test_run_handles_no_raw_articles_without_crashing(monkeypatch, caplog):
    monkeypatch.setattr(pipeline_module, "load_topics", lambda: [])
    monkeypatch.setattr(pipeline_module, "read_raw_articles", lambda: [])
    monkeypatch.setattr(
        pipeline_module, "write_scored_articles", lambda scored, processed_dir=None: []
    )
    monkeypatch.setattr(
        pipeline_module,
        "write_ranked_output",
        lambda ranked, outputs_dir=None: ("/fake/ranked_articles.json", "/fake/ranked_articles.md"),
    )

    with caplog.at_level("INFO"):
        pipeline_module.run()

    assert any("0 article(s) read" in record.message for record in caplog.records)
