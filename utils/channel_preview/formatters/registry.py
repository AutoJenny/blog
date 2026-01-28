"""
Formatter registry for channel preview.

Provides `get_formatter(channel)` which returns a formatter instance for
the requested channel. Falls back to the generic formatter when needed.
"""

from typing import Dict

from .facebook import FacebookFormatter
from .generic import GenericFormatter


_FORMATTERS: Dict[str, object] = {
    "facebook": FacebookFormatter(),
    "instagram": GenericFormatter(),
    "x": GenericFormatter(),
    "twitter": GenericFormatter(),
    "tiktok": GenericFormatter(),
    "generic": GenericFormatter(),
}


def get_formatter(channel: str):
    """
    Return formatter instance for the given channel.

    Always returns *some* formatter; unknown channels fall back to generic.
    """
    key = (channel or "facebook").lower()
    if key == "twitter":
        key = "x"
    return _FORMATTERS.get(key, _FORMATTERS["generic"])

