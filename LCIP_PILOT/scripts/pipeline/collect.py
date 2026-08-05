"""Collect 단계 — SourceAdapter를 호출해 RawArticle 목록을 가져온다.

Pipeline 코드는 `SourceAdapter` 인터페이스에만 의존한다 — 어떤 Adapter를 주입하느냐에 따라
실제 소스가 바뀔 뿐, 이 함수는 수정하지 않는다 (TASK-010 Source Adapter 설계 원칙).
"""
from __future__ import annotations

from adapters.base import RawArticle, SourceAdapter


def collect(adapter: SourceAdapter, query: str) -> list[RawArticle]:
    return adapter.collect(query)
