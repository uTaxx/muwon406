import pytest

import quick_company_scan as qcs
from _common import load_yaml
from providers.mock_provider import MockProvider

REGISTRY = qcs.load_company_registry()
SOURCES = load_yaml("config/sources.yaml")["sources"]


@pytest.mark.parametrize("query", ["LX Hausys", "LX하우시스", "lx hausys", "LX_HAUSYS", "LX하우시스"])
def test_resolve_company_input_matches_known_aliases(query):
    company = qcs.resolve_company_input(query, REGISTRY)
    assert company.resolved is True
    assert company.company_id == "LX_HAUSYS"
    assert company.display_name == "LX Hausys"


def test_resolve_company_input_unknown_company_is_not_fabricated():
    company = qcs.resolve_company_input("존재하지 않는 회사 XYZ", REGISTRY)
    assert company.resolved is False
    assert company.company_id is None
    assert company.display_name == "존재하지 않는 회사 XYZ"
    assert company.country is None


def test_select_sources_for_company_kr_dart_company_includes_all_three():
    company = qcs.resolve_company_input("LX Hausys", REGISTRY)
    sources = qcs.select_sources_for_company(company, SOURCES)
    source_ids = {s["source_id"] for s in sources}
    assert source_ids == {"SRC-0001", "SRC-0002", "SRC-0004"}


def test_select_sources_for_company_unresolved_company_gets_global_rss_only():
    company = qcs.resolve_company_input("Unknown Corp", REGISTRY)
    sources = qcs.select_sources_for_company(company, SOURCES)
    source_ids = {s["source_id"] for s in sources}
    assert source_ids == {"SRC-0001"}


def test_generate_company_intelligence_via_mock_provider():
    company = qcs.resolve_company_input("LX Hausys", REGISTRY)
    sources = qcs.select_sources_for_company(company, SOURCES)
    result = qcs.generate_company_intelligence(MockProvider(), company, sources)
    assert result.ok is True
    assert result.parsed_json["target_company"] == "LX Hausys"


def test_build_quick_report_is_schema_valid():
    company = qcs.resolve_company_input("LX Hausys", REGISTRY)
    sources = qcs.select_sources_for_company(company, SOURCES)
    result = qcs.generate_company_intelligence(MockProvider(), company, sources)
    report = qcs.build_quick_report(company, result)
    qcs.validate_quick_report(report)  # 예외 없이 통과해야 한다
    assert report["target_company"] == "LX Hausys"
    assert "scan_date" in report


def test_build_investment_review_input_extracts_expected_fields():
    company = qcs.resolve_company_input("LX Hausys", REGISTRY)
    sources = qcs.select_sources_for_company(company, SOURCES)
    result = qcs.generate_company_intelligence(MockProvider(), company, sources)
    report = qcs.build_quick_report(company, result)
    review_input = qcs.build_investment_review_input(report)
    assert review_input["target_company"] == "LX Hausys"
    assert "financial_snapshot" in review_input
    assert "competitor" in review_input
    assert "confidence" in review_input


def test_end_to_end_quick_scan_pipeline_for_unregistered_company_still_produces_valid_report():
    """미등록 회사도 파이프라인 자체는 끝까지 동작해야 한다 — 다만 Provider가 그 사실을
    unknowns에 정직하게 남긴다(임의 사실 생성 금지)."""
    company = qcs.resolve_company_input("전혀 모르는 회사", REGISTRY)
    assert company.resolved is False
    sources = qcs.select_sources_for_company(company, SOURCES)
    result = qcs.generate_company_intelligence(MockProvider(), company, sources)
    report = qcs.build_quick_report(company, result)
    qcs.validate_quick_report(report)
    assert report["confidence"] == "low"
