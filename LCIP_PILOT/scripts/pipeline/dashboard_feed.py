"""Store → Dashboard 연결 — ARTICLE_DB/INTELLIGENCE_DB 레코드를
`dashboard/sample_data.json`과 동일한 shape(dict)으로 변환한다.

8단계 Pipeline(Collect~Store) 자체에는 포함되지 않지만, TASK-017 Pilot MVP 성공 기준
("...Google Sheets 저장 → Dashboard 반영...")을 실제로 만족시키려면 저장된 레코드를
`scripts/dashboard_widgets.py`가 소비할 수 있는 형태로 넘겨주는 접착 함수가 필요하다.
"""
from __future__ import annotations


def _tracker_row(article: dict, intelligence: dict | None) -> dict:
    related_companies = article.get("related_companies") or []
    return {
        "published_at": (article.get("published_at") or "")[:10],
        "region": article.get("country") or "-",
        "title": article.get("title_original") or "-",
        "defendant": related_companies[0] if related_companies else "-",
        "event_type": article.get("event_type") or "-",
        "total_amount_usd": article.get("litigation_amount_total_usd"),
        "claimant_count": article.get("claimant_count"),
        "avg_amount_per_person_usd": article.get("average_amount_per_person_usd"),
        "status": article.get("status") or "-",
        "source_url": article.get("source_url") or "",
        "note": (intelligence or {}).get("fact_summary", ""),
    }


def build_dashboard_data(
    *,
    topic_display_name: str,
    generated_at_kst: str,
    articles: list[dict],
    intelligences: list[dict],
) -> dict:
    """articles/intelligences(둘 다 Store 단계에서 읽어온 레코드 목록)를 대시보드 입력
    JSON(shape)으로 변환한다."""
    intelligence_by_article_id: dict[str, dict] = {}
    for intelligence in intelligences:
        for article_id in intelligence.get("article_ids", []):
            intelligence_by_article_id[article_id] = intelligence

    tracker_rows = [
        _tracker_row(article, intelligence_by_article_id.get(article["article_id"]))
        for article in articles
    ]

    today_changes = [
        f"{article.get('title_original')} ({article.get('source_url')})"
        for article in articles
        if article.get("is_new_change")
    ]

    return {
        "generated_at_kst": generated_at_kst,
        "topic_display_name": topic_display_name,
        "today_changes": today_changes,
        "today_changes_summary": "신규 주요 변화 없음",
        "tracker_rows": tracker_rows,
        "non_us_issues": [],
        "us_state_regulations": [],
        "global_regulations": [],
        "safeguard_news": [],
        "litigation_amount_trend": [],
    }
