#!/usr/bin/env python3
"""Quality Gate — Architect Review Round 6.

Round 6 지시: "Coverage보다 품질 측정으로 전환." 이 모듈은 "기사를 몇 건 처리했는가"가
아니라 "Pilot이 지금 실제로 신뢰할 수 있는 상태인가"를 6개 지표로 측정한다.

각 지표는 이미 존재하는 단일 진실 공급원을 그대로 재사용하며 계산 로직을 중복 구현하지
않는다 — Knowledge Quality Score는 `knowledge_quality.py`, Source Reliability 등급은
`config/sources.yaml`/`source_priority.py`, Mock 의존도는 `feature_flags.py`를 그대로
읽는다. 이 파일은 그 값들을 모아 하나의 Quality Gate 리포트로 조립하는 역할만 한다.

지표 정의:
- **Knowledge Quality Score**: `knowledge_quality.score_document()`의 Company Profile
  문서(12계층 Taxonomy 적용 대상) 평균 — 기존 Round 5 정의 그대로.
- **Registry Completion**: `config/company_registry.yaml`의 K02 필수 필드
  (ticker/industry/products/value_chain/official_website/primary_disclosure_source)
  중 실제 값이 채워진(= null도 아니고 "TODO: source required"도 아닌) 비율. 미상장·TODO는
  Pilot 단계에서 정직하게 허용되므로 100%가 목표치는 아니다(참고 지표).
- **Public Source Coverage**: TASK-K03이 요구한 필수 공개정보 시스템
  (Google RSS/Naver/DART/KRX/SEC/EDINET/SEDAR+/Companies House)이 `config/sources.yaml`에
  전부 등록되어 있는지의 비율 — 목표 100%.
- **Source Freshness**: 등록된 Source 중 현재 `active: true`(실제로 살아있는 수집 대상)인
  비율. Public Source Coverage("등록은 됐는가")와 달리 "지금 당장 신선한 데이터를 가져올
  수 있는가"를 측정한다 — 두 지표를 하나로 합치면 "등록만 되어 있고 꺼져 있는 상태"를
  가릴 수 있어 의도적으로 분리했다.
- **Mock Dependency**: `config/feature_flags.yaml`의 플래그 중 아직 `false`인 비율 —
  다음 Architect 승인 전까지는 100%가 정상이며 "낮아져야 좋은" 지표가 아니라 "현재 상태를
  숨기지 않고 드러내는" 지표다.
- **Pilot Operational Readiness**: 아래 `_readiness_checks()`의 구조적 점검 항목 통과율.
  임의의 목표 수치가 아니라 리포지토리에 실제로 존재하는 파일/설정/테스트 결과를 그대로
  확인한다(테스트 스위트는 실제로 실행해 통과 여부를 본다 — 임의 판정 없음).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass

from _common import load_yaml, project_root
from feature_flags import load_feature_flags
from knowledge_quality import COMPANY_PROFILE_DOCS, score_document

REQUIRED_COMPANY_FIELDS = [
    "ticker",
    "industry",
    "products",
    "value_chain",
    "official_website",
    "primary_disclosure_source",
]

# TASK-K03이 지정한 필수 시스템 — tests/test_source_registry.py와 동일한 목록.
REQUIRED_SOURCE_SYSTEMS = [
    "Google News RSS",
    "Naver",
    "DART",
    "KRX",
    "SEC EDGAR",
    "EDINET",
    "SEDAR",
    "Companies House",
]

EXPECTED_FEATURE_FLAG_KEYS = {
    "real_network_calls",
    "claude_api_enabled",
    "google_sheets_enabled",
    "notification_send_enabled",
}


def _is_filled(value) -> bool:
    """null / 빈 리스트 / "TODO: source required" 계열 placeholder는 미확인으로 취급한다."""
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != "" and not value.strip().upper().startswith("TODO")
    if isinstance(value, list):
        return len(value) > 0
    return True


@dataclass(frozen=True)
class QualityGateReport:
    knowledge_quality_score: float
    registry_completion: float
    public_source_coverage: float
    source_freshness: float
    mock_dependency: float
    pilot_operational_readiness: float
    readiness_checks: dict[str, bool]


def knowledge_quality_score() -> float:
    scores = [score_document(filename)[0] for filename in COMPANY_PROFILE_DOCS]
    return sum(scores) / len(scores) if scores else 0.0


def registry_completion() -> float:
    companies = load_yaml("config/company_registry.yaml")["companies"]
    if not companies:
        return 0.0
    filled = sum(
        1
        for company in companies
        for field in REQUIRED_COMPANY_FIELDS
        if _is_filled(company.get(field))
    )
    total = len(companies) * len(REQUIRED_COMPANY_FIELDS)
    return (filled / total) * 100 if total else 0.0


def public_source_coverage() -> float:
    sources = load_yaml("config/sources.yaml")["sources"]
    names = {s["source_name"] for s in sources}
    matched = sum(
        1 for required in REQUIRED_SOURCE_SYSTEMS if any(required in n for n in names)
    )
    return (matched / len(REQUIRED_SOURCE_SYSTEMS)) * 100


def source_freshness() -> float:
    sources = load_yaml("config/sources.yaml")["sources"]
    if not sources:
        return 0.0
    active_count = sum(1 for s in sources if s.get("active") is True)
    return (active_count / len(sources)) * 100


def mock_dependency() -> float:
    flags = load_feature_flags()
    if not flags:
        return 100.0
    still_mocked = sum(1 for value in flags.values() if value is False)
    return (still_mocked / len(flags)) * 100


def _run_full_test_suite() -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=project_root(),
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _readiness_checks(run_tests: bool = True) -> dict[str, bool]:
    companies = load_yaml("config/company_registry.yaml")["companies"]
    sources = load_yaml("config/sources.yaml")["sources"]
    flags = load_feature_flags()
    checks = {
        "knowledge_quality_score >= 90%": knowledge_quality_score() >= 90.0,
        "public_source_coverage == 100%": public_source_coverage() == 100.0,
        "company_registry >= 14개사": len(companies) >= 14,
        "source_registry >= 11개 Source": len(sources) >= 11,
        "feature_flags.yaml 4개 스위치 구조 정상": set(flags.keys()) == EXPECTED_FEATURE_FLAG_KEYS,
        "통합 데모(scripts/demo_pilot.py) 존재": (project_root() / "scripts" / "demo_pilot.py").exists(),
    }
    # 이 함수 자체가 tests/test_quality_gate.py에서 실행되므로, run_tests=True로 pytest를
    # 서브프로세스로 재귀 호출하면 스스로를 무한히 다시 실행하게 된다 — CLI(`--skip-tests`
    # 미지정 시 기본 True)에서만 켜고, 테스트 코드에서는 반드시 run_tests=False로 호출한다.
    if run_tests:
        checks["전체 테스트 스위트 통과"] = _run_full_test_suite()
    return checks


def pilot_operational_readiness(readiness_checks: dict[str, bool]) -> float:
    if not readiness_checks:
        return 0.0
    passed = sum(1 for ok in readiness_checks.values() if ok)
    return (passed / len(readiness_checks)) * 100


def build_report(run_tests: bool = True) -> QualityGateReport:
    checks = _readiness_checks(run_tests=run_tests)
    return QualityGateReport(
        knowledge_quality_score=knowledge_quality_score(),
        registry_completion=registry_completion(),
        public_source_coverage=public_source_coverage(),
        source_freshness=source_freshness(),
        mock_dependency=mock_dependency(),
        pilot_operational_readiness=pilot_operational_readiness(checks),
        readiness_checks=checks,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="LCIP Pilot Quality Gate (Round 6)")
    parser.add_argument(
        "--skip-tests", action="store_true", help="전체 테스트 스위트 재실행을 생략한다(빠른 확인용)"
    )
    args = parser.parse_args()

    report = build_report(run_tests=not args.skip_tests)

    print("=== LCIP Pilot Quality Gate (Round 6) ===")
    print(f"Knowledge Quality Score:      {report.knowledge_quality_score:.1f}%")
    print(f"Registry Completion:         {report.registry_completion:.1f}% (참고 지표 — TODO 허용)")
    print(f"Public Source Coverage:      {report.public_source_coverage:.1f}%")
    print(f"Source Freshness (active비율): {report.source_freshness:.1f}%")
    print(f"Mock Dependency:             {report.mock_dependency:.1f}% (다음 승인 전까지 100%가 정상)")
    print(f"\nPilot Operational Readiness: {report.pilot_operational_readiness:.1f}%")
    for name, ok in report.readiness_checks.items():
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
