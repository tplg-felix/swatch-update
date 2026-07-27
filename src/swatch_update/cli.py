"""Command-line entry point for the manually triggered swatch linker."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import ConfigurationError, load_settings
from .linker import link_rows, summarize_results, write_result_report
from .manifest import ManifestError, build_manifest, load_manifest
from .shopify import ShopifyApiError, ShopifyClient

EXECUTION_CONFIRMATION = "APPLY_COLOR_PATTERN_LINKS"


def _path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def build_parser() -> argparse.ArgumentParser:
    """Create the stable command-line interface."""
    parser = argparse.ArgumentParser(
        prog="swatch-linker",
        description=(
            "Safely link Matrixify-imported Color option values to Shopify "
            "Color & pattern metaobjects."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser(
        "build-manifest",
        help="Create a link manifest and metaobject preflight CSV from a Matrixify workbook.",
    )
    build.add_argument("workbook", type=_path, help="Input Matrixify .xlsx or .xlsm workbook.")
    build.add_argument(
        "--manifest",
        type=_path,
        default=_path("output/color_pattern_link_manifest.csv"),
        help="Output link-manifest CSV path.",
    )
    build.add_argument(
        "--preflight",
        type=_path,
        default=_path("output/color_pattern_metaobject_preflight.csv"),
        help="Output distinct-metaobject preflight CSV path.",
    )
    build.add_argument(
        "--sheet",
        default="Product",
        help="Matrixify worksheet name (default: Product).",
    )
    build.add_argument(
        "--option-name", default="Color", help="Option name to inspect (default: Color)."
    )

    link = subparsers.add_parser(
        "link",
        help="Validate or explicitly link the entries in a reviewed manifest.",
    )
    link.add_argument(
        "--manifest",
        type=_path,
        default=_path("output/color_pattern_link_manifest.csv"),
        help="Reviewed link-manifest CSV path.",
    )
    link.add_argument(
        "--output-dir",
        type=_path,
        default=_path("reports"),
        help="Directory in which to write a timestamped result report.",
    )
    link.add_argument(
        "--env-file",
        type=_path,
        default=_path(".env"),
        help="Local .env file containing Shopify credentials.",
    )
    link.add_argument(
        "--execute",
        action="store_true",
        help="Apply the updates. Omit this flag for the mandatory no-write dry run.",
    )
    link.add_argument(
        "--confirm",
        default="",
        help=f"Required with --execute. Must equal {EXECUTION_CONFIRMATION!r}.",
    )
    return parser


def _run_build_manifest(arguments: argparse.Namespace) -> int:
    rows = build_manifest(
        input_workbook=arguments.workbook,
        output_manifest=arguments.manifest,
        output_preflight=arguments.preflight,
        worksheet_name=arguments.sheet,
        option_name=arguments.option_name,
    )
    handles = {row.metaobject_handle for row in rows}
    print(f"Created {arguments.manifest}")
    print(f"Created {arguments.preflight}")
    print(
        f"Found {len(rows)} affected rows across {len(handles)} "
        "distinct Color & pattern handles."
    )
    return 0


def _run_link(arguments: argparse.Namespace) -> int:
    if arguments.execute and arguments.confirm != EXECUTION_CONFIRMATION:
        raise ConfigurationError(
            "Live execution is blocked. Re-run with "
            f"--execute --confirm {EXECUTION_CONFIRMATION} after reviewing the dry-run report."
        )

    settings = load_settings(arguments.env_file)
    rows = load_manifest(arguments.manifest)
    client = ShopifyClient(settings)
    results = link_rows(rows, client, execute=arguments.execute)
    report_path = write_result_report(results, arguments.output_dir, execute=arguments.execute)
    summary = summarize_results(results)

    mode = "LIVE EXECUTION" if arguments.execute else "DRY RUN"
    print(f"{mode} complete.")
    print("Result summary: " + ", ".join(f"{status}={count}" for status, count in summary.items()))
    print(f"Result report: {report_path}")
    return 1 if summary.get("ERROR", 0) else 0


def main(argv: list[str] | None = None) -> int:
    """Run the command-line application and return a shell-friendly status code."""
    parser = build_parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "build-manifest":
            return _run_build_manifest(arguments)
        if arguments.command == "link":
            return _run_link(arguments)
        parser.error(f"Unknown command: {arguments.command}")
    except (ConfigurationError, ManifestError, ShopifyApiError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
