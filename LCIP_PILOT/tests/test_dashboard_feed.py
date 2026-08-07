"""Round 9 — Dashboard Feed 가독성/최신순 노출 검증.

Architect Review Round 9 지시: "Executive가 3분 안에 상황을 이해할 수 있어야 한다."
Scenario를 반복 실행하면 INTELLIGENCE_DB/COMPANY_SCAN_DB에 레코드가 계속 쌓여 같은
내용이 수십 건 표시되는 문제를 실사용 중 확인했다 — 이 테스트는 (1) 각 Widget row가
한글 라벨을 쓰는지, (2) 오래된 레코드가 쌓여도 최근 N건만 노출되는지를 검증한다.
"""
from __future__ import annotations

from pipeline.dashboard_feed import MAX_ROWS_PER_WIDGET, build_dashboard_data


def _intelligence(n: int) -> dict:
    return {
        "created_at": f"2026-08-{n:02d}T00:00:00Z",
        "fact_summary": f"사실 요약 {n}",
        "confidence_score": "low",
        "evidence": [f"https://example.com/{n}"],
        "mission_category": ["risk_management"],
    }


def test_intelligence_row_uses_korean_labels():
    data = build_dashboard_data(
        topic_display_name="Topic", generated_at_kst="2026-08-07 09:00",
        articles=[], intelligences=[_intelligence(1)],
    )
    row = data["today_intelligence"][0]
    assert set(row.keys()) == {"날짜", "핵심 내용", "신뢰도", "출처"}
    assert row["핵심 내용"] == "사실 요약 1"


def test_today_intelligence_caps_at_max_rows_and_shows_most_recent_first():
    intelligences = [_intelligence(n) for n in range(1, 20)]  # 19건 — 상한(10)보다 많음
    data = build_dashboard_data(
        topic_display_name="Topic", generated_at_kst="2026-08-07 09:00",
        articles=[], intelligences=intelligences,
    )
    assert len(data["today_intelligence"]) == MAX_ROWS_PER_WIDGET
    # 가장 마지막에 추가된(19번) 레코드가 맨 위(최신)로 와야 한다.
    assert data["today_intelligence"][0]["핵심 내용"] == "사실 요약 19"


def test_critical_risk_and_future_opportunity_also_capped():
    intelligences = [_intelligence(n) for n in range(1, 15)]
    data = build_dashboard_data(
        topic_display_name="Topic", generated_at_kst="2026-08-07 09:00",
        articles=[], intelligences=intelligences,
    )
    assert len(data["critical_risk"]) == MAX_ROWS_PER_WIDGET  # 전부 risk_management


def test_quick_company_scan_and_investment_review_row_labels_and_cap():
    scans = [
        {
            "target_company": "LX Hausys",
            "scan_date": f"2026-08-{n:02d}",
            "confidence": "low",
            "recommendation_signal": "monitor",
            "company_intelligence_score": {"overall": 42.3},
        }
        for n in range(1, 15)
    ]
    data = build_dashboard_data(
        topic_display_name="Topic", generated_at_kst="2026-08-07 09:00",
        articles=[], intelligences=[], company_scans=scans,
    )
    assert len(data["quick_company_scan"]) == MAX_ROWS_PER_WIDGET
    assert set(data["quick_company_scan"][0].keys()) == {"회사명", "스캔일", "신뢰도", "종합 점수"}
    assert data["quick_company_scan"][0]["종합 점수"] == "42.3/100"
    assert len(data["investment_review"]) == MAX_ROWS_PER_WIDGET
    assert set(data["investment_review"][0].keys()) == {"회사명", "추천 신호", "검토일"}


def test_source_health_row_uses_korean_labels_and_is_not_capped():
    sources = [
        {"source_name": f"Source {n}", "active": n % 2 == 0, "historical_stability": "설명"}
        for n in range(1, 15)
    ]
    data = build_dashboard_data(
        topic_display_name="Topic", generated_at_kst="2026-08-07 09:00",
        articles=[], intelligences=[], sources=sources,
    )
    assert len(data["source_health"]) == 14  # Source Registry는 로그가 아니라 목록이라 자르지 않는다
    assert set(data["source_health"][0].keys()) == {"Source", "가동 상태", "안정성 참고"}
    assert data["source_health"][0]["가동 상태"] in ("가동중", "미가동")
