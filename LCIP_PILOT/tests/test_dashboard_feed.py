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
            "target_company": f"Company {n}",
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


def test_quick_company_scan_dedupes_repeated_same_company_scans():
    """Round 12 TASK 1(TD-006) 완료조건: "같은 회사 반복 실행 시 무한 중복 누적하지
    않는다." 같은 회사를 14번 스캔해도 위젯에는 가장 최근 스캔 1건만 남아야 한다."""
    scans = [
        {
            "target_company": "LX Hausys",
            "scan_date": f"2026-08-{n:02d}",
            "confidence": "low",
            "recommendation_signal": "monitor",
            "company_intelligence_score": {"overall": float(n)},
        }
        for n in range(1, 15)
    ]
    data = build_dashboard_data(
        topic_display_name="Topic", generated_at_kst="2026-08-07 09:00",
        articles=[], intelligences=[], company_scans=scans,
    )
    assert len(data["quick_company_scan"]) == 1
    assert data["quick_company_scan"][0]["스캔일"] == "2026-08-14"  # 가장 마지막 스캔만 남는다
    assert len(data["investment_review"]) == 1


def test_quick_company_scan_dedup_keeps_multiple_distinct_companies():
    scans = [
        {"target_company": "LX Hausys", "scan_date": "2026-08-01", "confidence": "low",
         "recommendation_signal": "monitor", "company_intelligence_score": {"overall": 42.3}},
        {"target_company": "LX Hausys", "scan_date": "2026-08-02", "confidence": "low",
         "recommendation_signal": "monitor", "company_intelligence_score": {"overall": 43.0}},
        {"target_company": "KCC", "scan_date": "2026-08-03", "confidence": "low",
         "recommendation_signal": "monitor", "company_intelligence_score": {"overall": 45.0}},
    ]
    data = build_dashboard_data(
        topic_display_name="Topic", generated_at_kst="2026-08-07 09:00",
        articles=[], intelligences=[], company_scans=scans,
    )
    companies = {row["회사명"] for row in data["quick_company_scan"]}
    assert companies == {"LX Hausys", "KCC"}
    lx_row = next(r for r in data["quick_company_scan"] if r["회사명"] == "LX Hausys")
    assert lx_row["스캔일"] == "2026-08-02"


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


def _article(n: int) -> dict:
    return {
        "collected_at": f"2026-08-{n:02d}T00:00:00Z",
        "title_original": f"뉴스 제목 {n}",
        "source_url": f"https://example.com/news/{n}",
    }


def test_recent_news_row_uses_korean_labels_and_is_capped():
    """Round 11 지시: Home Dashboard '최근 뉴스' 섹션 — 새 Widget 없이 기존 articles
    인자를 recent_news 키로 가공한다."""
    articles = [_article(n) for n in range(1, 15)]
    data = build_dashboard_data(
        topic_display_name="Topic", generated_at_kst="2026-08-07 09:00",
        articles=articles, intelligences=[],
    )
    assert len(data["recent_news"]) == MAX_ROWS_PER_WIDGET
    assert set(data["recent_news"][0].keys()) == {"날짜", "제목", "출처"}
    # 가장 마지막에 추가된(14번) 기사가 맨 위(최신)로 와야 한다.
    assert data["recent_news"][0]["제목"] == "뉴스 제목 14"


def test_recent_news_empty_when_no_articles():
    data = build_dashboard_data(
        topic_display_name="Topic", generated_at_kst="2026-08-07 09:00",
        articles=[], intelligences=[],
    )
    assert data["recent_news"] == []


def test_reference_library_rows_empty_when_summary_missing():
    """Round 12 TASK 2: reference_library_summary를 넘기지 않아도(기본 None) 정직하게
    빈 카드가 되어야 한다."""
    data = build_dashboard_data(
        topic_display_name="Topic", generated_at_kst="2026-08-07 09:00",
        articles=[], intelligences=[],
    )
    assert data["reference_library_rows"] == []


def test_reference_library_rows_summarizes_top_companies_and_counts():
    summary = {
        "total": 5,
        "by_company": {"LX_HAUSYS": 3, "KCC": 2},
        "latest_title": "최신 문서",
        "official_count": 4,
    }
    data = build_dashboard_data(
        topic_display_name="Topic", generated_at_kst="2026-08-07 09:00",
        articles=[], intelligences=[], reference_library_summary=summary,
    )
    rows = data["reference_library_rows"]
    assert len(rows) == 1
    assert rows[0]["등록 자료 수"] == "5건"
    assert rows[0]["회사별 자료 수(상위)"] == "LX_HAUSYS 3건, KCC 2건"
    assert rows[0]["최신 자료"] == "최신 문서"
    assert rows[0]["공식자료 수"] == "4건"


def test_keyword_groups_summary_empty_when_not_provided():
    """뉴스 수집 실체화 라운드 신설 — keyword_groups를 넘기지 않아도(기본 None) 정직하게
    빈 카드가 되어야 한다."""
    data = build_dashboard_data(
        topic_display_name="Topic", generated_at_kst="2026-08-07 09:00",
        articles=[], intelligences=[],
    )
    assert data["keyword_groups_summary"] == []


def test_keyword_groups_summary_renders_group_fields():
    groups = [{
        "group_id": "GRP-0001", "topic_id": "TOP-0001",
        "group_name": "실리코시스", "include_keywords": ["a", "b", "c"],
        "exclude_keywords": [], "ai_instructions": "", "sources": ["SRC-0001", "SRC-0003"],
        "enabled": True,
    }]
    data = build_dashboard_data(
        topic_display_name="Topic", generated_at_kst="2026-08-07 09:00",
        articles=[], intelligences=[], keyword_groups=groups,
    )
    rows = data["keyword_groups_summary"]
    assert len(rows) == 1
    assert rows[0]["그룹명"] == "실리코시스"
    assert rows[0]["포함 키워드 수"] == 3
    assert rows[0]["소스"] == "SRC-0001, SRC-0003"
    assert rows[0]["상태"] == "활성"
