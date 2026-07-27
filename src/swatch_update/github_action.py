"""GitHub Actions runner for the manually dispatched swatch-linking workflow."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests

from .cli import EXECUTION_CONFIRMATION
from .config import ConfigurationError, load_settings
from .linker import link_rows, summarize_results, write_result_report
from .manifest import ManifestError, build_manifest, load_manifest
from .shopify import ShopifyApiError, ShopifyClient

MAX_DOWNLOAD_BYTES = 500 * 1024 * 1024


class DownloadError(RuntimeError):
    """Raised when the supplied Matrixify download URL cannot be used safely."""


def _validate_download_url(url: str) -> str:
    cleaned = url.strip()
    parsed = urlparse(cleaned)
    if parsed.scheme != "https" or not parsed.netloc:
        raise DownloadError("The Matrixify download link must be a complete HTTPS URL.")
    return cleaned


def download_workbook(
    url: str,
    destination: Path,
    session: requests.Session | None = None,
    max_bytes: int = MAX_DOWNLOAD_BYTES,
) -> Path:
    """Download a Matrixify Excel workbook without printing the protected URL.

    Matrixify can redirect an externally downloadable export to temporary S3
    storage, so redirects are intentionally followed. The source URL and final
    redirect URL are never echoed to the workflow log.
    """
    safe_url = _validate_download_url(url)
    client = session or requests.Session()
    try:
        response = client.get(safe_url, stream=True, timeout=(20, 180), allow_redirects=True)
    except requests.RequestException as exc:
        raise DownloadError("The Matrixify workbook could not be downloaded.") from exc

    if response.status_code != 200:
        raise DownloadError(
            "The Matrixify download returned HTTP "
            f"{response.status_code}. Confirm external downloads are enabled and the link is valid."
        )

    content_length = response.headers.get("Content-Length")
    if content_length and int(content_length) > max_bytes:
        raise DownloadError("The Matrixify workbook exceeds the 500 MB workflow safety limit.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    bytes_written = 0
    with destination.open("wb") as output:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if not chunk:
                continue
            bytes_written += len(chunk)
            if bytes_written > max_bytes:
                output.close()
                destination.unlink(missing_ok=True)
                raise DownloadError(
                    "The Matrixify workbook exceeds the 500 MB workflow safety limit."
                )
            output.write(chunk)

    with destination.open("rb") as output:
        file_signature = output.read(4)
    if file_signature != b"PK\x03\x04":
        destination.unlink(missing_ok=True)
        raise DownloadError(
            "The downloaded file is not an Excel workbook. Confirm the Matrixify link is a direct "
            "download link, not a sign-in or HTML page."
        )

    print(f"Downloaded Matrixify workbook successfully ({bytes_written:,} bytes).")
    return destination


def build_parser() -> argparse.ArgumentParser:
    """Create the limited, workflow-specific command-line interface."""
    parser = argparse.ArgumentParser(
        description="Run the Shopify swatch linker from a GitHub Actions workflow."
    )
    parser.add_argument(
        "--download-url",
        default=os.getenv("MATRIXIFY_DOWNLOAD_URL", ""),
        help="Matrixify direct-download URL. Defaults to MATRIXIFY_DOWNLOAD_URL.",
    )
    parser.add_argument(
        "--mode",
        choices=("dry-run", "execute"),
        default="dry-run",
        help="Use dry-run unless a reviewed report has no errors.",
    )
    parser.add_argument(
        "--confirmation",
        default="",
        help=f"Required for execute mode. Must equal {EXECUTION_CONFIRMATION!r}.",
    )
    parser.add_argument(
        "--worksheet",
        default="Product",
        help="Matrixify worksheet name (default: Product).",
    )
    return parser


def run(arguments: argparse.Namespace) -> int:
    """Download, validate, and process a Matrixify workbook for one workflow run."""
    if arguments.mode == "execute" and arguments.confirmation != EXECUTION_CONFIRMATION:
        raise ConfigurationError(
            "Live execution is blocked. In the Run workflow form, type "
            f"{EXECUTION_CONFIRMATION} exactly to confirm a reviewed batch."
        )

    workbook_path = download_workbook(arguments.download_url, Path("input/matrixify_input.xlsx"))
    manifest_path = Path("output/color_pattern_link_manifest.csv")
    preflight_path = Path("output/color_pattern_metaobject_preflight.csv")
    build_manifest(
        input_workbook=workbook_path,
        output_manifest=manifest_path,
        output_preflight=preflight_path,
        worksheet_name=arguments.worksheet,
    )
    rows = load_manifest(manifest_path)
    settings = load_settings()
    client = ShopifyClient(settings)
    execute = arguments.mode == "execute"
    results = link_rows(rows, client, execute=execute)
    report_path = write_result_report(results, Path("reports"), execute=execute)
    summary = summarize_results(results)

    print(f"Mode: {arguments.mode}")
    print("Result summary: " + ", ".join(f"{status}={count}" for status, count in summary.items()))
    print(f"Download the report artifact to review: {report_path}")
    return 1 if summary.get("ERROR", 0) else 0


def main(argv: list[str] | None = None) -> int:
    """Run the GitHub Actions entry point with safe, concise failure messages."""
    parser = build_parser()
    arguments = parser.parse_args(argv)
    try:
        return run(arguments)
    except (ConfigurationError, DownloadError, ManifestError, ShopifyApiError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
