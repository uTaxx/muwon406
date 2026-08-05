import pytest

import investment_review as ir
import quick_company_scan as qcs
from providers.mock_provider import MockProvider

PEERS = [
    ir.ComparablePeer("Peer A", ev_ebitda=8.0, per=12.0, pbr=1.5, source_url="https://example.com/peer-a"),
    ir.ComparablePeer("Peer B", ev_ebitda=10.0, per=14.0, pbr=1.7, source_url="https://example.com/peer-b"),
]

QUICK_REPORT_INPUT = {
    "target_company": "LX Hausys",
    "financial_snapshot": [],
    "competitor": ["경쟁사 A"],
    "lx_strategic_fit": "LX 기존 건축자재 사업과 직접 연관",
    "comparable_companies": ["Peer A", "Peer B"],
    "investment_multiple": None,
    "risk_assessment": [],
    "synergy_analysis": ["생산 시너지 가능성"],
    "unknowns": ["재무 수치 미확인"],
    "confidence": "medium",
}


def test_compute_peer_average_computes_mean_of_present_values():
    avg = ir.compute_peer_average(PEERS)
    assert avg["ev_ebitda_avg"] == 9.0
    assert avg["per_avg"] == 13.0
    assert avg["pbr_avg"] == pytest.approx(1.6)
    assert avg["peer_count"] == 2


def test_compute_peer_average_ignores_none_values():
    peers = [ir.ComparablePeer("Peer A", ev_ebitda=None, per=10.0, pbr=None, source_url="https://x")]
    avg = ir.compute_peer_average(peers)
    assert avg["ev_ebitda_avg"] is None
    assert avg["per_avg"] == 10.0


def test_compute_peer_average_empty_list():
    avg = ir.compute_peer_average([])
    assert avg == {"ev_ebitda_avg": None, "per_avg": None, "pbr_avg": None, "peer_count": 0}


def test_detect_deal_killers_finds_keyword_matches():
    report_input = {**QUICK_REPORT_INPUT, "risk_assessment": ["대규모 집단소송 진행 중", "일반적인 시장 리스크"]}
    found, reasons = ir.detect_deal_killers(report_input)
    assert found is True
    assert reasons == ["대규모 집단소송 진행 중"]


def test_detect_deal_killers_no_match():
    found, reasons = ir.detect_deal_killers(QUICK_REPORT_INPUT)
    assert found is False
    assert reasons == []


def test_build_estimated_valuation_returns_none_without_peers():
    avg = ir.compute_peer_average([])
    assert ir.build_estimated_valuation(avg, []) is None


def test_build_estimated_valuation_includes_peer_multiples_not_dollar_amount():
    avg = ir.compute_peer_average(PEERS)
    valuation = ir.build_estimated_valuation(avg, PEERS)
    assert valuation is not None
    assert "EV/EBITDA" in valuation["basis"]
    assert "DCF" in valuation["basis"]
    assert len(valuation["source_urls"]) == 2


def test_determine_recommendation_deal_killer_overrides_everything():
    avg = ir.compute_peer_average(PEERS)
    rec = ir.determine_recommendation(avg, True, ["형사 기소"], "high")
    assert rec["signal"] == "decline_deal_killer_found"


def test_determine_recommendation_no_peers_is_insufficient_information():
    avg = ir.compute_peer_average([])
    rec = ir.determine_recommendation(avg, False, [], "high")
    assert rec["signal"] == "insufficient_public_information"


def test_determine_recommendation_low_confidence_is_monitor():
    avg = ir.compute_peer_average(PEERS)
    rec = ir.determine_recommendation(avg, False, [], "low")
    assert rec["signal"] == "monitor"


def test_determine_recommendation_proceeds_when_peers_and_confidence_ok():
    avg = ir.compute_peer_average(PEERS)
    rec = ir.determine_recommendation(avg, False, [], "medium")
    assert rec["signal"] == "proceed_to_deep_review"


def test_build_investment_review_is_schema_valid():
    review = ir.build_investment_review(QUICK_REPORT_INPUT, PEERS)
    ir.validate_investment_review(review)  # 예외 없이 통과
    assert review["target_company"] == "LX Hausys"
    assert review["peer_average"]["peer_count"] == 2
    assert review["recommendation"]["signal"] == "proceed_to_deep_review"


def test_build_investment_review_without_peers_flags_unknown():
    review = ir.build_investment_review(QUICK_REPORT_INPUT, [])
    assert review["estimated_valuation"] is None
    assert any("Peer" in u for u in review["unknowns"])
    assert review["recommendation"]["signal"] == "insufficient_public_information"


def test_end_to_end_quick_scan_to_investment_review():
    """Quick Company Scan 출력이 Investment Review Engine 입력으로 그대로 이어지는지
    검증한다 (Architect Review Round 5 지시: "Quick Company Scan의 출력을 Investment
    Review Engine 입력으로 연결한다")."""
    registry = qcs.load_company_registry()
    company = qcs.resolve_company_input("LX Hausys", registry)
    result = qcs.generate_company_intelligence(MockProvider(), company, [])
    quick_report = qcs.build_quick_report(company, result)
    review_input = qcs.build_investment_review_input(quick_report)

    review = ir.build_investment_review(review_input, PEERS)
    ir.validate_investment_review(review)
    assert review["target_company"] == "LX Hausys"
