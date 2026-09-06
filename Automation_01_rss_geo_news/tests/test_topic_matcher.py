import pytest
from pydantic import ValidationError

from app.models import Article, Topic
from app.processing.topic_matcher import score_article, score_articles


def _article(**overrides):
    fields = {
        "title": "Example Title",
        "url": "https://example.com/article",
        "source": "Example Feed",
    }
    fields.update(overrides)
    return Article(**fields)


SEO_TOPIC = Topic(name="SEO", keywords=["SEO", "organic search", "backlinks"])
GEO_TOPIC = Topic(name="GEO", keywords=["GEO", "AI overviews"])
SHOPIFY_TOPIC = Topic(name="Shopify SEO", keywords=["Shopify"])
TOPICS = [SEO_TOPIC, GEO_TOPIC, SHOPIFY_TOPIC]


def test_matches_keyword_in_title():
    article = _article(title="A Guide to Backlinks")
    scored = score_article(article, TOPICS)
    assert scored.matched_topics == ["SEO"]
    assert scored.is_relevant is True


def test_matches_keyword_in_summary():
    article = _article(summary="This covers organic search trends.")
    scored = score_article(article, TOPICS)
    assert scored.matched_topics == ["SEO"]


def test_matches_keyword_in_categories():
    article = _article(categories=["Shopify"])
    scored = score_article(article, TOPICS)
    assert scored.matched_topics == ["Shopify SEO"]


def test_matches_keyword_in_keywords_field():
    article = _article(keywords=["backlinks"])
    scored = score_article(article, TOPICS)
    assert scored.matched_topics == ["SEO"]


def test_matching_is_case_insensitive():
    article = _article(title="how to do seo right")
    scored = score_article(article, TOPICS)
    assert scored.matched_topics == ["SEO"]


def test_matches_multiple_topics():
    article = _article(title="SEO and GEO strategy for Shopify stores")
    scored = score_article(article, TOPICS)
    assert set(scored.matched_topics) == {"SEO", "GEO", "Shopify SEO"}


def test_no_match_returns_empty_and_not_relevant():
    article = _article(title="A story about cooking pasta")
    scored = score_article(article, TOPICS)
    assert scored.matched_topics == []
    assert scored.relevance_score == 0
    assert scored.is_relevant is False


def test_relevance_score_counts_distinct_keywords_not_topics():
    article = _article(title="SEO and backlinks and organic search all covered")
    scored = score_article(article, TOPICS)
    assert scored.matched_topics == ["SEO"]
    assert scored.relevance_score == 3  # seo, backlinks, organic search


def test_relevance_score_does_not_double_count_repeated_keyword():
    article = _article(title="SEO SEO SEO everywhere")
    scored = score_article(article, TOPICS)
    assert scored.relevance_score == 1


def test_html_tags_in_summary_are_stripped_before_matching():
    article = _article(
        summary='<p>Covers <strong>organic search</strong> trends. '
        '<a href="https://example.com/x">Read more</a></p>'
    )
    scored = score_article(article, TOPICS)
    assert scored.matched_topics == ["SEO"]


def test_original_article_fields_are_preserved():
    article = _article(
        title="A Title",
        summary="A summary.",
        categories=["Cat"],
        author="Jane Doe",
    )
    scored = score_article(article, TOPICS)
    assert scored.title == "A Title"
    assert scored.summary == "A summary."
    assert scored.categories == ["Cat"]
    assert scored.author == "Jane Doe"
    assert str(scored.url) == "https://example.com/article"


def test_scored_article_is_immutable():
    scored = score_article(_article(), TOPICS)
    with pytest.raises(ValidationError):
        scored.relevance_score = 99


def test_score_articles_scores_a_batch():
    articles = [
        _article(url="https://example.com/a", title="All about SEO"),
        _article(url="https://example.com/b", title="A story about cooking pasta"),
    ]
    scored = score_articles(articles, TOPICS)
    assert len(scored) == 2
    assert scored[0].is_relevant is True
    assert scored[1].is_relevant is False


def test_score_articles_empty_list_returns_empty_list():
    assert score_articles([], TOPICS) == []


def test_no_topics_configured_means_nothing_matches():
    article = _article(title="All about SEO")
    scored = score_article(article, [])
    assert scored.matched_topics == []
    assert scored.is_relevant is False


def test_does_not_match_short_keyword_as_substring_of_unrelated_word():
    # "GEO" must not match inside "geography"/"geological" — a real
    # false positive found and fixed in Sprint 13.
    article = _article(
        title="A Guide to Geography and Geological Surveys",
        summary="This article has nothing to do with search marketing.",
    )
    scored = score_article(article, TOPICS)
    assert scored.matched_topics == []
    assert scored.relevance_score == 0


def test_matches_keyword_attached_to_punctuation():
    # Word-boundary matching should still catch a keyword glued to
    # punctuation, just not glued to other word characters.
    article = _article(title="A GEO-focused content strategy")
    scored = score_article(article, TOPICS)
    assert "GEO" in scored.matched_topics
