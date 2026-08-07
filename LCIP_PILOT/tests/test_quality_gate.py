"""Round 6 — Quality Gate 검증.

Round 6 지시: "Coverage보다 품질 측정으로 전환." 이 테스트는 `scripts/quality_gate.py`가
Knowledge Quality Score/Registry Completion/Public Source Coverage/Source Freshness/
Mock Dependency/Pilot Operational Readiness 6개 지표를 기존 단일 진실 공급원(YAML/기존
모듈)에서 정확히 계산하는지 검증한다.

주의: `quality_gate._readiness_checks()`는 `run_tests=True`일 때 전체 pytest 스위트를
서브프로세스로 재실행한다 — 이 테스트 파일 자체가 그 스위트에 포함되므로, 아래 테스트는
전부 `run_tests=False`로 호출하거나 `_run_full_test_suite`를 monkeypatch해 재귀 실행을
피한다.
"""
from __future__ import annotations

import quality_gate
from _common import load_yaml


def test_knowledge_quality_score_matches_module_average():
    from knowledge_quality import COMPANY_PROFILE_DOCS, score_document

    expected = sum(score_document(f)[0] for f in COMPANY_PROFILE_DOCS) / len(COMPANY_PROFILE_DOCS)
    assert quality_gate.knowledge_quality_score() == expected


def test_knowledge_quality_score_meets_round5_target():
    """Round 5에서 실제로 달성한 평균(95.8%)을 크게 밑돌면 회귀다."""
    assert quality_gate.knowledge_quality_score() >= 90.0


def test_registry_completion_is_between_0_and_100():
    score = quality_gate.registry_completion()
    assert 0.0 <= score <= 100.0


def test_registry_completion_todo_and_null_fields_not_counted_as_filled():
    assert quality_gate._is_filled(None) is False
    assert quality_gate._is_filled("TODO: source required") is False
    assert quality_gate._is_filled("") is False
    assert quality_gate._is_filled([]) is False
    assert quality_gate._is_filled("108670") is True
    assert quality_gate._is_filled(["HIMACS"]) is True


def test_public_source_coverage_is_100_percent():
    """TASK-K03 필수 시스템(Google RSS/Naver/DART/KRX/SEC/EDINET/SEDAR+/Companies House)이
    전부 config/sources.yaml에 등록되어 있어야 한다(tests/test_source_registry.py와 동일 전제)."""
    assert quality_gate.public_source_coverage() == 100.0


def test_source_freshness_matches_active_source_ratio():
    sources = load_yaml("config/sources.yaml")["sources"]
    expected = (sum(1 for s in sources if s.get("active") is True) / len(sources)) * 100
    assert quality_gate.source_freshness() == expected


def test_mock_dependency_is_100_percent_while_all_flags_false():
    """config/feature_flags.yaml은 다음 Architect 승인 전까지 4개 플래그 전부 false다."""
    assert quality_gate.mock_dependency() == 100.0


def test_mock_dependency_drops_when_a_flag_is_true(monkeypatch):
    monkeypatch.setattr(
        quality_gate,
        "load_feature_flags",
        lambda: {"a": True, "b": False, "c": False, "d": False},
    )
    assert quality_gate.mock_dependency() == 75.0


def test_readiness_checks_without_test_suite_run_has_no_recursion(monkeypatch):
    """run_tests=False면 _run_full_test_suite()를 아예 호출하지 않아야 한다(재귀 실행 방지)."""
    calls = []
    monkeypatch.setattr(quality_gate, "_run_full_test_suite", lambda: calls.append(1) or True)

    checks = quality_gate._readiness_checks(run_tests=False)

    assert calls == []
    assert "전체 테스트 스위트 통과" not in checks


def test_readiness_checks_with_run_tests_true_uses_injected_test_suite_result(monkeypatch):
    monkeypatch.setattr(quality_gate, "_run_full_test_suite", lambda: False)

    checks = quality_gate._readiness_checks(run_tests=True)

    assert checks["전체 테스트 스위트 통과"] is False


def test_pilot_operational_readiness_is_percentage_of_passed_checks():
    checks = {"a": True, "b": True, "c": False, "d": True}
    assert quality_gate.pilot_operational_readiness(checks) == 75.0


def test_pilot_operational_readiness_empty_checks_returns_zero():
    assert quality_gate.pilot_operational_readiness({}) == 0.0


def test_build_report_skip_tests_never_invokes_subprocess(monkeypatch):
    calls = []
    monkeypatch.setattr(quality_gate, "_run_full_test_suite", lambda: calls.append(1) or True)

    report = quality_gate.build_report(run_tests=False)

    assert calls == []
    assert isinstance(report, quality_gate.QualityGateReport)
    assert "전체 테스트 스위트 통과" not in report.readiness_checks
    assert 0.0 <= report.pilot_operational_readiness <= 100.0


def test_build_report_all_six_metrics_present(monkeypatch):
    monkeypatch.setattr(quality_gate, "_run_full_test_suite", lambda: True)
    report = quality_gate.build_report(run_tests=False)
    for field in (
        "knowledge_quality_score",
        "registry_completion",
        "public_source_coverage",
        "source_freshness",
        "mock_dependency",
        "pilot_operational_readiness",
    ):
        assert hasattr(report, field)


# --- Round 7 신규 5개 지표 ---


def test_registry_quality_score_is_between_0_and_100():
    assert 0.0 <= quality_gate.registry_quality_score() <= 100.0


def test_registry_quality_score_uses_all_7_registries_structurally():
    """RegistryManager의 7개 Registry 중 하나라도 비어있지 않은 한 구조 점수는 100이어야
    한다(현재 상태 기준 회귀 감시)."""
    from registries import RegistryManager

    summary = RegistryManager().summary()
    assert all(count > 0 for count in summary.values())


def test_report_quality_score_is_100_when_scenarios_succeed():
    """Scenario 2/3가 정상 동작하는 현재 상태에서는 100%여야 한다."""
    assert quality_gate.report_quality_score() == 100.0


def test_report_quality_score_drops_when_a_scenario_raises(monkeypatch):
    """Scenario 3만 실패하도록(Scenario 2는 정상 유지) investment_review 호출부만
    깨뜨려 1/2 = 50%가 나오는지 확인한다."""
    import scenarios.scenario_3_investment_review as s3

    def _raise(*args, **kwargs):
        raise RuntimeError("시뮬레이션된 실패")

    monkeypatch.setattr(s3, "build_investment_review", _raise)
    assert quality_gate.report_quality_score() == 50.0


def test_evidence_quality_score_is_between_0_and_100():
    assert 0.0 <= quality_gate.evidence_quality_score() <= 100.0


def test_evidence_quality_score_averages_knowledge_coverage_and_registry_completion():
    from knowledge_coverage import all_coverage

    coverage_values = list(all_coverage().values())
    expected_knowledge = sum(coverage_values) / len(coverage_values)
    expected = (expected_knowledge + quality_gate.registry_completion()) / 2
    assert quality_gate.evidence_quality_score() == expected


def test_reasoning_quality_score_is_100_for_current_compliant_prompts():
    """risk_analysis.md/policy_analysis.md는 둘 다 confidence/evidence/unknowns를
    요구한다 — 회귀하면 이 테스트가 잡아낸다."""
    assert quality_gate.reasoning_quality_score() == 100.0


def test_reasoning_quality_score_is_a_design_proxy_not_output_measurement():
    """모집단이 risk_analysis/policy_analysis 2개뿐임을 명시적으로 검증 — quick_scan
    등 다른 출력 계약의 프롬프트를 잘못 포함시키지 않았는지 확인."""
    assert quality_gate.REASONING_ANALYSIS_PROMPTS == ["risk_analysis", "policy_analysis"]


def test_maintainability_score_is_between_0_and_100():
    assert 0.0 <= quality_gate.maintainability_score() <= 100.0


def test_maintainability_score_reflects_module_docstring_convention():
    """이 리포지토리는 지금까지 모든 라운드에서 모듈 docstring을 관례로 지켜왔다 —
    큰 폭으로 떨어지면 회귀다."""
    assert quality_gate.maintainability_score() >= 90.0


def test_build_report_includes_all_5_round7_metrics(monkeypatch):
    monkeypatch.setattr(quality_gate, "_run_full_test_suite", lambda: True)
    report = quality_gate.build_report(run_tests=False)
    for field in (
        "registry_quality", "report_quality", "evidence_quality",
        "reasoning_quality", "maintainability",
    ):
        assert hasattr(report, field)
        assert 0.0 <= getattr(report, field) <= 100.0
