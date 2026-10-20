# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Collects SEO/GEO news from RSS feeds, scores each article against configurable topics, and ranks the result — source material for a future (not yet built) stage that writes video scripts. Runs entirely locally; no paid APIs.

## Commands

All commands assume the working directory is this folder and call the venv's Python directly (no activation needed):

```
.venv\Scripts\python.exe main.py                               # full pipeline: collect, then score + rank
.venv\Scripts\python.exe process_articles.py                    # re-score already-collected articles only (no fetch)
.venv\Scripts\python.exe run_tests.py                            # full test suite (thin pytest wrapper, forwards args)
.venv\Scripts\python.exe run_tests.py -k test_name                # a single test by name
.venv\Scripts\python.exe run_tests.py tests/test_topic_matcher.py -v   # one file, verbose
```

If `.venv` doesn't exist yet: `python -m venv .venv && .venv\Scripts\python.exe -m pip install -r requirements.txt`.

## Architecture

**Pipeline, three stages, three data folders, each with a different overwrite rule:**

1. **Collect** (`app/collectors/rss_collector.py` → `app/storage/writer.py`) reads `config/sources.yaml`, fetches each feed, filters to `config/collection.yaml`'s `collection_window_days`, and writes one JSON file per `Article` to `data/raw_articles/YYYY-MM-DD/<sha256(url)>.json`. Dedup (`app/storage/dedup.py`) checks the filesystem directly (globs for the hash across all date folders) rather than keeping a separate index — the saved files are the source of truth. **Raw storage never overwrites**: an article whose URL already exists anywhere is skipped.
2. **Process** (`app/storage/reader.py` → `app/processing/topic_matcher.py` → `app/processing/writer.py`) reads *every* file back from `data/raw_articles/` (the full accumulated history, not just one day), scores each against `config/topics.yaml` into a `ScoredArticle`, and writes to `data/processed/YYYY-MM-DD/<same hash>.json`. **Processed storage always overwrites** — scoring is a pure function of raw data + `topics.yaml`, so re-running after editing topics is expected and safe.
3. **Rank** (`app/processing/ranker.py` → `write_ranked_output` in `app/processing/writer.py`) sorts all scored articles by `relevance_score` (ties broken by `published_at`) and writes a single current snapshot to `data/outputs/ranked_articles.json` + `.md` — not date-partitioned, always overwritten, since it's "the current best view," not a log.

Both stages are orchestrated by `app/pipeline.py` (collect) and `app/processing/pipeline.py` (process), each logging one end-of-run summary line via a shared `LogOutcomeCounter` (`app/utils.py`) that counts warnings/errors emitted during the run.

**Config over code, consistently.** The three YAML files (`sources.yaml`, `collection.yaml`, `topics.yaml`) are each loaded by a same-shaped `load_X()` function in `app/config.py` (default path from `settings`, override via explicit path for tests). Adding/removing a feed, changing the recency window, or retuning topic keywords is a YAML edit — never a code change. Follow this pattern for new tunables rather than hardcoding.

**Models mirror the pipeline stages.** `Article` (title/url/source required, everything else — categories, keywords, summary, published_at — optional and permissive) is the raw-layer schema; rejecting on missing metadata at collection time would silently lose data a later stage might still use. `ScoredArticle` subclasses it, adding `matched_topics`/`relevance_score`/`is_relevant`. Both are frozen (immutable) Pydantic models.

**Topic matching is whole-word, not substring.** Short topic keywords (SEO, GEO, AEO, SMO) false-positive inside unrelated words under plain substring search (`"GEO"` inside `"geography"`) — `app/processing/topic_matcher.py` matches on `\b`-bounded regex for this reason. Preserve that if touching matching logic.

**Logging:** handlers attach to the *root* logger (not `app`) so genuine third-party warnings/errors are captured too; only the `app` logger's own level is raised to `settings.log_level` (default `INFO`), so third-party libraries keep Python's default `WARNING` threshold and stay quiet unless something real goes wrong. Per-article scoring detail logs at `DEBUG` — set `LOG_LEVEL=DEBUG` to see it.

**Feeds are unreliable; code accordingly.** A feed/entry parse failure, or the reader hitting a malformed file, logs a warning and is skipped — never raises past that boundary. OpenAI's feed returns its entire historical archive on every fetch (not just new items), which is what `collection_window_days` exists to bound.

## Known follow-ups

- **Revisit the README's data/legal note once full-article-body fetching lands (planned, Sprint 14+, not yet built).** The README currently says this project "never fetches or republishes full article text" and "nothing here redistributes" the collected content — true today only because `data/` stores metadata/excerpts and is fully gitignored. Storing full article text changes that framing even if it stays gitignored and local-only (copyright attaches to storage, not just publication) — update the README's wording at that point, not just the architecture docs.
- **Sprint 14+ (full-article-body fetching) design, agreed but not yet built:** fetch full text only for the top-ranked articles (a configurable count, not hardcoded, not the full raw set); check `robots.txt` before fetching each URL and skip+log anything disallowed; use a real identifying User-Agent and a modest delay between requests; never retry around a block — treat it like any other failure (log, skip, move on). Full-body fetching is intended to land *before* any LLM integration (an LLM writing scripts needs real article substance, not a short excerpt) — don't add a speculative LLM-based re-ranking step in the meantime; keyword-based ranking is already working well on real data.
- **Source diversity in ranking is currently unaddressed.** The top of `ranked_articles.md` tends to be dominated by one source (the one that both publishes the most and has the richest per-article metadata), which inflates its matches without necessarily meaning it's more important. A per-source cap on the top-N (discussed, not built) would help both content variety and avoid concentrating full-body fetch requests on one domain.
