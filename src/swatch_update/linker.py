"""Safe, explicit linkage of imported Color option values to Shopify metaobjects."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import LinkResult, LinkRow
from .shopify import (
    TARGET_METAFIELD_KEY,
    TARGET_METAFIELD_NAMESPACE,
    ShopifyApiError,
    ShopifyClient,
)

RESULT_FIELDNAMES = [
    "source_excel_row",
    "product_handle",
    "option_name",
    "option_value",
    "metaobject_handle",
    "product_id",
    "option_id",
    "option_value_id",
    "metaobject_id",
    "action",
    "status",
    "detail",
]


def _find_option(product: dict[str, Any], option_name: str) -> dict[str, Any] | None:
    exact_matches = [
        option for option in product.get("options", []) if option.get("name") == option_name
    ]
    if len(exact_matches) == 1:
        return exact_matches[0]
    folded_matches = [
        option
        for option in product.get("options", [])
        if (option.get("name") or "").casefold() == option_name.casefold()
    ]
    return folded_matches[0] if len(folded_matches) == 1 else None


def _find_option_value(option: dict[str, Any], name: str) -> dict[str, Any] | None:
    exact_matches = [value for value in option.get("optionValues", []) if value.get("name") == name]
    return exact_matches[0] if len(exact_matches) == 1 else None


def _error_result(row: LinkRow, detail: str, **ids: str) -> LinkResult:
    return LinkResult.from_link_row(row, status="ERROR", detail=detail, **ids)


def link_rows(
    rows: Iterable[LinkRow], client: ShopifyClient, execute: bool = False
) -> list[LinkResult]:
    """Validate or apply all requested links.

    The operation is all-or-nothing for each product option. If any source row
    for a Color option is invalid, no mutation is made for that product option.
    This prevents a partial product update from hiding an incomplete import.
    """
    grouped: dict[tuple[str, str], list[LinkRow]] = defaultdict(list)
    for row in rows:
        grouped[(row.product_handle, row.option_name)].append(row)

    results: list[LinkResult] = []
    for (product_handle, option_name), group_rows in grouped.items():
        try:
            product = client.get_product_by_handle(product_handle)
        except ShopifyApiError as exc:
            results.extend(
                _error_result(row, str(exc))
                for row in group_rows
            )
            continue

        if not product:
            results.extend(
                _error_result(row, "Product not found after the Matrixify import.")
                for row in group_rows
            )
            continue

        option = _find_option(product, option_name)
        if not option:
            available_options = ", ".join(
                option_item.get("name") or "" for option_item in product.get("options", [])
            )
            results.extend(
                _error_result(
                    row,
                    f"Option {option_name!r} not found. Available options: {available_options!r}",
                    product_id=product["id"],
                )
                for row in group_rows
            )
            continue

        current_link = option.get("linkedMetafield")
        if current_link and (
            current_link.get("namespace"),
            current_link.get("key"),
        ) != (TARGET_METAFIELD_NAMESPACE, TARGET_METAFIELD_KEY):
            detail = (
                "Color option is already linked to "
                f"{current_link.get('namespace')}.{current_link.get('key')}, not "
                f"{TARGET_METAFIELD_NAMESPACE}.{TARGET_METAFIELD_KEY}."
            )
            results.extend(
                _error_result(row, detail, product_id=product["id"], option_id=option["id"])
                for row in group_rows
            )
            continue

        group_results: list[LinkResult] = []
        update_values: list[dict[str, str]] = []
        group_has_error = False

        for row in group_rows:
            option_value = _find_option_value(option, row.option_value)
            if not option_value:
                group_results.append(
                    _error_result(
                        row,
                        "Expected exactly one option value named "
                        f"{row.option_value!r}; none was found.",
                        product_id=product["id"],
                        option_id=option["id"],
                    )
                )
                group_has_error = True
                continue

            try:
                metaobject = client.get_metaobject_by_handle(row.metaobject_handle)
            except ShopifyApiError as exc:
                group_results.append(
                    _error_result(
                        row,
                        str(exc),
                        product_id=product["id"],
                        option_id=option["id"],
                        option_value_id=option_value["id"],
                    )
                )
                group_has_error = True
                continue

            if not metaobject:
                group_results.append(
                    _error_result(
                        row,
                        "Metaobject shopify--color-pattern/"
                        f"{row.metaobject_handle!r} was not found.",
                        product_id=product["id"],
                        option_id=option["id"],
                        option_value_id=option_value["id"],
                    )
                )
                group_has_error = True
                continue

            result = LinkResult.from_link_row(
                row,
                product_id=product["id"],
                option_id=option["id"],
                option_value_id=option_value["id"],
                metaobject_id=metaobject["id"],
            )
            if option_value.get("linkedMetafieldValue") == metaobject["id"]:
                result.action = "NONE"
                result.status = "ALREADY_LINKED"
                result.detail = "Existing reference already matches the target metaobject."
            else:
                result.action = "LINK"
                result.status = "PENDING"
                result.detail = "Ready to set explicit linkedMetafieldValue."
                update_values.append(
                    {
                        "id": option_value["id"],
                        "linkedMetafieldValue": metaobject["id"],
                    }
                )
            group_results.append(result)

        if group_has_error:
            for result in group_results:
                if result.status == "PENDING":
                    result.status = "SKIPPED"
                    result.detail = (
                        "Skipped because another value in this product option failed validation."
                    )
            results.extend(group_results)
            continue

        if not update_values:
            results.extend(group_results)
            continue

        if not execute:
            for result in group_results:
                if result.status == "PENDING":
                    result.status = "WOULD_LINK"
                    result.detail = "Dry run only; no Shopify mutation was sent."
            results.extend(group_results)
            continue

        try:
            client.update_option_values(product["id"], option, update_values)
        except ShopifyApiError as exc:
            for result in group_results:
                if result.status == "PENDING":
                    result.status = "ERROR"
                    result.detail = str(exc)
        else:
            for result in group_results:
                if result.status == "PENDING":
                    result.status = "LINKED"
                    result.detail = "Explicit Color & pattern metaobject reference applied."
        results.extend(group_results)

    return results


def write_result_report(
    results: Iterable[LinkResult], output_directory: Path, execute: bool
) -> Path:
    """Write an auditable result CSV and return its absolute path."""
    output_directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    mode = "execute" if execute else "dry_run"
    output_path = output_directory / f"color_pattern_link_results_{mode}_{timestamp}.csv"
    with output_path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=RESULT_FIELDNAMES)
        writer.writeheader()
        for result in results:
            writer.writerow(result.as_csv_row())
    return output_path


def summarize_results(results: Iterable[LinkResult]) -> dict[str, int]:
    """Count results by durable status for CLI output and automation."""
    return dict(sorted(Counter(result.status for result in results).items()))
