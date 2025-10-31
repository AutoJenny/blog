"""Newsletter configuration.

Holds adapter selection and shared defaults. Keep this file small; if it nears
400–500 lines, split constants, adapters, and helpers into dedicated modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


AdapterName = Literal["mailchimp", "ses", "preview"]


@dataclass(frozen=True)
class UTMDefaults:
    utm_source: str = "newsletter"
    utm_medium: str = "email"
    utm_campaign_prefix: str = "week_"  # caller adds ISO week, e.g., week_2025W44


@dataclass(frozen=True)
class NewsletterConfig:
    adapter: AdapterName = "preview"
    utm: UTMDefaults = UTMDefaults()


def get_config() -> NewsletterConfig:
    """Return runtime configuration.

    In future this may read from environment or settings. Kept simple for now.
    """
    return NewsletterConfig()




