# Automation 01 — RSS/GEO News Collector

This automation collects the latest SEO and GEO (Generative Engine
Optimization) news from a configured list of RSS feeds (Search Engine
Journal, Search Engine Land, Google Search Central, Ahrefs Blog, Moz
Blog, Semrush Blog, OpenAI News) and saves each new article as its own
JSON file on your computer. It's the first stage of a larger pipeline —
this part only collects and stores; it doesn't summarize, filter, or
write anything yet.

Nothing here calls any paid API and nothing leaves your machine except
the RSS feed requests themselves.

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

## 3. Run it

**Windows:**
```
.venv\Scripts\python.exe main.py
```

**macOS/Linux:**
```
.venv/bin/python main.py
```

You'll see live progress in the terminal as it fetches each feed, and
a one-line summary at the end, e.g.:

```
Run complete: 7 feed(s) processed, 62 article(s) found, 4 written, 58 skipped (duplicate), 0 warning(s), 0 error(s), 12.3s
```

Run it again right away and you'll see most (or all) articles reported
as "skipped (duplicate)" — that's expected. The automation remembers
what it already saved and never saves the same article twice, so it's
always safe to run more than once.

## 4. Where to find the results

Every new article is saved as its own `.json` file under:

```
data/raw_articles/YYYY-MM-DD/
```

(one folder per day, named after the date the article was collected).
Each file looks like this:

```json
{
  "title": "How to measure AI share of voice using Semrush",
  "url": "https://www.semrush.com/blog/...",
  "source": "Semrush Blog",
  "categories": ["SEO"],
  "keywords": [],
  "published_at": "2026-07-31T12:30:09Z",
  "summary": "A short excerpt of the article...",
  "author": "Jane Doe",
  "collected_at": "2026-08-04T14:22:17Z"
}
```

A full run log (everything printed to the terminal, plus a bit more
detail) is also saved to `logs/automation.log`, in case you need to
check what happened after the fact.

## 5. Customize what it collects

Nothing here requires touching any code — everything tunable lives in
plain text files under `config/`:

- **`config/sources.yaml`** — the list of RSS feeds. Add a new one by
  copying the `- name: ... / url: ...` pattern, or delete an entry to
  stop collecting from it.
- **`config/collection.yaml`** — `collection_window_days` controls how
  far back to look. It's currently set to `14` (good for an initial
  run so you get a real batch of articles). Once you're running this
  daily going forward, you can lower it to `1` so each run only picks
  up what's genuinely new since the day before.

## 6. Run the tests (optional, but recommended after any change)

```
.venv\Scripts\python.exe -m pytest
```

This runs the full automated test suite (60+ checks covering article
parsing, deduplication, storage, and configuration loading) and tells
you immediately if something's broken.

## Project layout, briefly

```
Automation_01_rss_geo_news/
├── main.py                  # run this to start a collection
├── config/
│   ├── sources.yaml          # which RSS feeds to collect from
│   └── collection.yaml       # how far back to collect
├── data/raw_articles/        # output: one JSON file per article
├── logs/automation.log       # run history / debugging
├── app/                      # the actual source code
└── tests/                    # automated tests
```

## What this automation does *not* do (yet)

This is deliberately scoped to collection only. It does not currently:
- Judge whether an article is actually relevant/high-quality (every
  structurally valid article gets saved — filtering happens in a
  later stage, not yet built)
- Fetch full article text (only the title and a short excerpt are
  available from RSS — see the project's notes on this for why)
- Run automatically on a schedule (you need to run `main.py` yourself
  for now; scheduling it, e.g. via Windows Task Scheduler, is a future
  step)

## Troubleshooting

- **`ModuleNotFoundError: No module named 'feedparser'` (or similar)**
  — you ran `python main.py` with your system Python instead of the
  project's own copy. Use `.venv\Scripts\python.exe main.py` (Windows)
  or `.venv/bin/python main.py` (macOS/Linux) instead.
- **A feed shows a `WARNING` in the log** — this is normal and
  expected sometimes (feeds occasionally have minor formatting quirks
  or hiccups). The automation logs it and keeps going; it only becomes
  a problem if a feed shows `0 articles` on every run.
