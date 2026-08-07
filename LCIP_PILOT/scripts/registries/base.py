"""Registry — Architect Review Round 7.

Round 7 지시: "새로운 Engine을 만드는 것이 아니라 Registry 관리 방식을 통일한다." 이 모듈은
이미 존재하는 7개 Registry(Company/Source/Model/Prompt/Workflow/Config/Storage)의 파일
형식(YAML list, YAML dict, 파일 목록, 클래스 목록)은 그대로 두고, 그 위에 얇은 공통
Interface(`list_entries`/`get`/`count`)만 씌운다. 각 Registry의 원본 데이터 구조나 기존
호출부(`config/company_registry.yaml`을 직접 읽는 `quick_company_scan.py` 등)는 전혀
바꾸지 않는다 — RegistryManager는 "추가 조회 경로"이지 "유일한 조회 경로"가 아니다.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class Registry(ABC):
    """모든 Registry 어댑터가 구현해야 하는 최소 계약."""

    registry_id: str

    @abstractmethod
    def list_entries(self) -> list[dict]:
        """이 Registry의 모든 항목을 dict 목록으로 반환한다."""

    @abstractmethod
    def get(self, entry_id: str) -> dict | None:
        """entry_id에 해당하는 항목을 반환한다. 없으면 None(임의로 지어내지 않는다)."""

    def count(self) -> int:
        return len(self.list_entries())
