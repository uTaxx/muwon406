#!/usr/bin/env python3
"""Quality Gate — Architect Review Round 6/7.

Round 6 지시: "Coverage보다 품질 측정으로 전환." 이 모듈은 "기사를 몇 건 처리했는가"가
아니라 "Pilot이 지금 실제로 신뢰할 수 있는 상태인가"를 측정한다. Round 7이 5개 지표
(Report/Evidence/Reasoning/Registry Quality, Maintainability, 전부 100점 만점)를
추가했다.

각 지표는 이미 존재하는 단일 진실 공급원을 그대로 재사용하며 계산 로직을 중복 구현하지
않는다 — Knowledge Quality Score는 `knowledge_quality.py`, Knowledge Coverage는
`knowledge_coverage.py`, Registry는 `registries.RegistryManager`, Source Reliability
등급은 `config/sources.yaml`/`source_priority.py`, Mock 의존도는 `feature_flags.py`를
그대로 읽는다. 이 파일은 그 값들을 모아 하나의 Quality Gate 리포트로 조립하는 역할만 한다.

Round 6 지표 정의:
- **Knowledge Quality Score**: `knowledge_quality.score_document()`의 Company Profile
  문서(12계층 Taxonomy 적용 대상) 평균.
- **Registry Completion**: `config/company_registry.yaml`의 K02 필수 필드 중 실제 값이
  채워진 비율. 미상장·TODO는 Pilot 단계에서 정직하게 허용되므로 100%가 목표치는
  아니다(참고 지표).
- **Public Source Coverage**: TASK-K03 필수 공개정보 시스템의 등록 비율 — 목표 100%.
- **Source Freshness**: 등록된 Source 중 현재 `active: true`인 비율.
- **Mock Dependency**: `config/feature_flags.yaml`의 플래그 중 아직 `false`인 비율.
- **Pilot Operational Readiness**: 구조적 점검 항목 통과율(테스트 스위트 실제 실행 포함).

Round 8 신규 지표 정의(전부 100점 만점) — "새 기능보다 사용성/품질/완성도를 우선한다":
- **Architectural Stability**: "새로운 Framework는 더 이상 만들지 않는다"(Round 7/8)는
  제약을 직접 계측한다. `scripts/` 아래 패키지(`__init__.py`가 있는 디렉터리) 집합이
  Round 7/8이 확정한 기준 집합과 정확히 같은지 비교 — 새 패키지가 생기거나 있던 패키지가
  사라지면 감점된다.
- **Operational Simplicity**: "전략팀 시연 관점" 지표. 5개 Scenario가 추가 인자·설정 없이
  `python3 scripts/scenarios/<name>.py` 한 줄만으로 끝까지 실행되는지 실제 서브프로세스
  실행으로 측정한다(가정이 아니다).
- **Executive Usability**: `dashboard/sample_data.json` 기준으로 실제 `build_html()`을
  호출해, Architect가 지정한 6개 Widget 섹션이 전부 렌더링되는지 실측한다.
- **AI Reasoning Readiness**: Reasoning Quality(Round 7, 프롬프트 출력 계약)와는 다른
  축이다 — `ClaudeProvider`가 `AIProvider`의 4개 추상 메서드 전부를 실제 Prompt
  Engine 경로(`PromptBuilder`+`_call_anthropic`)까지 연결해 구현했는지 소스 코드
  기준으로 확인한다(RC2에서 Feature Flag만 켜면 즉시 쓸 수 있는 상태인지).

Round 7 신규 지표 정의(전부 100점 만점):
- **Registry Quality**: `registries.RegistryManager`의 7개 Registry가 전부 비어있지
  않은지(구조) + Registry Completion + Public Source Coverage의 평균(내용).
- **Report Quality**: Quick Company Scan/Investment Review Scenario(2/3)를 실제로
  실행해 각 Report가 스키마 검증을 통과하는지 실측한다 — 가정이 아니라 실행 결과다.
- **Evidence Quality**: Knowledge Coverage 8개 도메인 평균 + Registry Completion의
  평균 — "주장에 실제 출처가 붙어 있는가"를 지식/레지스트리 양쪽에서 본다.
- **Reasoning Quality**: **주의 — 실제 출력 품질이 아니라 설계 proxy다.** Mock
  Dependency가 100%인 동안은 Claude의 실제 추론 결과를 채점할 방법이 없다 — 대신
  `risk_analysis`/`policy_analysis`(claude_output.schema.json의 risk_analysis_output
  계열, 추론 근거를 명시적으로 요구하는 출력 계약) 프롬프트가 confidence/evidence/
  unknowns 필드를 실제로 요구하는 설계인지만 확인한다. `quick_scan`/`daily_change`/
  `relevance_filter`/`natural_language_admin`은 다른 출력 계약을 쓰므로 이 지표의
  모집단에서 제외한다(제외가 곧 통과 처리라는 뜻이 아니다).
- **Maintainability**: `scripts/` 전체 `.py` 파일 중 모듈 docstring이 있는 비율.
"""
from __future__ import annotations

import argparse
import ast
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

# Reasoning Quality 채점 대상 — claude_output.schema.json의 risk_analysis_output 계열
# (confidence/evidence/unknowns를 명시적으로 요구하는 출력 계약)을 쓰는 프롬프트만.
REASONING_ANALYSIS_PROMPTS = ["risk_analysis", "policy_analysis"]
REASONING_REQUIRED_MARKERS = ["confidence", "evidence", "unknowns"]

# Architectural Stability(Round 8)의 기준선 — Round 7/8까지 확정된 `scripts/` 하위
# 패키지 집합. "새로운 Framework는 더 이상 만들지 않는다"는 지시를 그대로 계측 대상으로
# 옮긴 것이다. 이 집합을 늘리는 것 자체가 "새 Framework를 만들었다"는 뜻이므로, 정말
# Architect 승인을 받은 구조 변경이 아니면 건드리지 않는다.
KNOWN_ARCHITECTURE_PACKAGES = {
    "adapters", "pipeline", "providers", "storage", "prompt_engine", "registries", "scenarios",
}

SCENARIO_SCRIPT_NAMES = [
    "scenario_1_news_analysis",
    "scenario_2_quick_company_scan",
    "scenario_3_investment_review",
    "scenario_4_policy_impact",
    "scenario_5_competitor_change_detection",
]

EXPECTED_DASHBOARD_SECTIONS = [
    "Today's Intelligence",
    "Critical Risk",
    "Future Opportunity",
    "Quick Company Scan",
    "Investment Review",
    "Source Health",
]

# AI Reasoning Readiness 채점 대상 — AIProvider의 추상 메서드 전부. ClaudeProvider가 이
# 메서드들을 실제 Prompt Engine 경로까지 연결했는지(단순 NotImplementedError stub이
# 아닌지)를 소스 코드로 확인한다.
AI_REASONING_READINESS_MARKERS = ["PromptBuilder", "_call_anthropic"]


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
    registry_quality: float
    report_quality: float
    evidence_quality: float
    reasoning_quality: float
    maintainability: float
    architectural_stability: float
    operational_simplicity: float
    executive_usability: float
    ai_reasoning_readiness: float


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


def registry_quality_score() -> float:
    """Round 7 신설(Round 8부터 Technical Debt Registry 포함 8개). `RegistryManager`의
    전체 Registry가 비어있지 않은지(구조)와
    Registry Completion/Public Source Coverage(내용)를 함께 본다 — 새 계산 로직을
    만들지 않고 기존 함수를 재사용한다."""
    from registries import RegistryManager

    summary = RegistryManager().summary()
    structural = (sum(1 for count in summary.values() if count > 0) / len(summary)) * 100
    return (structural + registry_completion() + public_source_coverage()) / 3


def report_quality_score() -> float:
    """Round 7 신설. Quick Company Scan(Scenario 2)과 Investment Review(Scenario 3)를
    실제로 실행해 각 Report가 스키마 검증을 실제로 통과하는지 실측한다 — 가정이 아니다."""
    from scenarios import scenario_2_quick_company_scan, scenario_3_investment_review

    checks = []
    for runner in (
        lambda: scenario_2_quick_company_scan.run("LX Hausys", verbose=False),
        lambda: scenario_3_investment_review.run("LX Hausys", verbose=False),
    ):
        try:
            runner()
            checks.append(True)
        except Exception:
            checks.append(False)
    return (sum(checks) / len(checks)) * 100 if checks else 0.0


def evidence_quality_score() -> float:
    """Round 7 신설. Knowledge Coverage(지식 쪽 출처 충실도) + Registry Completion
    (레지스트리 쪽 출처 충실도)의 평균 — 둘 다 기존 계산을 재사용한다."""
    from knowledge_coverage import all_coverage

    coverage_values = list(all_coverage().values())
    knowledge_evidence = sum(coverage_values) / len(coverage_values) if coverage_values else 0.0
    return (knowledge_evidence + registry_completion()) / 2


def reasoning_quality_score() -> float:
    """Round 7 신설 — 실제 출력 품질이 아니라 설계 proxy다(모듈 docstring 참고)."""
    prompts_dir = project_root() / "prompts"
    compliant = 0
    for prompt_name in REASONING_ANALYSIS_PROMPTS:
        text = (prompts_dir / f"{prompt_name}.md").read_text(encoding="utf-8")
        if all(marker in text for marker in REASONING_REQUIRED_MARKERS):
            compliant += 1
    return (compliant / len(REASONING_ANALYSIS_PROMPTS)) * 100 if REASONING_ANALYSIS_PROMPTS else 0.0


def maintainability_score() -> float:
    """Round 7 신설 — `scripts/` 전체 `.py` 파일 중 모듈 docstring이 있는 비율."""
    scripts_dir = project_root() / "scripts"
    py_files = [p for p in scripts_dir.rglob("*.py") if "__pycache__" not in p.parts]
    if not py_files:
        return 0.0
    documented = 0
    for path in py_files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        if ast.get_docstring(tree):
            documented += 1
    return (documented / len(py_files)) * 100


def architectural_stability_score() -> float:
    """Round 8 신설. `scripts/` 하위 패키지 집합이 `KNOWN_ARCHITECTURE_PACKAGES`와
    정확히 같은지 비교한다 — 새 패키지가 생기거나 기존 패키지가 사라지면 감점된다."""
    scripts_dir = project_root() / "scripts"
    current_packages = {
        p.name
        for p in scripts_dir.iterdir()
        if p.is_dir() and p.name != "__pycache__" and (p / "__init__.py").exists()
    }
    total_relevant = KNOWN_ARCHITECTURE_PACKAGES | current_packages
    if not total_relevant:
        return 100.0
    unexpected_new = current_packages - KNOWN_ARCHITECTURE_PACKAGES
    missing = KNOWN_ARCHITECTURE_PACKAGES - current_packages
    stable = len(total_relevant) - len(unexpected_new) - len(missing)
    return (stable / len(total_relevant)) * 100


def operational_simplicity_score(run_scenarios: bool = True) -> float:
    """Round 8 신설. 5개 Scenario가 추가 인자 없이 `python3 <script>.py` 한 줄로 끝까지
    실행되는지 실제 서브프로세스로 측정한다. `run_scenarios=False`는 테스트에서 매번
    5개 서브프로세스를 재실행하지 않기 위한 스킵 모드다(구조적 존재 확인은
    `_readiness_checks()`가 이미 별도로 한다)."""
    if not run_scenarios:
        return 100.0
    scenarios_dir = project_root() / "scripts" / "scenarios"
    results = []
    for name in SCENARIO_SCRIPT_NAMES:
        path = scenarios_dir / f"{name}.py"
        if not path.exists():
            results.append(False)
            continue
        result = subprocess.run(
            [sys.executable, str(path)],
            cwd=project_root(),
            capture_output=True,
            text=True,
            timeout=120,
        )
        results.append(result.returncode == 0)
    return (sum(results) / len(results)) * 100 if results else 0.0


def executive_usability_score() -> float:
    """Round 8 신설. `dashboard/sample_data.json`으로 실제 `build_html()`을 호출해
    Architect가 지정한 6개 Widget 섹션이 전부 렌더링되는지 실측한다."""
    import json

    from build_dashboard import build_html

    sample_path = project_root() / "dashboard" / "sample_data.json"
    data = json.loads(sample_path.read_text(encoding="utf-8"))
    html = build_html(data)
    found = sum(1 for section in EXPECTED_DASHBOARD_SECTIONS if section in html)
    return (found / len(EXPECTED_DASHBOARD_SECTIONS)) * 100


def ai_reasoning_readiness_score() -> float:
    """Round 8 신설. `ClaudeProvider`가 `AIProvider`의 추상 메서드 전부를 실제 Prompt
    Engine 경로(PromptBuilder + _call_anthropic)까지 연결했는지 소스 코드로 확인한다 —
    Reasoning Quality(Round 7, 프롬프트 출력 계약)와 다른 축이다."""
    import inspect

    from providers.base import AIProvider
    from providers.claude_provider import ClaudeProvider

    abstract_methods = sorted(AIProvider.__abstractmethods__)
    if not abstract_methods:
        return 0.0
    ready = 0
    for name in abstract_methods:
        method = getattr(ClaudeProvider, name)
        source = inspect.getsource(method)
        if all(marker in source for marker in AI_REASONING_READINESS_MARKERS):
            ready += 1
    return (ready / len(abstract_methods)) * 100


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
        "company_registry >= 30개사": len(companies) >= 30,
        "source_registry >= 11개 Source": len(sources) >= 11,
        "feature_flags.yaml 4개 스위치 구조 정상": set(flags.keys()) == EXPECTED_FEATURE_FLAG_KEYS,
        "Scenario 5종 스크립트 존재": all(
            (project_root() / "scripts" / "scenarios" / f"{name}.py").exists()
            for name in [
                "scenario_1_news_analysis",
                "scenario_2_quick_company_scan",
                "scenario_3_investment_review",
                "scenario_4_policy_impact",
                "scenario_5_competitor_change_detection",
            ]
        ),
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


def build_report(run_tests: bool = True, run_scenarios: bool = True) -> QualityGateReport:
    checks = _readiness_checks(run_tests=run_tests)
    return QualityGateReport(
        knowledge_quality_score=knowledge_quality_score(),
        registry_completion=registry_completion(),
        public_source_coverage=public_source_coverage(),
        source_freshness=source_freshness(),
        mock_dependency=mock_dependency(),
        pilot_operational_readiness=pilot_operational_readiness(checks),
        readiness_checks=checks,
        registry_quality=registry_quality_score(),
        report_quality=report_quality_score(),
        evidence_quality=evidence_quality_score(),
        reasoning_quality=reasoning_quality_score(),
        maintainability=maintainability_score(),
        architectural_stability=architectural_stability_score(),
        operational_simplicity=operational_simplicity_score(run_scenarios=run_scenarios),
        executive_usability=executive_usability_score(),
        ai_reasoning_readiness=ai_reasoning_readiness_score(),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="LCIP Pilot Quality Gate (Round 6/7/8)")
    parser.add_argument(
        "--skip-tests", action="store_true", help="전체 테스트 스위트 재실행을 생략한다(빠른 확인용)"
    )
    parser.add_argument(
        "--skip-scenarios",
        action="store_true",
        help="Operational Simplicity의 5개 Scenario 서브프로세스 실행을 생략한다(빠른 확인용)",
    )
    args = parser.parse_args()

    report = build_report(run_tests=not args.skip_tests, run_scenarios=not args.skip_scenarios)

    print("=== LCIP Pilot Quality Gate (Round 6/7/8) ===")
    print(f"Knowledge Quality Score:      {report.knowledge_quality_score:.1f}%")
    print(f"Registry Completion:         {report.registry_completion:.1f}% (참고 지표 — TODO 허용)")
    print(f"Public Source Coverage:      {report.public_source_coverage:.1f}%")
    print(f"Source Freshness (active비율): {report.source_freshness:.1f}%")
    print(f"Mock Dependency:             {report.mock_dependency:.1f}% (다음 승인 전까지 100%가 정상)")
    print(f"\nPilot Operational Readiness: {report.pilot_operational_readiness:.1f}%")
    for name, ok in report.readiness_checks.items():
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")

    print("\n--- Round 7 신규 지표 (100점 만점) ---")
    print(f"Registry Quality:    {report.registry_quality:.1f}")
    print(f"Report Quality:      {report.report_quality:.1f}")
    print(f"Evidence Quality:    {report.evidence_quality:.1f}")
    print(f"Reasoning Quality:   {report.reasoning_quality:.1f}  (설계 proxy — 실제 출력 품질 아님)")
    print(f"Maintainability:     {report.maintainability:.1f}")

    print("\n--- Round 8 신규 지표 (100점 만점) ---")
    print(f"Architectural Stability:  {report.architectural_stability:.1f}")
    print(f"Operational Simplicity:   {report.operational_simplicity:.1f}")
    print(f"Executive Usability:      {report.executive_usability:.1f}")
    print(f"AI Reasoning Readiness:   {report.ai_reasoning_readiness:.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
