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


def test_company_registry_has_14_companies_round6_taskk02():
    assert len(REGISTRY) == 14
    ids = {c["company_id"] for c in REGISTRY}
    assert ids == {
        "LX_HOLDINGS", "LX_HAUSYS", "LX_MMA", "LX_SEMICON", "LX_PANTOS", "LX_INTERNATIONAL",
        "KCC", "HANSSEM", "CAESARSTONE", "COSENTINO", "SHAW_INDUSTRIES", "WILSONART",
        "LIXIL", "YKK_AP",
    }


@pytest.mark.parametrize(
    "company_id,expected_ticker,expected_country",
    [
        ("LX_HOLDINGS", "383800", "KR"),
        ("LX_HAUSYS", "108670", "KR"),
        ("LX_SEMICON", "108320", "KR"),
        ("LX_INTERNATIONAL", "001120", "KR"),
        ("KCC", "002380", "KR"),
        ("HANSSEM", "009240", "KR"),
        ("CAESARSTONE", "CSTE", "IL"),
        ("LIXIL", "5938", "JP"),
    ],
)
def test_company_registry_confirmed_tickers(company_id, expected_ticker, expected_country):
    entry = next(c for c in REGISTRY if c["company_id"] == company_id)
    assert entry["ticker"] == expected_ticker
    assert entry["country"] == expected_country


def test_company_registry_every_entry_has_k02_required_fields():
    """Round 6 TASK-K02: 모든 회사가 Company ID/Ticker/Country/Industry/Products/
    Value Chain/Official Website/Primary Disclosure Source 필드를 갖는다(값이 null/빈
    배열이어도 키 자체는 존재해야 한다 — 확인 안 된 사실은 TODO로 정직하게 표시)."""
    required_keys = {
        "company_id", "ticker", "country", "industry", "products", "value_chain",
        "official_website", "primary_disclosure_source",
    }
    for entry in REGISTRY:
        missing = required_keys - entry.keys()
        assert not missing, f"{entry['company_id']}에 누락된 필드: {missing}"


def test_resolve_company_input_exposes_k02_fields():
    company = qcs.resolve_company_input("LX Hausys", REGISTRY)
    assert company.industry == "건축자재·자동차소재"
    assert "HIMACS(솔리드 서페이스)" in company.products
    assert company.official_website == "https://www.lxhausys.com"
    assert company.primary_disclosure_source is not None


def test_select_sources_for_company_non_kr_company_gets_global_rss_only():
    company = qcs.resolve_company_input("Caesarstone", REGISTRY)
    sources = qcs.select_sources_for_company(company, SOURCES)
    source_ids = {s["source_id"] for s in sources}
    assert source_ids == {"SRC-0001"}


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
