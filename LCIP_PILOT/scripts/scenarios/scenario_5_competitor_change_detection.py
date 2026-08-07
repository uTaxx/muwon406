#!/usr/bin/env python3
"""Scenario 5 — 경쟁사 변화 감지 (Architect Review Round 7 신설).

Pilot은 아직 시계열 이력을 쌓아본 적이 없다(Round 6까지 전 구간 Mock/dry-run, 실제 정기
수집 없음) — 그래서 "변화를 감지한다"는 것은 매번 Quick Company Scan(Scenario 2)을 돌려
스냅샷을 저장하고, 직전 스냅샷이 있으면 핵심 필드를 비교하는 것으로 정직하게 구현한다.
처음 실행하는 회사는 "최초 스냅샷"이라고 있는 그대로 보고하며, 변화가 있었다고 지어내지
않는다.

주의: `providers.factory.get_default_provider()`가 현재 MockProvider로 귀결되는 동안은
매 실행마다 Mock 응답이 달라질 수 있어(mock_provider는 결정론적이지만 quick_scan_date
등 일부 필드는 실행 시각에 따라 변함) "변화 감지"가 실제 시장 변화를 반영하지 않는다 —
Connection Readiness(Round 7 항목 51) 완료 후 실제 데이터로 의미가 생긴다.

사용법: python3 scripts/scenarios/scenario_5_competitor_change_detection.py [회사명 ...]
        (인자를 생략하면 config/company_registry.yaml의 경쟁사 중 CAESARSTONE/COSENTINO)
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _common import project_root
from scenarios import scenario_2_quick_company_scan

DEFAULT_COMPETITORS = ["CAESARSTONE", "COSENTINO"]
SNAPSHOT_FIELDS = ["company_overview", "competitor", "lx_strategic_fit", "confidence"]


def _snapshot_dir() -> Path:
    d = project_root() / "output" / "scenario_5_competitor_change_detection"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _latest_snapshot_path(company_query: str) -> Path:
    safe_name = company_query.strip().replace(" ", "_").upper()
    return _snapshot_dir() / f"{safe_name}_latest.json"


def _diff_fields(previous: dict, current: dict) -> list[str]:
    return [field for field in SNAPSHOT_FIELDS if previous.get(field) != current.get(field)]


def run(company_query: str, verbose: bool = True) -> dict:
    """단일 회사에 대해 스냅샷을 갱신하고 변화 여부를 반환한다."""

    def log(msg: str) -> None:
        if verbose:
            print(msg)

    log(f"\n[Scenario 5] '{company_query}' 스냅샷 생성 (Scenario 2 재사용)")
    scan = scenario_2_quick_company_scan.run(company_query, verbose=False)
    quick_report = scan["quick_report"]

    path = _latest_snapshot_path(company_query)
    previous = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

    result = {
        "company_query": company_query,
        "company_id": scan["company"].company_id,
        "snapshot_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if previous is None:
        result["is_first_snapshot"] = True
        result["changed_fields"] = []
        log("  최초 스냅샷 — 비교 대상 없음(변화 감지는 다음 실행부터 가능)")
    else:
        changed_fields = _diff_fields(previous, quick_report)
        result["is_first_snapshot"] = False
        result["changed_fields"] = changed_fields
        if changed_fields:
            log(f"  변화 감지: {changed_fields}")
        else:
            log("  변화 없음(직전 스냅샷과 동일)")

    path.write_text(json.dumps(quick_report, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> int:
    companies = sys.argv[1:] or DEFAULT_COMPETITORS
    print("=" * 70)
    print(f"Scenario 5 — 경쟁사 변화 감지 ({', '.join(companies)})")
    print("=" * 70)
    for company_query in companies:
        run(company_query, verbose=True)
    print("\nScenario 5 완료.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
