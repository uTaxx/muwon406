"""StorageRegistryAdapter — `scripts/storage/`에 존재하는 StorageBackend 구현체 목록을
공통 Registry Interface로 감싼다. 실제 저장 로직은 그대로 `scripts/storage/*.py`에 있고,
이 어댑터는 "어떤 구현체가 있고 Pilot 기본값이 무엇인지"만 정적으로 나열한다.
"""
from __future__ import annotations

from .base import Registry

_STORAGE_BACKENDS = [
    {
        "storage_id": "local_jsonl",
        "class_name": "LocalJSONLStorage",
        "module": "storage.local_jsonl_storage",
        "enabled_by_default": True,
        "description": "로컬 JSONL 파일 기반 저장소 — Pilot 기본값, 실동작.",
    },
    {
        "storage_id": "google_sheets",
        "class_name": "GoogleSheetsStorage",
        "module": "storage.google_sheets_storage",
        "enabled_by_default": False,
        "description": "Google Sheets 저장소 — 구조만 존재, enabled=False 기본값.",
    },
    {
        "storage_id": "future_database",
        "class_name": "FutureDatabaseStorage",
        "module": "storage.future_storage",
        "enabled_by_default": False,
        "description": "미래 확장용(PostgreSQL 등) — 아직 구현하지 않음(Enterprise Backlog).",
    },
]


class StorageRegistryAdapter(Registry):
    registry_id = "storage"

    def list_entries(self) -> list[dict]:
        return list(_STORAGE_BACKENDS)

    def get(self, entry_id: str) -> dict | None:
        for entry in _STORAGE_BACKENDS:
            if entry["storage_id"] == entry_id:
                return entry
        return None
