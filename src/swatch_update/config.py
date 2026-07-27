"""Configuration loading for local, manually triggered runs."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_API_VERSION = "2026-07"


class ConfigurationError(ValueError):
    """Raised when required local configuration is missing or unsafe."""


@dataclass(frozen=True)
class Settings:
    """Validated settings required to authenticate and call Shopify."""

    shop_domain: str
    api_version: str
    client_id: str | None
    client_secret: str | None
    legacy_admin_access_token: str | None
    json_logs: bool

    @property
    def graphql_endpoint(self) -> str:
        """Return the current Admin GraphQL endpoint for the configured store."""
        return f"https://{self.shop_domain}/admin/api/{self.api_version}/graphql.json"

    @property
    def oauth_token_endpoint(self) -> str:
        """Return Shopify's client-credentials token endpoint for the configured store."""
        return f"https://{self.shop_domain}/admin/oauth/access_token"

    @property
    def uses_client_credentials(self) -> bool:
        """Whether the current app uses the Dev Dashboard authentication flow."""
        return bool(self.client_id and self.client_secret)


def _truthy(value: str | None) -> bool:
    return (value or "").strip().casefold() in {"1", "true", "yes", "on"}


def _normalize_shop_domain(raw_value: str | None) -> str:
    if not raw_value or not raw_value.strip():
        raise ConfigurationError("SHOPIFY_SHOP_DOMAIN is required.")
    domain = raw_value.strip().removeprefix("https://").removeprefix("http://").rstrip("/")
    if not domain.endswith(".myshopify.com"):
        raise ConfigurationError(
            "SHOPIFY_SHOP_DOMAIN must be the permanent myshopify.com domain, "
            "for example: your-store.myshopify.com."
        )
    return domain


def load_settings(env_file: Path | None = None) -> Settings:
    """Load settings from a local .env file and environment variables.

    Environment variables override values in .env. New Dev Dashboard apps should
    use the client-credentials pair. The legacy token fallback exists only for
    already-created admin custom apps.
    """
    if env_file is None:
        env_file = Path.cwd() / ".env"
    load_dotenv(env_file, override=False)

    shop_domain = _normalize_shop_domain(os.getenv("SHOPIFY_SHOP_DOMAIN"))
    api_version = (os.getenv("SHOPIFY_API_VERSION") or DEFAULT_API_VERSION).strip()
    client_id = (os.getenv("SHOPIFY_CLIENT_ID") or "").strip() or None
    client_secret = (os.getenv("SHOPIFY_CLIENT_SECRET") or "").strip() or None
    legacy_token = (os.getenv("SHOPIFY_ADMIN_ACCESS_TOKEN") or "").strip() or None

    if bool(client_id) != bool(client_secret):
        raise ConfigurationError(
            "SHOPIFY_CLIENT_ID and SHOPIFY_CLIENT_SECRET must be set together."
        )
    if not (client_id and client_secret) and not legacy_token:
        raise ConfigurationError(
            "Provide SHOPIFY_CLIENT_ID and SHOPIFY_CLIENT_SECRET for a new Dev Dashboard app, "
            "or SHOPIFY_ADMIN_ACCESS_TOKEN only for a legacy admin-created app."
        )

    return Settings(
        shop_domain=shop_domain,
        api_version=api_version,
        client_id=client_id,
        client_secret=client_secret,
        legacy_admin_access_token=legacy_token,
        json_logs=_truthy(os.getenv("SWATCH_LINKER_JSON_LOGS")),
    )
