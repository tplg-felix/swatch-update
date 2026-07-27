"""Handle normalization used to derive Shopify Color & pattern object handles."""

from __future__ import annotations

import re
import unicodedata


def normalize_metaobject_handle(value: str) -> str:
    """Return a Shopify-style, URL-safe handle for a human-readable label.

    Example: ``Ivy Green / Vintage Ripstop`` becomes
    ``ivy-green-vintage-ripstop``. The generated handle is a candidate key;
    the linker still verifies that an entry with this exact handle exists in
    Shopify before it can make any change.
    """
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    normalized = normalized.casefold().strip()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    return normalized.strip("-")
