"""
Product caption formatting: policy that price must never appear in preview or publish.
"""
import re


def strip_price_from_caption(text: str) -> str:
    """
    Remove price-like substrings from product caption text.
    Policy: price must never appear in Facebook preview or published product posts.
    Handles £43.99, $43.99, and bare decimal amounts (e.g. 43.99). Collapses
    resulting extra whitespace and trims.
    """
    if not text or not isinstance(text, str):
        return text
    # Currency amounts: £43.99, £ 43.99, $43.99
    out = re.sub(r"£\s*\d+(?:\.\d{1,2})?", "", text)
    out = re.sub(r"\$\s*\d+(?:\.\d{1,2})?", "", out)
    # Bare decimal price (e.g. 43.99) - common in product text
    out = re.sub(r"\b\d+\.\d{2}\b", "", out)
    # Collapse multiple spaces and trim
    out = re.sub(r"\s+", " ", out).strip()
    return out
