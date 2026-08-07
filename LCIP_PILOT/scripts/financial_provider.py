"""FinancialDataProvider — Architect Review Round 8, Quick Company Scan 파이프라인의
"Financial Provider" 단계.

Round 5부터 `scenarios/scenario_3_investment_review.py`(구 `demo_quick_scan.py`)에
`DEMO_PEERS`라는 이름으로 하드코딩되어 있던 Comparable Peer 목록을 Provider Layer
패턴(추상 클래스 + Mock 구현체)으로 옮긴 것이다 — 새 Framework가 아니라 기존
`providers/`의 "추상 인터페이스 + Mock" 패턴을 재무 데이터에도 적용한 것뿐이다
(ADR-010 "새 Framework 금지" 원칙 참고). Round 7 보고서 §53(Top 10 Refactoring
Candidates 10번)에서 지적한 하드코딩 문제도 함께 해소한다.

Pilot 범위에서는 `MockFinancialDataProvider`만 존재한다 — 실제 재무 데이터
소스(Bloomberg/CapitalIQ/공시 XBRL 등) 연동은 RC2 이후 범위이며, Architect Review
Round 8 지시("Financial Provider는 Mock, 나머지는 실제 코드")와 정확히 일치한다.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from investment_review import ComparablePeer


class FinancialDataProvider(ABC):
    """모든 재무 데이터 공급자가 구현해야 하는 계약."""

    @abstractmethod
    def get_comparable_peers(self, company_id: str | None) -> list[ComparablePeer]:
        """company_id에 대한 Comparable Peer(EV/EBITDA·PER·PBR) 목록을 반환한다."""


class MockFinancialDataProvider(FinancialDataProvider):
    """Pilot 기본값 — 실제 재무 데이터 연동 전까지 예시 Peer 2개만 반환한다.

    회사별로 다른 Peer를 반환하지 않는다(모든 company_id에 동일 예시) — 실제 재무
    데이터 없이 회사별로 다르게 보이면 마치 진짜 조사를 한 것처럼 오인될 수 있기
    때문에, 의도적으로 "예시"임이 드러나도록 고정된 값을 쓴다.
    """

    _DEMO_PEERS = [
        ComparablePeer(
            "Peer A (예시)", ev_ebitda=8.5, per=13.0, pbr=1.4,
            source_url="https://example.com/peer-a",
        ),
        ComparablePeer(
            "Peer B (예시)", ev_ebitda=9.5, per=15.0, pbr=1.6,
            source_url="https://example.com/peer-b",
        ),
    ]

    def get_comparable_peers(self, company_id: str | None) -> list[ComparablePeer]:
        return list(self._DEMO_PEERS)
