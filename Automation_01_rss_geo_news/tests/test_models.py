from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models import Article


def _make(**overrides):
    fields = {
        "title": "Example Title",
        "url": "https://example.com/article",
        "source": "Example Feed",
    }
    fields.update(overrides)
    return Article(**fields)


def test_valid_article_constructs():
    article = _make()
    assert article.title == "Example Title"
    assert str(article.url) == "https://example.com/article"
    assert article.source == "Example Feed"


def test_optional_fields_default_to_none():
    article = _make()
    assert article.published_at is None
    assert article.summary is None
    assert article.author is None


def test_categories_and_keywords_default_to_empty_list():
    article = _make()
    assert article.categories == []
    assert article.keywords == []


def test_categories_and_keywords_are_cleaned():
    article = _make(
        categories=["  SEO  ", "", "SEO", "GEO", "CMS SEO"],
        keywords=["YouTube SEO", "  ", "YouTube SEO", "Shopify SEO", "Backlinks"],
    )
    assert article.categories == ["SEO", "GEO", "CMS SEO"]
    assert article.keywords == ["YouTube SEO", "Shopify SEO", "Backlinks"]


def test_collected_at_defaults_to_now():
    before = datetime.now(timezone.utc)
    article = _make()
    after = datetime.now(timezone.utc)
    assert before <= article.collected_at <= after


def test_missing_required_field_raises():
    with pytest.raises(ValidationError):
        Article(url="https://example.com/a", source="Feed")


def test_invalid_url_raises():
    with pytest.raises(ValidationError):
        _make(url="not-a-url")


def test_blank_title_raises():
    with pytest.raises(ValidationError):
        _make(title="   ")


def test_blank_source_raises():
    with pytest.raises(ValidationError):
        _make(source="")


def test_title_and_source_are_stripped():
    article = _make(title="  Padded Title  ", source="  Padded Source  ")
    assert article.title == "Padded Title"
    assert article.source == "Padded Source"


def test_blank_summary_and_author_normalize_to_none():
    article = _make(summary="   ", author="")
    assert article.summary is None
    assert article.author is None


def test_article_is_immutable():
    article = _make()
    with pytest.raises(ValidationError):
        article.title = "Changed"


def test_is_quality_candidate_true_with_summary_and_category():
    article = _make(summary="A useful summary.", categories=["SEO"])
    assert article.is_quality_candidate is True


def test_is_quality_candidate_true_with_summary_and_keyword_only():
    article = _make(summary="A useful summary.", keywords=["Backlinks"])
    assert article.is_quality_candidate is True


def test_is_quality_candidate_false_without_summary():
    article = _make(categories=["SEO"], keywords=["Backlinks"])
    assert article.is_quality_candidate is False


def test_is_quality_candidate_false_without_categories_or_keywords():
    article = _make(summary="A useful summary.")
    assert article.is_quality_candidate is False
