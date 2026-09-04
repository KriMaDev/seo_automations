import dataclasses
import textwrap

import pytest
from pydantic import ValidationError

from app import config as config_module
from app.config import load_collection_window_days, load_feed_sources, load_topics, settings
from app.models import FeedSource, Topic


def _write_sources(tmp_path, content):
    path = tmp_path / "sources.yaml"
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


def _write_collection_settings(tmp_path, content):
    path = tmp_path / "collection.yaml"
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


def _write_topics(tmp_path, content):
    path = tmp_path / "topics.yaml"
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


def test_load_feed_sources_parses_valid_yaml(tmp_path):
    path = _write_sources(
        tmp_path,
        """
        feeds:
          - name: Search Engine Journal
            url: https://www.searchenginejournal.com/feed/
          - name: Ahrefs Blog
            url: https://ahrefs.com/blog/feed/
        """,
    )
    feeds = load_feed_sources(path)
    assert feeds == [
        FeedSource(name="Search Engine Journal", url="https://www.searchenginejournal.com/feed/"),
        FeedSource(name="Ahrefs Blog", url="https://ahrefs.com/blog/feed/"),
    ]


def test_load_feed_sources_empty_file_returns_empty_list(tmp_path):
    path = _write_sources(tmp_path, "")
    assert load_feed_sources(path) == []


def test_load_feed_sources_missing_feeds_key_returns_empty_list(tmp_path):
    path = _write_sources(tmp_path, "some_other_key: []")
    assert load_feed_sources(path) == []


def test_load_feed_sources_rejects_feed_missing_url(tmp_path):
    path = _write_sources(
        tmp_path,
        """
        feeds:
          - name: No URL Feed
        """,
    )
    with pytest.raises(ValidationError):
        load_feed_sources(path)


def test_load_feed_sources_rejects_invalid_url(tmp_path):
    path = _write_sources(
        tmp_path,
        """
        feeds:
          - name: Bad Feed
            url: not-a-url
        """,
    )
    with pytest.raises(ValidationError):
        load_feed_sources(path)


def test_load_feed_sources_rejects_blank_name(tmp_path):
    path = _write_sources(
        tmp_path,
        """
        feeds:
          - name: "   "
            url: https://example.com/feed
        """,
    )
    with pytest.raises(ValidationError):
        load_feed_sources(path)


def test_load_feed_sources_defaults_to_settings_sources_file(monkeypatch, tmp_path):
    path = _write_sources(
        tmp_path,
        """
        feeds:
          - name: Only Feed
            url: https://example.com/feed
        """,
    )
    patched_settings = dataclasses.replace(settings, sources_file=path)
    monkeypatch.setattr(config_module, "settings", patched_settings)
    feeds = config_module.load_feed_sources()
    assert feeds == [FeedSource(name="Only Feed", url="https://example.com/feed")]


def test_real_sources_file_parses_successfully():
    feeds = load_feed_sources(settings.sources_file)
    names = {f.name for f in feeds}
    assert names == {
        "Search Engine Journal",
        "Search Engine Land",
        "Google Search Central",
        "Ahrefs Blog",
        "Moz Blog",
        "Semrush Blog",
        "OpenAI News",
    }


def test_load_collection_window_days_reads_configured_value(tmp_path):
    path = _write_collection_settings(tmp_path, "collection_window_days: 3")
    assert load_collection_window_days(path) == 3


def test_load_collection_window_days_defaults_when_file_missing(tmp_path):
    missing_path = tmp_path / "does_not_exist.yaml"
    assert load_collection_window_days(missing_path) == 14


def test_load_collection_window_days_defaults_when_key_missing(tmp_path):
    path = _write_collection_settings(tmp_path, "some_other_key: 3")
    assert load_collection_window_days(path) == 14


def test_real_collection_settings_file_parses_successfully():
    # Checks the real file parses to a sane value, not an exact number —
    # collection_window_days is meant to be tuned freely, so pinning an
    # exact value here would make the test break on every legitimate edit.
    window = load_collection_window_days(settings.collection_settings_file)
    assert isinstance(window, int)
    assert window > 0


def test_load_topics_parses_valid_yaml(tmp_path):
    path = _write_topics(
        tmp_path,
        """
        topics:
          - name: SEO
            keywords: [seo, backlinks]
          - name: GEO
            keywords: [geo, ai search]
        """,
    )
    topics = load_topics(path)
    assert topics == [
        Topic(name="SEO", keywords=["seo", "backlinks"]),
        Topic(name="GEO", keywords=["geo", "ai search"]),
    ]


def test_load_topics_empty_file_returns_empty_list(tmp_path):
    path = _write_topics(tmp_path, "")
    assert load_topics(path) == []


def test_load_topics_missing_topics_key_returns_empty_list(tmp_path):
    path = _write_topics(tmp_path, "some_other_key: []")
    assert load_topics(path) == []


def test_load_topics_rejects_topic_missing_keywords(tmp_path):
    path = _write_topics(
        tmp_path,
        """
        topics:
          - name: SEO
        """,
    )
    with pytest.raises(ValidationError):
        load_topics(path)


def test_load_topics_rejects_topic_with_only_blank_keywords(tmp_path):
    path = _write_topics(
        tmp_path,
        """
        topics:
          - name: SEO
            keywords: ["   ", ""]
        """,
    )
    with pytest.raises(ValidationError):
        load_topics(path)


def test_load_topics_rejects_blank_name(tmp_path):
    path = _write_topics(
        tmp_path,
        """
        topics:
          - name: "   "
            keywords: [seo]
        """,
    )
    with pytest.raises(ValidationError):
        load_topics(path)


def test_load_topics_deduplicates_keywords(tmp_path):
    path = _write_topics(
        tmp_path,
        """
        topics:
          - name: SEO
            keywords: [seo, SEO, "  seo  ", backlinks]
        """,
    )
    topics = load_topics(path)
    assert topics[0].keywords == ["seo", "SEO", "backlinks"]


def test_load_topics_defaults_to_settings_topics_file(monkeypatch, tmp_path):
    path = _write_topics(
        tmp_path,
        """
        topics:
          - name: Only Topic
            keywords: [only]
        """,
    )
    patched_settings = dataclasses.replace(settings, topics_file=path)
    monkeypatch.setattr(config_module, "settings", patched_settings)
    topics = config_module.load_topics()
    assert topics == [Topic(name="Only Topic", keywords=["only"])]


def test_real_topics_file_parses_successfully():
    topics = load_topics(settings.topics_file)
    names = {t.name for t in topics}
    assert names == {"SEO", "GEO", "Shopify SEO", "YouTube SEO", "Video SEO", "Social SEO"}
    assert all(len(t.keywords) > 0 for t in topics)
