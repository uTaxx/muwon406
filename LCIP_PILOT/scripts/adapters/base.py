"""SourceAdapter — 뉴스 소스별 수집 로직을 갈아끼울 수 있는 공통 인터페이스.

Round 4 지시: "각 뉴스 소스(Google RSS/Naver/DART/정부/IR)를 Adapter 클래스로 분리한다."
Pipeline(scripts/pipeline/collect.py)은 이 인터페이스에만 의존한다 — 새 소스를 추가해도
Pipeline 코드는 수정하지 않고 Adapter만 새로 만들면 된다 (providers/base.py의 AIProvider와
동일한 설계 원칙).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class RawArticle:
    """Adapter가 반환하는 정규화 이전(raw) 수집 결과 — Article 스키마 매핑은 Pipeline의
    Normalize 단계(TASK-011)가 담당한다."""

    title_original: str
    source_url: str
    source_name: str
    published_at: str | None
    language: str
    summary_raw: str | None = None


class SourceAdapterDisabledError(RuntimeError):
    """Adapter가 enabled=False(기본값)이거나 source_config.active=False일 때 발생."""


class SourceAdapter(ABC):
    """모든 뉴스 소스 Adapter(Google RSS/Naver/DART/정부/IR 등)가 구현해야 하는 계약."""

    def __init__(self, source_config: dict):
        self.source_config = source_config

    @property
    def source_id(self) -> str:
        return self.source_config.get("source_id", "UNKNOWN")

    @abstractmethod
    def collect(self, query: str) -> list[RawArticle]:
        """주어진 query(topic 키워드 등)로 소스를 조회해 RawArticle 목록을 반환한다."""
