from pathlib import Path

from openpyxl import Workbook

from swatch_update.manifest import build_manifest, load_manifest


def test_build_manifest_extracts_only_slash_containing_color_values(tmp_path: Path) -> None:
    workbook_path = tmp_path / "matrixify.xlsx"
    manifest_path = tmp_path / "manifest.csv"
    preflight_path = tmp_path / "preflight.csv"

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Product"
    worksheet.append(
        [
            "Handle",
            "Title",
            "Variant SKU",
            "Option 1 Name",
            "Option 1 Value",
            "Variant Metafield: custom.color [single_line_text_field]",
            "Variant Metafield: custom.material [single_line_text_field]",
        ]
    )
    worksheet.append(
        [
            "card-sacoche",
            "Card Sacoche",
            "TP-WBA-CSC-IGN-55",
            "Color",
            "Ivy Green / Vintage Ripstop",
            "Ivy Green",
            "Vintage Ripstop",
        ]
    )
    worksheet.append(
        [
            "webbing-loop",
            "Webbing Loop",
            "TP-WST-20WL-WDL-02",
            "Color",
            "Woodlot",
            "Woodlot",
            "Poly Rope",
        ]
    )
    workbook.save(workbook_path)

    rows = build_manifest(workbook_path, manifest_path, preflight_path)

    assert len(rows) == 1
    assert rows[0].product_handle == "card-sacoche"
    assert rows[0].option_value == "Ivy Green / Vintage Ripstop"
    assert rows[0].metaobject_handle == "ivy-green-vintage-ripstop"
    assert rows[0].expected_source_color == "Ivy Green"
    assert rows[0].expected_source_material == "Vintage Ripstop"
    assert manifest_path.exists()
    assert preflight_path.exists()

    loaded = load_manifest(manifest_path)
    assert loaded == rows
