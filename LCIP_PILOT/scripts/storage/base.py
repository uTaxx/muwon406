"""StorageBackend — 저장소 구현에 무관한 Pipeline 저장 인터페이스.

Round 5 지시: "Storage를 Provider 구조처럼 추상화한다. Pipeline은 StorageBackend만
참조한다. Store 구현이 바뀌어도 Pipeline은 수정하지 않는다." `providers/base.py`의
AIProvider, `adapters/base.py`의 SourceAdapter와 동일한 설계 원칙이다.

`collection`은 ARTICLE_DB/INTELLIGENCE_DB 같은 논리적 저장 단위 이름이다 — 실제로는
로컬 JSONL 파일 하나, Google Sheets 탭 하나, 또는 미래의 DB 테이블 하나에 대응할 수 있다.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class StorageBackendDisabledError(RuntimeError):
    """Storage 구현이 enabled=False(기본값)이거나 아직 설정되지 않은 상태에서 호출되면 발생."""


class StorageBackend(ABC):
    """모든 저장소 구현(LocalJSONLStorage/GoogleSheetsStorage/FutureDatabaseStorage 등)이
    구현해야 하는 계약."""

    @abstractmethod
    def append(self, collection: str, record: dict) -> None:
        """collection에 레코드 1건을 추가한다."""

    @abstractmethod
    def load_all(self, collection: str) -> list[dict]:
        """collection의 전체 레코드를 반환한다. 저장된 것이 없으면 빈 리스트."""

    def existing_ids(self, collection: str, id_field: str) -> set[str]:
        return {record[id_field] for record in self.load_all(collection)}

    def existing_values(self, collection: str, field: str) -> set[str]:
        return {record[field] for record in self.load_all(collection) if record.get(field)}
