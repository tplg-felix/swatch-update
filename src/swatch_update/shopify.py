"""Small Shopify Admin GraphQL client for explicit Color & pattern linking."""

from __future__ import annotations

import json
import time
from typing import Any

import requests

from .config import Settings

TARGET_METAOBJECT_TYPE = "shopify--color-pattern"
TARGET_METAFIELD_NAMESPACE = "shopify"
TARGET_METAFIELD_KEY = "color-pattern"
REQUIRED_SCOPES = {"read_products", "write_products", "read_metaobjects"}

PRODUCT_BY_HANDLE_QUERY = """
query ProductByHandle($handle: String!) {
  productByIdentifier(identifier: {handle: $handle}) {
    id
    handle
    title
    options {
      id
      name
      linkedMetafield { namespace key }
      optionValues {
        id
        name
        linkedMetafieldValue
      }
    }
  }
}
"""

METAOBJECT_BY_HANDLE_QUERY = """
query MetaobjectByHandle($type: String!, $handle: String!) {
  metaobjectByHandle(handle: {type: $type, handle: $handle}) {
    id
    handle
    displayName
    type
  }
}
"""

UPDATE_OPTION_VALUES_MUTATION = """
mutation LinkColorOptionValues(
  $productId: ID!,
  $option: OptionUpdateInput!,
  $values: [OptionValueUpdateInput!]
) {
  productOptionUpdate(
    productId: $productId,
    option: $option,
    optionValuesToUpdate: $values
  ) {
    userErrors { field message code }
    product {
      id
      handle
      options {
        id
        name
        linkedMetafield { namespace key }
        optionValues { id name linkedMetafieldValue }
      }
    }
  }
}
"""


class ShopifyApiError(RuntimeError):
    """Raised when Shopify rejects, rate-limits, or cannot process an API request."""


class ShopifyClient:
    """Use a Dev Dashboard client-credentials pair or a legacy static token."""

    def __init__(self, settings: Settings, session: requests.Session | None = None) -> None:
        self.settings = settings
        self.session = session or requests.Session()
        self._access_token: str | None = settings.legacy_admin_access_token
        self._token_expires_at = float("inf") if self._access_token else 0.0
        self._metaobject_cache: dict[str, dict[str, Any] | None] = {}

    def _request_access_token(self) -> str:
        """Exchange Dev Dashboard client credentials for a short-lived Admin API token."""
        if not self.settings.uses_client_credentials:
            if self._access_token:
                return self._access_token
            raise ShopifyApiError("No usable Shopify credentials are configured.")

        response = self.session.post(
            self.settings.oauth_token_endpoint,
            data={
                "grant_type": "client_credentials",
                "client_id": self.settings.client_id,
                "client_secret": self.settings.client_secret,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            timeout=30,
        )
        try:
            payload = response.json()
        except ValueError as exc:
            raise ShopifyApiError(
                "Token request returned non-JSON HTTP "
                f"{response.status_code}: {response.text[:500]}"
            ) from exc
        if response.status_code >= 400:
            raise ShopifyApiError(
                f"Token request failed with HTTP {response.status_code}: "
                f"{json.dumps(payload, ensure_ascii=False)}"
            )

        token = payload.get("access_token")
        if not token:
            raise ShopifyApiError(
                "Token response did not contain access_token: "
                f"{json.dumps(payload, ensure_ascii=False)}"
            )
        granted_scopes = {
            scope.strip() for scope in (payload.get("scope") or "").split(",") if scope
        }
        missing_scopes = REQUIRED_SCOPES.difference(granted_scopes)
        if missing_scopes:
            raise ShopifyApiError(
                "The custom app token is missing required scope(s): "
                + ", ".join(sorted(missing_scopes))
                + ". Update the app version and reinstall the app before running again."
            )

        expires_in = int(payload.get("expires_in") or 0)
        # Refresh one minute early. Shopify documents client-credential tokens as 24-hour tokens.
        self._access_token = token
        self._token_expires_at = time.time() + max(60, expires_in - 60)
        return token

    def _get_access_token(self) -> str:
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token
        return self._request_access_token()

    def graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        """Call Shopify GraphQL with limited retry support for transient throttling."""
        last_error: ShopifyApiError | None = None
        for attempt in range(1, 4):
            token = self._get_access_token()
            response = self.session.post(
                self.settings.graphql_endpoint,
                json={"query": query, "variables": variables},
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "X-Shopify-Access-Token": token,
                },
                timeout=45,
            )
            try:
                payload = response.json()
            except ValueError as exc:
                raise ShopifyApiError(
                    f"GraphQL returned non-JSON HTTP {response.status_code}: {response.text[:500]}"
                ) from exc

            if (
                response.status_code == 401
                and self.settings.uses_client_credentials
                and attempt == 1
            ):
                self._access_token = None
                self._token_expires_at = 0.0
                continue
            if response.status_code == 429:
                wait_seconds = min(10.0, float(response.headers.get("Retry-After", attempt)))
                last_error = ShopifyApiError("Shopify rate-limited the request.")
                time.sleep(wait_seconds)
                continue
            if response.status_code >= 400:
                raise ShopifyApiError(
                    f"GraphQL HTTP {response.status_code}: "
                    f"{json.dumps(payload, ensure_ascii=False)}"
                )
            if payload.get("errors"):
                raise ShopifyApiError(
                    "GraphQL top-level error: "
                    + json.dumps(payload["errors"], ensure_ascii=False)
                )
            return payload.get("data") or {}

        raise last_error or ShopifyApiError("Shopify request failed after retry attempts.")

    def get_product_by_handle(self, handle: str) -> dict[str, Any] | None:
        """Retrieve a product, its options, and option-value identifiers."""
        data = self.graphql(PRODUCT_BY_HANDLE_QUERY, {"handle": handle})
        return data.get("productByIdentifier")

    def get_metaobject_by_handle(self, handle: str) -> dict[str, Any] | None:
        """Retrieve and cache one Color & pattern metaobject by its unique handle."""
        if handle not in self._metaobject_cache:
            data = self.graphql(
                METAOBJECT_BY_HANDLE_QUERY,
                {"type": TARGET_METAOBJECT_TYPE, "handle": handle},
            )
            self._metaobject_cache[handle] = data.get("metaobjectByHandle")
        return self._metaobject_cache[handle]

    def update_option_values(
        self,
        product_id: str,
        option: dict[str, Any],
        values: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        """Link one or more existing values to Color & pattern metaobjects.

        An unlinked Color option is linked to ``shopify.color-pattern`` as part
        of the same update. A different existing linked metafield is never
        overridden; callers must check and stop before this method is called.
        """
        option_input: dict[str, Any] = {"id": option["id"]}
        if not option.get("linkedMetafield"):
            option_input["linkedMetafield"] = {
                "namespace": TARGET_METAFIELD_NAMESPACE,
                "key": TARGET_METAFIELD_KEY,
            }
        data = self.graphql(
            UPDATE_OPTION_VALUES_MUTATION,
            {"productId": product_id, "option": option_input, "values": values},
        )
        payload = data.get("productOptionUpdate") or {}
        user_errors = payload.get("userErrors") or []
        if user_errors:
            raise ShopifyApiError(
                "Shopify userErrors: " + json.dumps(user_errors, ensure_ascii=False)
            )
        return (payload.get("product") or {}).get("options") or []
