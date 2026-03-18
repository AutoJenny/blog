"""Base source adapter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta


class SourceAdapter(ABC):
    """Abstract base for all source adapters.
    
    Each adapter handles fetching and normalizing content from a specific source type
    (RSS feeds, APIs, HTML pages). Keeps adapters small and focused.
    """
    
    def __init__(self, source_name: str, rate_limit_minutes: int = 60):
        """Initialize adapter with source name and rate limit."""
        self.source_name = source_name
        self.rate_limit_minutes = rate_limit_minutes
        self._last_fetch: Optional[datetime] = None
    
    @abstractmethod
    def fetch(self) -> List[Dict[str, Any]]:
        """Fetch raw items from source. Returns list of dicts with source-specific fields."""
        pass
    
    @abstractmethod
    def normalize(self, raw_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert raw item to common normalized shape.
        
        Returns dict with keys:
        - source_name: str
        - title: str
        - url: str
        - published_at: datetime | None
        - event_date: datetime | None
        - location: str | None
        - category: str (weather|event|community|news|other)
        - raw_data: dict (original fields for reference)
        """
        pass
    
    def rate_limit_check(self) -> bool:
        """Check if enough time has passed since last fetch."""
        if self._last_fetch is None:
            return True
        elapsed = datetime.now() - self._last_fetch
        return elapsed.total_seconds() >= (self.rate_limit_minutes * 60)
    
    def mark_fetched(self) -> None:
        """Record that fetch just completed."""
        self._last_fetch = datetime.now()
    
    def fetch_and_normalize(self) -> List[Dict[str, Any]]:
        """Fetch raw items and normalize all to common shape."""
        if not self.rate_limit_check():
            return []
        raw_items = self.fetch()
        self.mark_fetched()
        normalized = []
        for item in raw_items:
            norm = self.normalize(item)
            if norm:
                normalized.append(norm)
        return normalized

