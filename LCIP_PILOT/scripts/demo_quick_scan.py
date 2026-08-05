#!/usr/bin/env python3
"""Round 5 — Quick Company Scan → Investment Review 데모 CLI.

Quick Company Scan이 Pilot의 첫 번째 실제 서비스로 승격된 것을 콘솔에서 바로 보여준다:
입력(회사명) → 자동 Source 선택 → Company Intelligence 생성(MockProvider) → Quick
Report(스키마 검증) → Investment Review Engine(Comparable 기반 Valuation + 스크리닝
신호). 전 구간 실제 외부 호출 없음(MockProvider, Comparable Peer 데이터는 데모용 예시).

사용법: python3 scripts/demo_quick_scan.py ["회사명"]
        (인자를 생략하면 config/company_registry.yaml에 등록된 "LX Hausys"로 실행)
"""
from __future__ import annotations

import sys

from _common import load_yaml
from investment_review import ComparablePeer, build_investment_review
from providers.mock_provider import MockProvider
from quick_company_scan import (
    build_investment_review_input,
    build_quick_report,
    generate_company_intelligence,
    resolve_company_input,
    select_sources_for_company,
)

# 데모용 Comparable Peer 예시(공개 배수를 실제로 조회하지 않았음을 명시) — 실제 서비스에서는
# Knowledge Retrieval Engine/외부 데이터로 채워야 한다.
DEMO_PEERS = [
    ComparablePeer("Peer A (예시)", ev_ebitda=8.5, per=13.0, pbr=1.4, source_url="https://example.com/peer-a"),
    ComparablePeer("Peer B (예시)", ev_ebitda=9.5, per=15.0, pbr=1.6, source_url="https://example.com/peer-b"),
]


def step(n: int, title: str) -> None:
    print(f"\n[{n}/6] {title}")


def main() -> int:
    query = sys.argv[1] if len(sys.argv) > 1 else "LX Hausys"

    print("=" * 70)
    print("LCIP Pilot — Quick Company Scan → Investment Review 데모 (Mock 기반)")
    print("=" * 70)
    print(f"입력: '{query}'")

    step(1, "Resolve Company Input — 레지스트리 정규화 (임의 생성 금지)")
    company = resolve_company_input(query)
    print(f"  resolved={company.resolved}  company_id={company.company_id}")
    if not company.resolved:
        print("  주의: config/company_registry.yaml에 등록되지 않은 회사 — 임의로 정보를")
        print("        지어내지 않고 그대로 진행한다(Provider가 unknowns에 정직하게 남김).")

    step(2, "Select Sources — 국가/DART 등록 여부로 자동 선택")
    sources = select_sources_for_company(company)
    for s in sources:
        print(f"  - {s['source_id']}: {s['source_name']} (active={s.get('active')})")

    step(3, "Generate Company Intelligence — Provider 호출 (MockProvider)")
    provider = MockProvider()
    result = generate_company_intelligence(provider, company, sources)
    print(f"  ok={result.ok}")

    step(4, "Build Quick Report — Core 스키마 검증")
    quick_report = build_quick_report(company, result)
    print(f"  target_company={quick_report['target_company']}  scan_date={quick_report['scan_date']}")
    print(f"  confidence={quick_report['confidence']}")

    step(5, "Build Investment Review Input")
    review_input = build_investment_review_input(quick_report)
    print(f"  lx_strategic_fit={review_input['lx_strategic_fit']}")

    step(6, "Investment Review Engine — Comparable 기반 Valuation (DCF 미사용)")
    review = build_investment_review(review_input, DEMO_PEERS)
    print(f"  peer_average: {review['peer_average']}")
    if review["estimated_valuation"]:
        print(f"  estimated_valuation.basis: {review['estimated_valuation']['basis']}")
    print(f"  deal_killer.found: {review['deal_killer']['found']}")
    print(f"  recommendation.signal: {review['recommendation']['signal']}")
    print(f"  recommendation.rationale: {review['recommendation']['rationale']}")

    print("\n" + "=" * 70)
    print("Quick Company Scan → Investment Review 전 단계 정상 동작 (Mock 기반)")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
