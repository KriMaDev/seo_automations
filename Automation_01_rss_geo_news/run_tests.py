"""Convenience entrypoint for the test suite: `python run_tests.py`.

Not used by main.py/process_articles.py — the automation itself never
depends on pytest being installed. This is purely for you to verify
the code, kept separate from the actual pipeline on purpose.
"""

import sys

import pytest

if __name__ == "__main__":
    sys.exit(pytest.main(sys.argv[1:]))
