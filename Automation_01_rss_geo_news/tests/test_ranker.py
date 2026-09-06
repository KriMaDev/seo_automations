from datetime import datetime, timezone

from app.models import ScoredArticle
from app.processing.ranker import rank_articles


def _scored(**overrides):
    fields = {
        "title": "Example Title",
        "url": "https://example.com/article",
        "source": "Example Feed",
        "relevance_score": 0,
    }
    fields.update(overrides)
    return ScoredArticle(**fields)


def test_rank_articles_sorts_by_relevance_score_descending():
    low = _scored(url="https://example.com/a", relevance_score=1)
    high = _scored(url="https://example.com/b", relevance_score=5)
    mid = _scored(url="https://example.com/c", relevance_score=3)

    ranked = rank_articles([low, high, mid])

    assert [str(a.url) for a in ranked] == [
        "https://example.com/b",
        "https://example.com/c",
        "https://example.com/a",
    ]


def test_rank_articles_tie_breaks_by_published_at_descending():
    older = _scored(
        url="https://example.com/old",
        relevance_score=2,
        published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    newer = _scored(
        url="https://example.com/new",
        relevance_score=2,
        published_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
    )

    ranked = rank_articles([older, newer])

    assert [str(a.url) for a in ranked] == ["https://example.com/new", "https://example.com/old"]


def test_rank_articles_places_undated_articles_last_within_a_tie():
    dated = _scored(
        url="https://example.com/dated",
        relevance_score=2,
        published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    undated = _scored(url="https://example.com/undated", relevance_score=2, published_at=None)

    ranked = rank_articles([undated, dated])

    assert [str(a.url) for a in ranked] == [
        "https://example.com/dated",
        "https://example.com/undated",
    ]


def test_rank_articles_handles_empty_list():
    assert rank_articles([]) == []


def test_rank_articles_does_not_mutate_input_order():
    a = _scored(url="https://example.com/a", relevance_score=1)
    b = _scored(url="https://example.com/b", relevance_score=5)
    original = [a, b]

    rank_articles(original)

    assert original == [a, b]
