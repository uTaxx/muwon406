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
