"""Round 8 — Company Intelligence Score 검증."""
from __future__ import annotations

import company_intelligence_score as cis

FULL_REPORT = {
    "target_company": "LX Hausys",
    "scan_date": "2026-08-07",
    "company_overview": "요약",
    "business_structure": ["사업부 A"],
    "product_portfolio": ["HIMACS"],
    "manufacturing": ["Adairsville"],
    "value_chain": "원재료->생산->유통",
    "customer": ["건축사"],
    "competitor": ["Caesarstone"],
    "comparable_companies": ["Caesarstone"],
    "growth_strategy": ["미국 확장"],
    "financial_snapshot": ["매출 X"],
    "investment_multiple": ["EV/EBITDA 9x"],
    "capital_market": "비상장 아님",
    "estimated_valuation": {"basis": "peer"},
    "lx_strategic_fit": "핵심 계열사",
    "synergy_analysis": ["시너지 A"],
    "risk_assessment": ["소송 리스크"],
    "government_exposure": ["OSHA"],
    "reference_sources": ["https://example.com"],
    "unknowns": [],
    "confidence": "medium",
}

EMPTY_REPORT = {
    "target_company": "미등록회사",
    "scan_date": "2026-08-07",
    "company_overview": "",
    "business_structure": [],
    "product_portfolio": [],
    "financial_snapshot": [],
    "competitor": [],
    "lx_strategic_fit": "",
    "reference_sources": [],
    "unknowns": ["미등록"],
    "confidence": "low",
}

SOURCES = [{"source_type": "government_filing"}, {"source_type": "news_rss"}]


def test_compute_score_returns_all_7_subscores():
    score = cis.compute_score("LX_HAUSYS", FULL_REPORT, SOURCES)
    d = score.as_dict()
    for key in (
        "business_understanding", "market_position", "financial_visibility",
        "strategic_importance", "risk_visibility", "source_reliability",
        "knowledge_coverage", "overall",
    ):
        assert key in d
        assert 0.0 <= d[key] <= 100.0


def test_full_report_scores_higher_than_empty_report():
    full = cis.compute_score("LX_HAUSYS", FULL_REPORT, SOURCES)
    empty = cis.compute_score(None, EMPTY_REPORT, [])
    assert full.overall > empty.overall


def test_empty_report_has_zero_business_understanding():
    score = cis.compute_score(None, EMPTY_REPORT, [])
    assert score.business_understanding == 0.0


def test_full_report_has_full_business_understanding():
    score = cis.compute_score("LX_HAUSYS", FULL_REPORT, SOURCES)
    assert score.business_understanding == 100.0


def test_knowledge_coverage_is_zero_for_company_without_knowledge_files():
    """WILSONART는 Round 10 TOP10 Knowledge Population 대상에 포함되지 않아 여전히
    Knowledge 파일이 없다 — Company Registry에는 있지만 COMPANY_KNOWLEDGE_FILES에는
    없는 회사의 정직한 케이스로 쓴다."""
    score = cis.compute_score("WILSONART", FULL_REPORT, SOURCES)
    assert score.knowledge_coverage == 0.0


def test_knowledge_coverage_is_nonzero_for_lx_hausys():
    score = cis.compute_score("LX_HAUSYS", FULL_REPORT, SOURCES)
    assert score.knowledge_coverage > 0.0


def test_knowledge_coverage_is_zero_when_company_id_is_none():
    score = cis.compute_score(None, FULL_REPORT, SOURCES)
    assert score.knowledge_coverage == 0.0


def test_source_reliability_is_zero_with_no_sources():
    score = cis.compute_score("LX_HAUSYS", FULL_REPORT, [])
    assert score.source_reliability == 0.0


def test_source_reliability_uses_source_priority_scores():
    from source_priority import score_for_source_type

    score = cis.compute_score("LX_HAUSYS", FULL_REPORT, SOURCES)
    expected = (
        sum(score_for_source_type(s["source_type"]) for s in SOURCES) / len(SOURCES) / 5
    ) * 100
    assert score.source_reliability == expected


def test_overall_is_average_of_7_subscores():
    score = cis.compute_score("LX_HAUSYS", FULL_REPORT, SOURCES)
    values = [
        score.business_understanding, score.market_position, score.financial_visibility,
        score.strategic_importance, score.risk_visibility, score.source_reliability,
        score.knowledge_coverage,
    ]
    assert score.overall == sum(values) / len(values)
