"""Entrypoint for the full daily pipeline: collect, then score/rank.

For re-scoring already-collected articles only (e.g. after tuning
config/topics.yaml), without a fresh collection, use
process_articles.py instead.
"""

from app.pipeline import run as collect
from app.processing.pipeline import run as process

if __name__ == "__main__":
    collect()
    process()
