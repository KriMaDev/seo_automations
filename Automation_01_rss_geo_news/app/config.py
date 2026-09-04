"""Central configuration for the SEO/GEO automation project.

Defines the shared paths and settings used across the collection
pipeline. `settings` is the only public surface — import it rather than
reaching for path constants elsewhere in this module.

Tests that need an isolated location (e.g. a tmp_path for data or a
config fixture) can build a variant with
`dataclasses.replace(settings, raw_articles_dir=tmp_path, ...)` instead
of hand-rolling a fresh Settings().
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml

from app.models import FeedSource, Topic

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_DIR = _PROJECT_ROOT / "config"
_DATA_DIR = _PROJECT_ROOT / "data"
_LOGS_DIR = _PROJECT_ROOT / "logs"


@dataclass(frozen=True)
class Settings:
    """Application-wide settings. Override via dataclasses.replace(settings, ...)."""

    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    project_root: Path = _PROJECT_ROOT
    config_dir: Path = _CONFIG_DIR
    data_dir: Path = _DATA_DIR
    raw_articles_dir: Path = _DATA_DIR / "raw_articles"
    processed_dir: Path = _DATA_DIR / "processed"
    outputs_dir: Path = _DATA_DIR / "outputs"
    logs_dir: Path = _LOGS_DIR
    log_file: Path = _LOGS_DIR / "automation.log"
    sources_file: Path = _CONFIG_DIR / "sources.yaml"
    collection_settings_file: Path = _CONFIG_DIR / "collection.yaml"
    topics_file: Path = _CONFIG_DIR / "topics.yaml"


settings = Settings()

_DEFAULT_COLLECTION_WINDOW_DAYS = 14


def load_feed_sources(path: Optional[Path] = None) -> List[FeedSource]:
    """Load and validate the configured RSS feed list.

    Reads the `feeds:` list from a YAML file (defaulting to
    settings.sources_file) — add or remove feeds by editing that file,
    no code changes needed. Does not fetch or read the feeds themselves.
    """
    source_path = path or settings.sources_file
    raw = yaml.safe_load(source_path.read_text(encoding="utf-8")) or {}
    return [FeedSource(**feed) for feed in raw.get("feeds", [])]


def load_collection_window_days(path: Optional[Path] = None) -> int:
    """Load how many days back the collector should keep articles from.

    Reads `collection_window_days` from a YAML file (defaulting to
    settings.collection_settings_file) — tune it there, no code changes
    needed (e.g. set to 1 for a steady-state daily run). Falls back to
    a default if the file or key is missing.
    """
    source_path = path or settings.collection_settings_file
    if not source_path.exists():
        return _DEFAULT_COLLECTION_WINDOW_DAYS
    raw = yaml.safe_load(source_path.read_text(encoding="utf-8")) or {}
    return int(raw.get("collection_window_days", _DEFAULT_COLLECTION_WINDOW_DAYS))


def load_topics(path: Optional[Path] = None) -> List[Topic]:
    """Load and validate the configured relevance topics.

    Reads the `topics:` list from a YAML file (defaulting to
    settings.topics_file) — add, remove, or edit a topic's keywords by
    editing that file, no code changes needed.
    """
    source_path = path or settings.topics_file
    raw = yaml.safe_load(source_path.read_text(encoding="utf-8")) or {}
    return [Topic(**topic) for topic in raw.get("topics", [])]
