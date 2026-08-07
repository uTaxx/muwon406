#!/usr/bin/env python3
"""Scenario 2 — Quick Company Scan (Architect Review Round 5/7/8).

Architect Review Round 8이 확정한 순서를 그대로 따른다:
Input → Company Registry → **Knowledge Retrieval** → Source Selection → Provider 호출
(Company Intelligence) → Quick Report(스키마 검증). 다른 Scenario에 의존하지 않고
단독으로 실행된다(Scenario 3이 이 모듈의 `run()`을 재사용해 Financial Provider/
Investment Review/Dashboard Widget/Export까지 이어간다).

사용법: python3 scripts/scenarios/scenario_2_quick_company_scan.py ["회사명"]
        (인자를 생략하면 "LX Hausys")
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from providers.factory import get_default_provider
from quick_company_scan import (
    build_investment_review_input,
    build_quick_report,
    generate_company_intelligence,
    resolve_company_input,
    retrieve_knowledge_for_company,
    select_sources_for_company,
)


def run(query: str = "LX Hausys", verbose: bool = True) -> dict:
    """Scenario 2를 실행하고 {company, sources, quick_report, review_input}을 반환한다."""

    def log(msg: str) -> None:
        if verbose:
            print(msg)

    provider = get_default_provider()
    log(f"[Scenario 2] Provider: {type(provider).__name__}")

    log(f"\n[1/5] Resolve Company Input ('{query}') — Company Registry")
    company = resolve_company_input(query)
    log(f"  resolved={company.resolved}  company_id={company.company_id}")
    if not company.resolved:
        log("  주의: config/company_registry.yaml에 등록되지 않은 회사 — 임의로 정보를")
        log("        지어내지 않고 그대로 진행한다.")

    log("[2/5] Knowledge Retrieval")
    knowledge_excerpt = retrieve_knowledge_for_company(company)
    log(f"  발췌 길이: {len(knowledge_excerpt)}자"
        + ("" if knowledge_excerpt else " (등록된 Knowledge 파일 없음 — 정직하게 빈 값)"))

    log("[3/5] Select Sources")
    sources = select_sources_for_company(company)
    for s in sources:
        log(f"  - {s['source_id']}: {s['source_name']} (active={s.get('active')})")

    log("[4/5] Generate Company Intelligence")
    result = generate_company_intelligence(provider, company, sources, knowledge_excerpt)
    log(f"  ok={result.ok}")

    log("[5/5] Build Quick Report")
    quick_report = build_quick_report(company, result)
    log(f"  target_company={quick_report['target_company']}  confidence={quick_report['confidence']}")

    review_input = build_investment_review_input(quick_report)
    return {
        "company": company,
        "sources": sources,
        "quick_report": quick_report,
        "review_input": review_input,
    }


def main() -> int:
    query = sys.argv[1] if len(sys.argv) > 1 else "LX Hausys"
    print("=" * 70)
    print(f"Scenario 2 — Quick Company Scan ('{query}')")
    print("=" * 70)
    run(query, verbose=True)
    print("\nScenario 2 완료.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
