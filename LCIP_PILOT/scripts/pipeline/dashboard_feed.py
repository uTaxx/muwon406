"""Store → Dashboard 연결 — ARTICLE_DB/INTELLIGENCE_DB/COMPANY_SCAN_DB 레코드와 Source
Registry를 Executive Dashboard(6개 Widget, Round 8) 입력 shape으로 변환한다.

Pipeline 8단계(Collect~Store) 자체에는 포함되지 않지만, "Dashboard는 실제 Pipeline
산출물을 반영해야 한다"(Round 8 지시)를 만족시키려면 저장된 레코드를
`scripts/dashboard_widgets.py`가 소비할 수 있는 형태로 넘겨주는 접착 함수가 필요하다.
"""
from __future__ import annotations


def _intelligence_row(intelligence: dict) -> dict:
    return {
        "created_at": (intelligence.get("created_at") or "")[:10],
        "fact_summary": intelligence.get("fact_summary") or "-",
        "confidence": intelligence.get("confidence_score") or "-",
        "source_url": (intelligence.get("evidence") or ["-"])[0],
    }


def _quick_scan_row(scan: dict) -> dict:
    score = scan.get("company_intelligence_score") or {}
    return {
        "target_company": scan.get("target_company") or "-",
        "scan_date": scan.get("scan_date") or "-",
        "confidence": scan.get("confidence") or "-",
        "intelligence_score": score.get("overall", "-"),
    }


def _investment_review_row(scan: dict) -> dict:
    return {
        "target_company": scan.get("target_company") or "-",
        "recommendation_signal": scan.get("recommendation_signal") or "-",
        "scan_date": scan.get("scan_date") or "-",
    }


def _source_health_row(source: dict) -> dict:
    return {
        "source_id": source.get("source_id") or "-",
        "source_name": source.get("source_name") or "-",
        "active": source.get("active", False),
        "historical_stability": source.get("historical_stability") or "-",
    }


def build_dashboard_data(
    *,
    topic_display_name: str,
    generated_at_kst: str,
    articles: list[dict],
    intelligences: list[dict],
    company_scans: list[dict] | None = None,
    sources: list[dict] | None = None,
) -> dict:
    """articles/intelligences/company_scans(Store 단계에서 읽어온 레코드 목록)와
    sources(Source Registry)를 Executive Dashboard 6개 Widget 입력 shape으로 변환한다.

    `articles`는 현재 위젯 어디에도 직접 쓰이지 않지만(Round 8부터 Today's
    Intelligence/Critical Risk/Future Opportunity는 INTELLIGENCE_DB 기준으로 재정의됨),
    호출부(Scenario 1)와의 시그니처 호환을 위해 인자로 남겨둔다.
    """
    company_scans = company_scans or []
    sources = sources or []

    today_intelligence = [_intelligence_row(i) for i in intelligences]
    critical_risk = [
        _intelligence_row(i)
        for i in intelligences
        if "risk_management" in (i.get("mission_category") or [])
    ]
    future_opportunity = [
        _intelligence_row(i)
        for i in intelligences
        if "future_readiness" in (i.get("mission_category") or [])
    ]

    return {
        "generated_at_kst": generated_at_kst,
        "topic_display_name": topic_display_name,
        "today_intelligence": today_intelligence,
        "critical_risk": critical_risk,
        "future_opportunity": future_opportunity,
        "quick_company_scan": [_quick_scan_row(s) for s in company_scans],
        "investment_review": [
            _investment_review_row(s) for s in company_scans if s.get("recommendation_signal")
        ],
        "source_health": [_source_health_row(s) for s in sources],
    }
