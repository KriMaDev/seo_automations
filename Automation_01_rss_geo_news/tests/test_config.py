import dataclasses
import textwrap

import pytest
from pydantic import ValidationError

from app import config as config_module
from app.config import load_feed_sources, settings
from app.models import FeedSource


def _write_sources(tmp_path, content):
    path = tmp_path / "sources.yaml"
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
