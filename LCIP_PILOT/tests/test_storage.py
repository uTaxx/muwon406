import pytest

from storage.base import StorageBackend, StorageBackendDisabledError
from storage.future_storage import FutureDatabaseStorage
from storage.google_sheets_storage import GoogleSheetsStorage
from storage.local_jsonl_storage import LocalJSONLStorage


def test_local_jsonl_storage_is_a_storage_backend():
    assert isinstance(LocalJSONLStorage("/tmp"), StorageBackend)


def test_local_jsonl_storage_append_and_load_round_trips(tmp_path):
    storage = LocalJSONLStorage(tmp_path)
    storage.append("ARTICLE_DB", {"article_id": "ART-20260805-0001", "canonical_url": "https://example.com/a"})
    storage.append("ARTICLE_DB", {"article_id": "ART-20260805-0002", "canonical_url": "https://example.com/b"})
    records = storage.load_all("ARTICLE_DB")
    assert len(records) == 2
    assert storage.existing_ids("ARTICLE_DB", "article_id") == {
        "ART-20260805-0001",
        "ART-20260805-0002",
    }
    assert storage.existing_values("ARTICLE_DB", "canonical_url") == {
        "https://example.com/a",
        "https://example.com/b",
    }


def test_local_jsonl_storage_load_all_returns_empty_list_when_missing(tmp_path):
    storage = LocalJSONLStorage(tmp_path)
    assert storage.load_all("DOES_NOT_EXIST") == []


def test_local_jsonl_storage_separates_collections(tmp_path):
    storage = LocalJSONLStorage(tmp_path)
    storage.append("ARTICLE_DB", {"id": "a1"})
    storage.append("INTELLIGENCE_DB", {"id": "i1"})
    assert len(storage.load_all("ARTICLE_DB")) == 1
    assert len(storage.load_all("INTELLIGENCE_DB")) == 1


def test_google_sheets_storage_is_a_storage_backend():
    assert isinstance(GoogleSheetsStorage(), StorageBackend)


def test_google_sheets_storage_disabled_by_default():
    storage = GoogleSheetsStorage()
    assert storage.enabled is False
    with pytest.raises(StorageBackendDisabledError):
        storage.append("ARTICLE_DB", {})
    with pytest.raises(StorageBackendDisabledError):
        storage.load_all("ARTICLE_DB")


def test_google_sheets_storage_enabled_without_spreadsheet_id_raises():
    storage = GoogleSheetsStorage(enabled=True)
    with pytest.raises(RuntimeError):
        storage.append("ARTICLE_DB", {})


class _FakeWorksheet:
    def __init__(self):
        self.rows: list[list[str]] = []

    def row_values(self, row_number: int) -> list[str]:
        return self.rows[row_number - 1] if len(self.rows) >= row_number else []

    def append_row(self, values: list) -> None:
        self.rows.append([str(v) for v in values])

    def get_all_records(self) -> list[dict]:
        if not self.rows:
            return []
        headers, *data_rows = self.rows
        return [dict(zip(headers, row)) for row in data_rows]


class _FakeSpreadsheet:
    def __init__(self):
        self.worksheets_by_name: dict[str, _FakeWorksheet] = {}

    def worksheet(self, name: str) -> _FakeWorksheet:
        import gspread.exceptions

        if name not in self.worksheets_by_name:
            raise gspread.exceptions.WorksheetNotFound(name)
        return self.worksheets_by_name[name]


class _FakeGspreadClient:
    def __init__(self, spreadsheet: _FakeSpreadsheet):
        self._spreadsheet = spreadsheet

    def open_by_key(self, spreadsheet_id: str) -> _FakeSpreadsheet:
        return self._spreadsheet


def test_google_sheets_storage_append_and_load_round_trips_with_injected_client():
    """Round 13(RC2 실체화) — GoogleRSSAdapter의 http_get 주입과 동일한 패턴으로,
    실제 네트워크 없이 append/load_all의 행 매핑 로직만 검증한다."""
    spreadsheet = _FakeSpreadsheet()
    spreadsheet.worksheets_by_name["ARTICLE_DB"] = _FakeWorksheet()
    storage = GoogleSheetsStorage(
        spreadsheet_id="fake-id", enabled=True,
        client_factory=lambda: _FakeGspreadClient(spreadsheet),
    )

    storage.append("ARTICLE_DB", {"article_id": "ART-0001", "title": "제목 A"})
    storage.append("ARTICLE_DB", {"article_id": "ART-0002", "title": "제목 B"})

    records = storage.load_all("ARTICLE_DB")
    assert records == [
        {"article_id": "ART-0001", "title": "제목 A"},
        {"article_id": "ART-0002", "title": "제목 B"},
    ]


def test_google_sheets_storage_missing_tab_raises_clear_runtime_error():
    spreadsheet = _FakeSpreadsheet()  # ARTICLE_DB 탭 없음
    storage = GoogleSheetsStorage(
        spreadsheet_id="fake-id", enabled=True,
        client_factory=lambda: _FakeGspreadClient(spreadsheet),
    )
    with pytest.raises(RuntimeError, match="create_google_sheets.py"):
        storage.load_all("ARTICLE_DB")


def test_future_database_storage_is_a_storage_backend_but_not_implemented():
    storage = FutureDatabaseStorage()
    assert isinstance(storage, StorageBackend)
    with pytest.raises(NotImplementedError):
        storage.append("ARTICLE_DB", {})
    with pytest.raises(NotImplementedError):
        storage.load_all("ARTICLE_DB")


def test_storage_backends_are_interchangeable_same_call_signature(tmp_path):
    """Storage 교체 가능성 검증: 동일한 시그니처로 여러 StorageBackend를 다룰 수 있다."""
    backends: list[StorageBackend] = [LocalJSONLStorage(tmp_path)]
    for backend in backends:
        backend.append("ARTICLE_DB", {"article_id": "ART-20260805-0001"})
        assert backend.load_all("ARTICLE_DB") == [{"article_id": "ART-20260805-0001"}]
