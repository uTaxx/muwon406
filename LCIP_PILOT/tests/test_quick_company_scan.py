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


# --- Round 8: Knowledge Retrieval 단계 (Input -> Company Registry -> Knowledge
# Retrieval -> Source Selection -> ...) ---


def test_retrieve_knowledge_for_company_returns_nonempty_for_lx_hausys():
    company = qcs.resolve_company_input("LX Hausys", REGISTRY)
    excerpt = qcs.retrieve_knowledge_for_company(company)
    assert len(excerpt) > 0
    assert "LX_HAUSYS_COMPANY_DNA.md" in excerpt


def test_retrieve_knowledge_for_company_returns_empty_for_company_without_knowledge_files():
    """WILSONART는 Round 10 TOP10 Knowledge Population 대상에 포함되지 않아 여전히
    Knowledge 파일이 없다."""
    company = qcs.resolve_company_input("Wilsonart", REGISTRY)
    assert qcs.retrieve_knowledge_for_company(company) == ""


def test_retrieve_knowledge_for_company_returns_empty_for_unresolved_company():
    company = qcs.resolve_company_input("존재하지 않는 회사 XYZ", REGISTRY)
    assert qcs.retrieve_knowledge_for_company(company) == ""


def test_generate_company_intelligence_passes_knowledge_excerpt_through():
    company = qcs.resolve_company_input("LX Hausys", REGISTRY)
    sources = qcs.select_sources_for_company(company, SOURCES)
    excerpt = qcs.retrieve_knowledge_for_company(company)
    result = qcs.generate_company_intelligence(MockProvider(), company, sources, excerpt)
    assert "Knowledge Base 발췌 없음" not in str(result.parsed_json["unknowns"])


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


def test_export_quick_scan_report_writes_json_and_markdown(tmp_path):
    company = qcs.resolve_company_input("LX Hausys", REGISTRY)
    sources = qcs.select_sources_for_company(company, SOURCES)
    result = qcs.generate_company_intelligence(MockProvider(), company, sources)
    report = qcs.build_quick_report(company, result)
    from investment_review import build_investment_review

    review = build_investment_review(qcs.build_investment_review_input(report), [])
    from company_intelligence_score import compute_score

    score = compute_score(company.company_id, report, sources).as_dict()

    paths = qcs.export_quick_scan_report(company, report, review, score, out_dir=tmp_path)

    assert paths["json_path"].exists()
    assert paths["md_path"].exists()
    import json

    exported = json.loads(paths["json_path"].read_text(encoding="utf-8"))
    assert exported["company_id"] == "LX_HAUSYS"
    assert exported["company_intelligence_score"]["overall"] == score["overall"]
    assert "LX Hausys" in paths["md_path"].read_text(encoding="utf-8")


def test_export_quick_scan_report_also_writes_executive_report_html(tmp_path):
    """Round 11 Priority 3: "Quick Company Scan 결과를 임원 보고용 1~2페이지 요약본으로
    자동 생성한다. HTML 또는 Markdown 둘 중 하나만 지원한다. PDF는 구현하지 않는다."""
    company = qcs.resolve_company_input("LX Hausys", REGISTRY)
    sources = qcs.select_sources_for_company(company, SOURCES)
    result = qcs.generate_company_intelligence(MockProvider(), company, sources)
    report = qcs.build_quick_report(company, result)
    from investment_review import build_investment_review

    review = build_investment_review(qcs.build_investment_review_input(report), [])
    from company_intelligence_score import compute_score

    score = compute_score(company.company_id, report, sources).as_dict()

    paths = qcs.export_quick_scan_report(company, report, review, score, out_dir=tmp_path)

    assert paths["executive_report_path"].exists()
    assert paths["executive_report_path"].suffix == ".html"
    html = paths["executive_report_path"].read_text(encoding="utf-8")
    assert "LX Hausys" in html
    assert f"{score['overall']}/100" in html
    assert review["recommendation"]["signal"] in html
    assert "<!DOCTYPE html>" in html


def test_build_executive_report_html_escapes_and_limits_to_top_3_unknowns():
    quick_report = {
        "target_company": "<Test> Co",
        "scan_date": "2026-08-07",
        "confidence": "low",
        "company_overview": "개요",
        "lx_strategic_fit": "적합성",
        "unknowns": ["미확인1", "미확인2", "미확인3", "미확인4"],
    }
    investment_review = {
        "recommendation": {"signal": "monitor", "rationale": "근거"},
        "deal_killer": {"found": False, "reasons": []},
        "peer_average": {"peer_count": 2},
    }
    intelligence_score = {"overall": 42.3}

    html = qcs.build_executive_report_html(quick_report, investment_review, intelligence_score)

    assert "&lt;Test&gt; Co" in html
    assert "<Test> Co" not in html.replace("&lt;Test&gt; Co", "")
    assert "미확인1" in html and "미확인2" in html and "미확인3" in html
    assert "미확인4" not in html


def test_export_quick_scan_report_markdown_includes_all_core_7_fields(tmp_path):
    """Round 9 지시: "실제 전략팀 직원이 바로 사용할 수 있는가?" — 이전에는 Company
    Overview만 보여줬다. 나머지 Core 필드(Business Structure/Product Portfolio/
    Financial Snapshot/Competitor/LX Strategic Fit/Unknowns/Reference Sources)도
    전부 한 페이지에 나와야 한다."""
    company = qcs.resolve_company_input("LX Hausys", REGISTRY)
    sources = qcs.select_sources_for_company(company, SOURCES)
    result = qcs.generate_company_intelligence(MockProvider(), company, sources)
    report = qcs.build_quick_report(company, result)
    from investment_review import build_investment_review

    review = build_investment_review(qcs.build_investment_review_input(report), [])
    from company_intelligence_score import compute_score

    score = compute_score(company.company_id, report, sources).as_dict()

    paths = qcs.export_quick_scan_report(company, report, review, score, out_dir=tmp_path)
    text = paths["md_path"].read_text(encoding="utf-8")

    for heading in (
        "## Company Overview", "## Business Structure", "## Product Portfolio",
        "## Financial Snapshot", "## Competitor", "## LX Strategic Fit",
        "## Investment Review", "## 확인되지 않은 사항 (Unknowns)", "## 참고 출처 (Reference Sources)",
    ):
        assert heading in text, f"{heading}가 Export Markdown에 없음"


def test_company_registry_has_14_companies_round6_taskk02():
    """Round 6 TASK-K02가 등록한 14개사는 Round 7에서 30개사로 확장된 뒤에도 그대로
    부분집합으로 남아 있어야 한다(기존 등록을 지우지 않았는지 확인)."""
    ids = {c["company_id"] for c in REGISTRY}
    round6_ids = {
        "LX_HOLDINGS", "LX_HAUSYS", "LX_MMA", "LX_SEMICON", "LX_PANTOS", "LX_INTERNATIONAL",
        "KCC", "HANSSEM", "CAESARSTONE", "COSENTINO", "SHAW_INDUSTRIES", "WILSONART",
        "LIXIL", "YKK_AP",
    }
    assert round6_ids <= ids


def test_company_registry_has_30_companies_round7():
    assert len(REGISTRY) == 30
    ids = {c["company_id"] for c in REGISTRY}
    round7_new_ids = {
        "LG_ELECTRONICS", "LG_CHEM", "SAINT_GOBAIN", "AGC", "NSG_GROUP",
        "GUARDIAN_INDUSTRIES", "VITRO", "SCHUCO", "REHAU", "DECEUNINCK", "ANDERSEN",
        "PELLA", "MARVIN", "PPG", "CORNING", "OWENS_CORNING",
    }
    assert round7_new_ids <= ids


def test_lg_electronics_and_lg_chem_are_not_flagged_as_lx_group():
    """LG전자/LG화학은 2021년 LG그룹에서 계열 분리된 LX그룹과는 별개 법인이다 —
    사명 유사성으로 인한 오분류를 방지하는 회귀 테스트."""
    by_id = {c["company_id"]: c for c in REGISTRY}
    assert by_id["LG_ELECTRONICS"]["is_lx_group_company"] is False
    assert by_id["LG_CHEM"]["is_lx_group_company"] is False


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
