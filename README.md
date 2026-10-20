# SEO Automations

A collection of independent local automations, each self-contained in its own `Automation_NN_<slug>/` folder. Every automation has its own virtual environment, dependencies, tests, and README — there's no shared code between them, and no root-level package.

## Automations

| # | Name | What it does |
|---|------|--------------|
| 01 | [`Automation_01_rss_geo_news`](Automation_01_rss_geo_news/) | Collects SEO/GEO news from RSS feeds, scores each article against configurable topics, and ranks the most relevant results — entirely locally, no paid APIs. |

See each automation's own README for setup and usage instructions.

## Repository structure

```
seo_automations/
├── LICENSE
├── README.md               # this file
├── CLAUDE.md                # repo-wide conventions for AI coding agents
└── Automation_01_rss_geo_news/
    ├── README.md             # setup + usage for this automation
    └── CLAUDE.md             # architecture notes for this automation
```

When adding a new automation, create a new `Automation_NN_<slug>/` folder following the same shape as `Automation_01_rss_geo_news/`, rather than introducing shared infrastructure speculatively.

## License

[MIT](LICENSE) — free to use, modify, and distribute. See the `LICENSE` file for the full text.

Each automation's own README lists the specific third-party libraries it depends on and their licenses.
