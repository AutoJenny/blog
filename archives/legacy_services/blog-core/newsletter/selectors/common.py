"""Common helpers for selectors (UTM building, filters, thresholds)."""

from __future__ import annotations

from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl
from typing import Dict


def append_utms(url: str, utms: Dict[str, str]) -> str:
    parsed = urlparse(url)
    q = dict(parse_qsl(parsed.query))
    q.update(utms)
    new_query = urlencode(q)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))




