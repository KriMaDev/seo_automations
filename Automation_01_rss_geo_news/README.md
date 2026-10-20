# Automation 01 — RSS/GEO News Collector & Ranker

This automation collects the latest SEO and GEO (Generative Engine
Optimization) news from a configured list of RSS feeds (Search Engine
Journal, Search Engine Land, Google Search Central, Ahrefs Blog, Moz
Blog, Semrush Blog, OpenAI News), scores each article against a
configurable list of topics, and produces a ranked list of the most
relevant recent articles — ready to be the source material for a
later stage (not built yet) that writes educational video scripts.

Nothing here calls any paid API and nothing leaves your machine except
the RSS feed requests and the article pages themselves.

## What you need before starting

- **Python 3.10 or newer** (developed and tested on 3.13). Check your
  version with:
  ```
  python --version
  ```
  If that command isn't found, install Python from
  [python.org](https://www.python.org/downloads/) — on Windows, tick
  "Add python.exe to PATH" during setup.
- **Git**, to download the project. Check with:
  ```
  git --version
  ```
  If you don't want to install Git, you can also download the project
  as a ZIP from its GitHub page (green "Code" button → "Download ZIP")
  and skip the `git clone` step below.

## 1. Download the project

```
git clone https://github.com/KriMaDev/seo_automations.git
cd seo_automations/Automation_01_rss_geo_news
```

Every command below assumes you're inside this `Automation_01_rss_geo_news`
folder.

## 2. Set up an isolated environment

This creates a private, self-contained copy of Python just for this
automation, so its dependencies never clash with anything else on your
machine.

**Windows (PowerShell):**
```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**macOS/Linux:**
```
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

That last command reads `requirements.txt` and installs everything the
project needs (feed parsing, data validation, YAML support, the test
runner).

> **Windows note:** you don't need to "activate" the virtual
> environment for any of this — calling `.venv\Scripts\python.exe`
> directly, as shown above and below, always uses the right, isolated
> Python. If you'd rather activate it once per terminal session and
> then just type `python`, run `.venv\Scripts\Activate.ps1` first; if
> PowerShell blocks that with an execution-policy error, skip it and
> use the direct `.venv\Scripts\python.exe` form instead — it always
> works.

## 3. The three commands you'll use

Everything you'll ever run day-to-day is one of these three. On
macOS/Linux, replace `.venv\Scripts\python.exe` with `.venv/bin/python`.

**Command 1 — run the whole pipeline:**
```
.venv\Scripts\python.exe main.py
```
Collects the latest articles from every feed, then scores and ranks
them. This is the one you'll use almost all the time — a normal day's
run. Safe to run repeatedly: already-collected articles are never
duplicated.

**Command 2 — re-score without collecting anything new:**
```
.venv\Scripts\python.exe process_articles.py
```
Use this after editing `config/topics.yaml` (see step 5) when you want
updated rankings without waiting on a fresh collection. Re-reads
everything already collected and rewrites the scores/ranking.

**Command 3 — run the test suite:**
```
.venv\Scripts\python.exe run_tests.py
```
Checks that everything still works. Optional, but worth running after
you change any config file or code — tells you immediately if
something broke.

## 4. Where to find the results

Open **`data/outputs/ranked_articles.md`** — this is the one file
meant to just be opened and read. It lists every scored article,
highest-relevance first, e.g.:

```
1. [3] Getting Your Product Into ChatGPT Isn't The Hard Part — SEO, GEO
   https://www.searchenginejournal.com/...
```

The same ranked list also exists as `data/outputs/ranked_articles.json`
(same information, machine-readable). Behind those, every article
passes through two intermediate stages if you want to inspect them:

- `data/raw_articles/YYYY-MM-DD/*.json` — exactly what was collected,
  one file per article, one folder per day
- `data/processed/YYYY-MM-DD/*.json` — the same articles with scoring
  added (`matched_topics`, `relevance_score`, `is_relevant`)

A full run log (everything printed to the terminal, plus a bit more
detail, including per-feed/per-article activity) is also saved to
`logs/automation.log`.

## 5. Customize what it collects and how it scores

Nothing here requires touching any code — everything tunable lives in
plain text files under `config/`:

- **`config/sources.yaml`** — the list of RSS feeds. Add a new one by
  copying the `- name: ... / url: ...` pattern, or delete an entry to
  stop collecting from it.
- **`config/collection.yaml`** — `collection_window_days` controls how
  far back to look. Currently set to `7`. Once you're running this
  daily going forward, consider lowering it to `1` so each run only
  picks up what's genuinely new since the day before.
- **`config/topics.yaml`** — the topics articles are scored against
  (SEO, GEO, Shopify SEO, YouTube SEO, Video SEO, Social SEO), each
  with its own keyword list. Add, remove, or edit a topic's keywords
  freely — matching is case-insensitive and whole-word (so "GEO"
  matches "GEO-focused" but not "geography"). After editing this file,
  run Command 2 (above) to see the new rankings.

## Project layout, briefly

```
Automation_01_rss_geo_news/
├── main.py                   # Command 1: collect + score + rank, all in one
├── process_articles.py       # Command 2: re-score already-collected articles only
├── run_tests.py              # Command 3: run the test suite
├── config/
│   ├── sources.yaml           # which RSS feeds to collect from
│   ├── collection.yaml        # how far back to collect
│   └── topics.yaml            # topics + keywords used for scoring
├── data/
│   ├── raw_articles/           # what was collected, one file per article
│   ├── processed/              # the same articles, with scores added
│   └── outputs/                 # ranked_articles.md / .json — the final view
├── logs/automation.log       # run history / debugging
├── app/                      # the actual source code
└── tests/                    # automated tests
```

## What this automation does *not* do (yet)

This is deliberately scoped to collecting, scoring, and ranking — not
generating the videos themselves. It does not currently:
- Fetch full article text (only the title and a short excerpt are
  available from RSS — a future stage will fetch full text for just
  the top-ranked articles, not everything collected)
- Use an LLM for scoring (relevance is judged by keyword matching
  today — deterministic and free, with known limits on nuance)
- Generate any video script text
- Run automatically on a schedule (you need to run `main.py` yourself
  for now; scheduling it, e.g. via Windows Task Scheduler, is a future
  step)

## Troubleshooting

- **`ModuleNotFoundError: No module named 'feedparser'` (or similar)**
  — you ran a script with your system Python instead of the project's
  own copy. Use `.venv\Scripts\python.exe main.py` (Windows) or
  `.venv/bin/python main.py` (macOS/Linux) instead — same for the
  other two commands.
- **A feed shows a `WARNING` in the log** — this is normal and
  expected sometimes (feeds occasionally have minor formatting quirks
  or hiccups). The automation logs it and keeps going; it only becomes
  a problem if a feed shows `0 articles` on every run.
- **A topic in `config/topics.yaml` always shows `0` matches** — check
  the "Topic breakdown" line in the log after running Command 2. If a
  topic never matches anything, its keyword list may need broadening.

## A note on the collected data

This project only stores the article metadata that feeds themselves
publish (title, a short excerpt, link, publish date) — it never
fetches or republishes full article text, and `data/raw_articles/`,
`data/processed/`, and `data/outputs/` are all excluded from version
control (see `.gitignore`). The code is open source; the news content
it collects belongs to its original publishers, and nothing here
redistributes it.

## License

[MIT](../LICENSE) — same license as the rest of the repository.

### Third-party libraries

This automation depends on the following open-source packages (see
`requirements.txt` for exact versions), each under a permissive
license with no conflicts with the MIT license above:

| Package | License |
|---|---|
| [pydantic](https://github.com/pydantic/pydantic) | MIT |
| [pytest](https://github.com/pytest-dev/pytest) | MIT |
| [PyYAML](https://pyyaml.org/) | MIT |
| [feedparser](https://github.com/kurtmckee/feedparser) | BSD-2-Clause |
| [feedparser-sgmllib](https://pypi.org/project/feedparser-sgmllib/) | PSF-2.0 |

Developed with the assistance of [Claude Code](https://claude.com/claude-code) (Anthropic).
