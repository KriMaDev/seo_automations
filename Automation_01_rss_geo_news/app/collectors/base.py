"""Base collector interface.

Common interface for all source-specific collectors (RSS now, other
source types later) so the pipeline can treat them interchangeably.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from app.models import Article


class BaseCollector(ABC):
    """A collector gathers Articles from one source type."""

    @abstractmethod
    def collect(self) -> List[Article]:
        """Fetch and parse content into Article objects."""
        raise NotImplementedError
