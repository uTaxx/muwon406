#!/usr/bin/env python3
"""Scenario 3 — Investment Review (Architect Review Round 7).

Comparable(Peer EV/EBITDA·PER·PBR) 기반 Valuation과 스크리닝 신호를 만든다. Round 7
지시대로 Pilot 범위는 Comparable 기반만 유지한다 — DCF/LBO/Option은 Enterprise
Backlog(변경 없음).

"모든 Scenario는 독립 실행 가능해야 한다"는 지시를 만족시키기 위해, Investment Review의
입력(quick_report 기반 review_input)을 Scenario 2를 직접 호출해 스스로 만든다 — 즉 이
스크립트 하나만 실행해도 전체 흐름(Quick Scan → Investment Review)이 끝까지 도는다.

사용법: python3 scripts/scenarios/scenario_3_investment_review.py ["회사명"]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from investment_review import ComparablePeer, build_investment_review
from scenarios import scenario_2_quick_company_scan

# 데모용 Comparable Peer 예시(공개 배수를 실제로 조회하지 않았음을 명시) — 실제
# 서비스에서는 Knowledge Retrieval Engine/외부 데이터로 채워야 한다.
DEMO_PEERS = [
    ComparablePeer("Peer A (예시)", ev_ebitda=8.5, per=13.0, pbr=1.4, source_url="https://example.com/peer-a"),
    ComparablePeer("Peer B (예시)", ev_ebitda=9.5, per=15.0, pbr=1.6, source_url="https://example.com/peer-b"),
]


def run(query: str = "LX Hausys", verbose: bool = True) -> dict:
    """Scenario 2(Quick Scan)를 내부 호출해 review_input을 얻은 뒤 Investment Review를
    실행한다. {quick_report, review} 반환."""

    def log(msg: str) -> None:
        if verbose:
            print(msg)

    scan = scenario_2_quick_company_scan.run(query, verbose=verbose)

    log("\n[Scenario 3] Investment Review — Comparable 기반 Valuation (DCF 미사용)")
    review = build_investment_review(scan["review_input"], DEMO_PEERS)
    log(f"  peer_average: {review['peer_average']}")
    if review["estimated_valuation"]:
        log(f"  estimated_valuation.basis: {review['estimated_valuation']['basis']}")
    log(f"  deal_killer.found: {review['deal_killer']['found']}")
    log(f"  recommendation.signal: {review['recommendation']['signal']}")

    return {"quick_report": scan["quick_report"], "review": review}


def main() -> int:
    query = sys.argv[1] if len(sys.argv) > 1 else "LX Hausys"
    print("=" * 70)
    print(f"Scenario 3 — Investment Review ('{query}', Scenario 2 자동 실행 포함)")
    print("=" * 70)
    run(query, verbose=True)
    print("\nScenario 3 완료.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
