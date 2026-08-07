#!/usr/bin/env python3
"""Scenario 3 — Quick Company Scan 전체 파이프라인 (Architect Review Round 7/8).

Architect Review Round 8이 확정한 전체 순서를 이 Scenario가 끝까지 수행한다:
Input → Company Registry → Knowledge Retrieval → Source Selection(Scenario 2) →
**Financial Provider(Mock)** → Analysis Pipeline(스키마 검증) → Investment Review →
**Dashboard Widget 반영** → **Export**.

Pilot 원칙(Round 8 지시 그대로): Financial Provider만 Mock이고 나머지 단계는 전부
실제 코드다. DCF/LBO/Option은 여전히 Enterprise Backlog — Comparable 기반만 쓴다.

"모든 Scenario는 독립 실행 가능해야 한다"는 지시를 만족시키기 위해 Scenario 2를 내부
호출한다 — 이 스크립트 하나만 실행해도 전체 흐름이 끝까지 돈다.

사용법: python3 scripts/scenarios/scenario_3_investment_review.py ["회사명"]
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _common import project_root
from company_intelligence_score import compute_score
from financial_provider import MockFinancialDataProvider
from investment_review import build_investment_review
from quick_company_scan import export_quick_scan_report
from scenarios import scenario_2_quick_company_scan
from storage.local_jsonl_storage import LocalJSONLStorage

COMPANY_SCAN_DB = "COMPANY_SCAN_DB"


def run(query: str = "LX Hausys", verbose: bool = True) -> dict:
    """Scenario 2(Quick Scan)를 내부 호출해 review_input을 얻은 뒤 Financial
    Provider→Investment Review→Company Intelligence Score→Dashboard Widget 저장→
    Export까지 실행한다. {quick_report, review, intelligence_score, export} 반환."""

    def log(msg: str) -> None:
        if verbose:
            print(msg)

    scan = scenario_2_quick_company_scan.run(query, verbose=verbose)
    company, sources, quick_report = scan["company"], scan["sources"], scan["quick_report"]

    log("\n[6/8] Financial Provider(Mock) — Comparable Peer 조회")
    peers = MockFinancialDataProvider().get_comparable_peers(company.company_id)
    log(f"  Peer {len(peers)}건(전부 예시 데이터 — 실제 재무 데이터 아님)")

    log("[7/8] Investment Review — Comparable 기반 Valuation (DCF 미사용)")
    review = build_investment_review(scan["review_input"], peers)
    log(f"  peer_average: {review['peer_average']}")
    log(f"  deal_killer.found: {review['deal_killer']['found']}")
    log(f"  recommendation.signal: {review['recommendation']['signal']}")

    log("[8/8] Company Intelligence Score")
    score = compute_score(company.company_id, quick_report, sources)
    score_dict = score.as_dict()
    log(f"  overall: {score_dict['overall']}/100")

    log("\nDashboard Widget 반영 — COMPANY_SCAN_DB에 저장")
    # Scenario 1(ARTICLE_DB/INTELLIGENCE_DB)과 동일한 디렉터리를 쓴다 — Executive
    # Dashboard가 두 Scenario의 산출물을 하나의 StorageBackend에서 함께 읽어야 한다.
    storage = LocalJSONLStorage(project_root() / "output" / "pilot_data")
    storage.append(
        COMPANY_SCAN_DB,
        {
            "company_id": company.company_id,
            "target_company": quick_report["target_company"],
            "scan_date": quick_report["scan_date"],
            "scanned_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "confidence": quick_report["confidence"],
            "recommendation_signal": review["recommendation"]["signal"],
            "company_intelligence_score": score_dict,
        },
    )
    log(f"  {COMPANY_SCAN_DB}.jsonl에 1건 추가")

    log("\nExport — JSON/Markdown 산출물 생성")
    export_paths = export_quick_scan_report(company, quick_report, review, score_dict)
    log(f"  {export_paths['json_path']}")
    log(f"  {export_paths['md_path']}")

    return {
        "quick_report": quick_report,
        "review": review,
        "intelligence_score": score_dict,
        "export": export_paths,
    }


def main() -> int:
    query = sys.argv[1] if len(sys.argv) > 1 else "LX Hausys"
    print("=" * 70)
    print(f"Scenario 3 — Quick Company Scan 전체 파이프라인 ('{query}', Scenario 2 자동 실행 포함)")
    print("=" * 70)
    run(query, verbose=True)
    print("\nScenario 3 완료.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
