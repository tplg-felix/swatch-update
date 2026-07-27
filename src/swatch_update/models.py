"""Typed records shared by manifest generation, Shopify requests, and result reporting."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class LinkRow:
    """One Color option value that should be linked to one Color & pattern entry."""

    source_excel_row: int
    product_handle: str
    product_title: str
    variant_sku: str
    option_name: str
    option_value: str
    metaobject_handle: str
    expected_source_color: str
    expected_source_material: str

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> LinkRow:
        """Convert a CSV manifest row into a validated record."""
        return cls(
            source_excel_row=int(row["Source Excel Row"]),
            product_handle=row["Product Handle"].strip(),
            product_title=row.get("Product Title", "").strip(),
            variant_sku=row.get("Variant SKU", "").strip(),
            option_name=row["Option Name"].strip(),
            option_value=row["Option Value (Display Name)"].strip(),
            metaobject_handle=row["Color & Pattern Metaobject Handle"].strip(),
            expected_source_color=row.get("Expected Source Color", "").strip(),
            expected_source_material=row.get("Expected Source Material", "").strip(),
        )


@dataclass
class LinkResult:
    """One auditable result from a dry run or an execute run."""

    source_excel_row: int
    product_handle: str
    option_name: str
    option_value: str
    metaobject_handle: str
    product_id: str = ""
    option_id: str = ""
    option_value_id: str = ""
    metaobject_id: str = ""
    action: str = ""
    status: str = ""
    detail: str = ""

    @classmethod
    def from_link_row(cls, row: LinkRow, **overrides: Any) -> LinkResult:
        """Start a result record from its source manifest row."""
        result = cls(
            source_excel_row=row.source_excel_row,
            product_handle=row.product_handle,
            option_name=row.option_name,
            option_value=row.option_value,
            metaobject_handle=row.metaobject_handle,
        )
        for key, value in overrides.items():
            setattr(result, key, value)
        return result

    def as_csv_row(self) -> dict[str, Any]:
        """Return the stable, external report schema."""
        raw = asdict(self)
        return {
            "source_excel_row": raw["source_excel_row"],
            "product_handle": raw["product_handle"],
            "option_name": raw["option_name"],
            "option_value": raw["option_value"],
            "metaobject_handle": raw["metaobject_handle"],
            "product_id": raw["product_id"],
            "option_id": raw["option_id"],
            "option_value_id": raw["option_value_id"],
            "metaobject_id": raw["metaobject_id"],
            "action": raw["action"],
            "status": raw["status"],
            "detail": raw["detail"],
        }
