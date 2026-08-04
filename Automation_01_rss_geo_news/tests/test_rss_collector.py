from datetime import datetime, timedelta, timezone

import feedparser

from app.collectors.rss_collector import RSSCollector
from app.models import FeedSource

SOURCE = FeedSource(name="Test Feed", url="https://example.com/feed")


def _entry(**overrides):
    fields = {
        "title": "Example Title",
        "link": "https://example.com/article",
    }
    fields.update(overrides)
    return fields


def _struct_time(days_ago=0):
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return dt.timetuple()


# --- _split_categories_and_keywords -----------------------------------------


def test_split_categories_no_tags_returns_empty():
    categories, keywords = RSSCollector._split_categories_and_keywords(_entry())
    assert categories == []
    assert keywords == []


def test_split_categories_untagged_scheme_goes_to_categories():
    entry = _entry(tags=[{"term": "SEO", "scheme": None}, {"term": "GEO", "scheme": ""}])
    categories, keywords = RSSCollector._split_categories_and_keywords(entry)
    assert categories == ["SEO", "GEO"]
    assert keywords == []


def test_split_categories_tag_scheme_goes_to_keywords():
    entry = _entry(
        tags=[
            {"term": "SEO", "scheme": "https://example.com/category/seo/"},
            {"term": "wordpress", "scheme": "https://example.com/tag/wordpress/"},
        ]
    )
    categories, keywords = RSSCollector._split_categories_and_keywords(entry)
    assert categories == ["SEO"]
    assert keywords == ["wordpress"]


def test_split_categories_scheme_matching_is_case_insensitive():
    entry = _entry(tags=[{"term": "wordpress", "scheme": "HTTPS://EXAMPLE.COM/TAG/wordpress/"}])
    _, keywords = RSSCollector._split_categories_and_keywords(entry)
    assert keywords == ["wordpress"]


def test_split_categories_skips_tags_without_term():
    entry = _entry(tags=[{"term": None, "scheme": None}, {"term": "SEO", "scheme": None}])
    categories, _ = RSSCollector._split_categories_and_keywords(entry)
    assert categories == ["SEO"]


# --- _parse_published ---------------------------------------------------


def test_parse_published_uses_published_parsed():
    entry = _entry(published_parsed=_struct_time())
    result = RSSCollector._parse_published(entry)
    assert result is not None
    assert result.tzinfo is not None


def test_parse_published_falls_back_to_updated_parsed():
    entry = _entry(updated_parsed=_struct_time())
    result = RSSCollector._parse_published(entry)
    assert result is not None


def test_parse_published_returns_none_when_neither_present():
    assert RSSCollector._parse_published(_entry()) is None


# --- _parse_entry --------------------------------------------------------


def test_parse_entry_builds_valid_article():
    collector = RSSCollector(sources=[])
    article = collector._parse_entry(SOURCE, _entry(summary="A summary.", author="Jane Doe"))
    assert article is not None
    assert article.title == "Example Title"
    assert str(article.url) == "https://example.com/article"
    assert article.source == "Test Feed"
    assert article.summary == "A summary."
    assert article.author == "Jane Doe"


def test_parse_entry_returns_none_for_missing_link():
    collector = RSSCollector(sources=[])
    article = collector._parse_entry(SOURCE, _entry(link=None))
    assert article is None


def test_parse_entry_returns_none_for_blank_title():
    collector = RSSCollector(sources=[])
    article = collector._parse_entry(SOURCE, _entry(title="   "))
    assert article is None


# --- collect() / _collect_feed (feedparser mocked) -----------------------


def test_collect_returns_articles_from_all_sources(monkeypatch):
    def fake_parse(url):
        return {"bozo": False, "entries": [_entry(title=f"Article for {url}")]}

    monkeypatch.setattr(feedparser, "parse", fake_parse)

    sources = [
        FeedSource(name="Feed A", url="https://a.example.com/feed"),
        FeedSource(name="Feed B", url="https://b.example.com/feed"),
    ]
    articles = RSSCollector(sources=sources).collect()

    assert len(articles) == 2
    assert {a.source for a in articles} == {"Feed A", "Feed B"}


def test_collect_skips_feed_that_raises_without_crashing(monkeypatch):
    def fake_parse(url):
        if "broken" in url:
            raise ValueError("network exploded")
        return {"bozo": False, "entries": [_entry()]}

    monkeypatch.setattr(feedparser, "parse", fake_parse)

    sources = [
        FeedSource(name="Broken Feed", url="https://broken.example.com/feed"),
        FeedSource(name="Good Feed", url="https://good.example.com/feed"),
    ]
    articles = RSSCollector(sources=sources).collect()

    assert len(articles) == 1
    assert articles[0].source == "Good Feed"


def test_collect_logs_bozo_warning_but_still_returns_entries(monkeypatch, caplog):
    def fake_parse(url):
        return {"bozo": True, "bozo_exception": "malformed xml", "entries": [_entry()]}

    monkeypatch.setattr(feedparser, "parse", fake_parse)

    with caplog.at_level("WARNING"):
        articles = RSSCollector(sources=[SOURCE]).collect()

    assert len(articles) == 1
    assert any("malformed xml" in record.message for record in caplog.records)


def test_collect_excludes_entries_outside_recency_window(monkeypatch):
    def fake_parse(url):
        return {
            "bozo": False,
            "entries": [
                _entry(link="https://example.com/recent", published_parsed=_struct_time(days_ago=1)),
                _entry(link="https://example.com/old", published_parsed=_struct_time(days_ago=30)),
            ],
        }

    monkeypatch.setattr(feedparser, "parse", fake_parse)

    articles = RSSCollector(sources=[SOURCE], max_age_days=7).collect()

    assert len(articles) == 1
    assert str(articles[0].url) == "https://example.com/recent"


def test_collect_keeps_entries_with_no_published_date(monkeypatch):
    # An entry with no date at all can't be judged as "old", so it's kept
    # rather than dropped for missing metadata (consistent with Article's
    # own permissive-by-default design).
    def fake_parse(url):
        return {"bozo": False, "entries": [_entry()]}  # no published/updated_parsed

    monkeypatch.setattr(feedparser, "parse", fake_parse)

    articles = RSSCollector(sources=[SOURCE], max_age_days=1).collect()

    assert len(articles) == 1
    assert articles[0].published_at is None
