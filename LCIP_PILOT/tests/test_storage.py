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


def test_google_sheets_storage_enabled_with_spreadsheet_id_raises_not_implemented():
    storage = GoogleSheetsStorage(spreadsheet_id="fake-id", enabled=True)
    with pytest.raises(NotImplementedError):
        storage.append("ARTICLE_DB", {})
    with pytest.raises(NotImplementedError):
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
