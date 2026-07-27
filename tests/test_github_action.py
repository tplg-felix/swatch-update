from pathlib import Path

import pytest

from swatch_update.github_action import DownloadError, download_workbook


class FakeResponse:
    def __init__(
        self,
        status_code: int,
        body: bytes,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self._body = body
        self.headers = headers or {}

    def iter_content(self, chunk_size: int):
        del chunk_size
        yield self._body


class FakeSession:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.calls: list[dict] = []

    def get(self, url: str, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return self.response


def test_download_workbook_follows_redirects_and_writes_xlsx(tmp_path: Path) -> None:
    destination = tmp_path / "matrixify.xlsx"
    session = FakeSession(FakeResponse(200, b"PK\x03\x04minimal workbook"))

    result = download_workbook("https://app.matrixify.app/files/example.xlsx", destination, session)

    assert result == destination
    assert destination.read_bytes() == b"PK\x03\x04minimal workbook"
    assert session.calls[0]["allow_redirects"] is True


def test_download_workbook_rejects_non_excel_response(tmp_path: Path) -> None:
    destination = tmp_path / "matrixify.xlsx"
    session = FakeSession(FakeResponse(200, b"<html>Sign in</html>"))

    with pytest.raises(DownloadError, match="not an Excel workbook"):
        download_workbook("https://app.matrixify.app/files/example.xlsx", destination, session)

    assert not destination.exists()


def test_download_workbook_rejects_non_https_urls(tmp_path: Path) -> None:
    with pytest.raises(DownloadError, match="HTTPS URL"):
        download_workbook("http://example.com/file.xlsx", tmp_path / "matrixify.xlsx")
