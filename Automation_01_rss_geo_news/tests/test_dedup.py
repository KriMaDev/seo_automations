from app.storage.dedup import find_existing, is_duplicate, url_hash


def test_url_hash_is_stable():
    assert url_hash("https://example.com/a") == url_hash("https://example.com/a")


def test_url_hash_differs_for_different_urls():
    assert url_hash("https://example.com/a") != url_hash("https://example.com/b")


def test_find_existing_returns_none_when_dir_missing(tmp_path):
    missing = tmp_path / "does_not_exist"
    assert find_existing("https://example.com/a", missing) is None


def test_find_existing_returns_none_when_not_saved(tmp_path):
    (tmp_path / "2026-08-04").mkdir()
    assert find_existing("https://example.com/a", tmp_path) is None


def test_find_existing_finds_article_in_any_date_folder(tmp_path):
    url = "https://example.com/a"
    day_dir = tmp_path / "2026-07-20"
    day_dir.mkdir()
    saved_path = day_dir / f"{url_hash(url)}.json"
    saved_path.write_text("{}", encoding="utf-8")

    found = find_existing(url, tmp_path)
    assert found == saved_path


def test_is_duplicate_true_when_saved(tmp_path):
    url = "https://example.com/a"
    day_dir = tmp_path / "2026-07-20"
    day_dir.mkdir()
    (day_dir / f"{url_hash(url)}.json").write_text("{}", encoding="utf-8")

    assert is_duplicate(url, tmp_path) is True


def test_is_duplicate_false_when_not_saved(tmp_path):
    assert is_duplicate("https://example.com/a", tmp_path) is False
