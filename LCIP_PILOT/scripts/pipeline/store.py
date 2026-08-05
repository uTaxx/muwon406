"""Store 단계 — 검증된 레코드를 ARTICLE_DB/INTELLIGENCE_DB에 저장한다.

Round 5부터 실제 저장 로직은 `scripts/storage/`(StorageBackend 추상화)로 이전되었다.
이 모듈은 Round 4까지 쓰이던 `sink_path: Path` 기반 함수 시그니처(`tests/test_pipeline.py`,
`tests/test_mvp_integration.py` 등)와의 하위 호환을 위해 남겨두되, 내부적으로는
`LocalJSONLStorage`에 위임한다 — 저장 로직 자체는 한 곳(`scripts/storage/`)에만 존재한다.

새 코드(`scripts/demo_mvp.py` 등)는 이 함수들 대신 `StorageBackend`를 직접 주입받아
쓴다 (Round 5 지시: "Pipeline은 StorageBackend만 참조한다").
"""
from __future__ import annotations

from pathlib import Path

from storage.local_jsonl_storage import LocalJSONLStorage


def _storage_and_collection(sink_path: Path) -> tuple[LocalJSONLStorage, str]:
    """`.../ARTICLE_DB.jsonl` 같은 기존 경로를 (같은 폴더를 쓰는 LocalJSONLStorage,
    collection 이름) 튜플로 분해한다."""
    return LocalJSONLStorage(sink_path.parent), sink_path.stem


def append_record(sink_path: Path, record: dict) -> None:
    storage, collection = _storage_and_collection(sink_path)
    storage.append(collection, record)


def load_records(sink_path: Path) -> list[dict]:
    storage, collection = _storage_and_collection(sink_path)
    return storage.load_all(collection)


def existing_ids(sink_path: Path, id_field: str) -> set[str]:
    storage, collection = _storage_and_collection(sink_path)
    return storage.existing_ids(collection, id_field)


def existing_values(sink_path: Path, field: str) -> set[str]:
    storage, collection = _storage_and_collection(sink_path)
    return storage.existing_values(collection, field)
