"""Central configuration for the SEO/GEO automation project.

Loads environment variables and defines the shared paths used across the
collection pipeline (data directories, config files, logging).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
RAW_ARTICLES_DIR = DATA_DIR / "raw_articles"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = DATA_DIR / "outputs"
LOGS_DIR = PROJECT_ROOT / "logs"

SOURCES_FILE = CONFIG_DIR / "sources.yaml"


@dataclass(frozen=True)
class Settings:
    """Application-wide settings, populated from environment variables."""

    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: Path = LOGS_DIR / "automation.log"

    project_root: Path = PROJECT_ROOT
    config_dir: Path = CONFIG_DIR
    data_dir: Path = DATA_DIR
    raw_articles_dir: Path = RAW_ARTICLES_DIR
    processed_dir: Path = PROCESSED_DIR
    outputs_dir: Path = OUTPUTS_DIR
    logs_dir: Path = LOGS_DIR
    sources_file: Path = SOURCES_FILE


settings = Settings()