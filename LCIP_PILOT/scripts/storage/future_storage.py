"""FutureDatabaseStorage — 아직 구현하지 않는다. Storage 확장 지점을 증명하기 위한
placeholder(`providers/future_providers.py`, `adapters/future_adapters.py`와 동일한 패턴).

CLAUDE.md는 Pilot 단계에서 별도 DB(PostgreSQL 등)를 먼저 구축하지 말라고 명시한다 — 이
클래스는 "나중에 정말 필요해지면 여기만 채우면 된다"는 확장 지점만 보여준다.

Round 6/7 감사 표시: `scripts/scenarios/*.py` 어느 것도 이 클래스를 호출하지 않는다
(`LocalJSONLStorage`가 Pilot 기본값) — `tests/test_storage.py`에서만 "StorageBackend
계약을 지키는지"를 확인한다.
"""
from __future__ import annotations

from .base import StorageBackend


class FutureDatabaseStorage(StorageBackend):
    """미래 확장용(PostgreSQL 등). 아직 구현하지 않는다 (Architect Review Round 5)."""

    def append(self, collection: str, record: dict) -> None:
        raise NotImplementedError("FutureDatabaseStorage는 아직 구현되지 않았다 (Future).")

    def load_all(self, collection: str) -> list[dict]:
        raise NotImplementedError("FutureDatabaseStorage는 아직 구현되지 않았다 (Future).")
