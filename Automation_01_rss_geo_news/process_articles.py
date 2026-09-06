"""Entrypoint for re-scoring already-collected articles only.

Use this instead of main.py when you've tuned config/topics.yaml (or
config/sources.yaml/collection.yaml) and want to re-score existing
data/raw_articles/ without running a fresh collection.
"""

from app.processing.pipeline import run

if __name__ == "__main__":
    run()
