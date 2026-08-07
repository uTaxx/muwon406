"""Store → Dashboard 연결 — ARTICLE_DB/INTELLIGENCE_DB/COMPANY_SCAN_DB 레코드와 Source
Registry를 Executive Dashboard(6개 Widget, Round 8) 입력 shape으로 변환한다.

Pipeline 8단계(Collect~Store) 자체에는 포함되지 않지만, "Dashboard는 실제 Pipeline
산출물을 반영해야 한다"(Round 8 지시)를 만족시키려면 저장된 레코드를
`scripts/dashboard_widgets.py`가 소비할 수 있는 형태로 넘겨주는 접착 함수가 필요하다.

Round 9 지시("Executive가 3분 안에 상황을 이해할 수 있어야 한다"): 새 Widget을 추가하지
않고, 이 접착 함수들이 만드는 dict의 키를 원본 필드명(created_at/fact_summary 등) 대신
사람이 읽는 한글 라벨로 바꿨다 — `render_generic_list()`가 dict의 key를 그대로 테이블
헤더로 쓰기 때문에, 여기서 바꾸는 것만으로 6개 Widget 전부의 가독성이 개선된다(Widget
클래스나 렌더러 코드는 건드리지 않는다). 또한 Scenario를 반복 실행할수록 INTELLIGENCE_DB/
COMPANY_SCAN_DB에 레코드가 계속 쌓여 같은 내용이 수십 건 중복 표시되는 문제(실사용 중
직접 확인함 — Pilot 검증 5번 질문 "가장 불편한 부분"의 근거)를 `_most_recent()`로
최신 N건만 보이게 줄였다 — Storage 자체는 그대로 전체를 남긴다(감사·이력 목적).

Round 11 지시("Home Dashboard 첫 화면에 최근 뉴스도 보여준다", "새 Dashboard Widget은
추가하지 않는다"): 지금까지 `articles`는 인자로만 받고 어떤 Widget도 쓰지 않았다(위
docstring 참고) — 새 Widget 클래스를 만들지 않고, 이미 받고 있던 `articles`를
`recent_news`라는 새 dict 키로 가공해 반환값에 추가했다. `build_dashboard.py`의 Home
섹션이 기존 `render_generic_list()`로 이 값을 직접 렌더링한다(6개 Widget 목록에는
들어가지 않는다).
"""
from __future__ import annotations

MAX_ROWS_PER_WIDGET = 10


def _most_recent(rows: list[dict], limit: int = MAX_ROWS_PER_WIDGET) -> list[dict]:
    """가장 최근에 추가된 것부터 최대 `limit`건만 반환한다. `rows`는 Storage에 append된
    순서(오래된 것 -> 최신)로 들어온다고 가정한다(`LocalJSONLStorage.load_all()`과 동일)."""
    return list(reversed(rows))[:limit]


def _intelligence_row(intelligence: dict) -> dict:
    return {
        "날짜": (intelligence.get("created_at") or "")[:10] or "-",
        "핵심 내용": intelligence.get("fact_summary") or "-",
        "신뢰도": intelligence.get("confidence_score") or "-",
        "출처": (intelligence.get("evidence") or ["-"])[0],
    }


def _quick_scan_row(scan: dict) -> dict:
    score = scan.get("company_intelligence_score") or {}
    overall = score.get("overall")
    return {
        "회사명": scan.get("target_company") or "-",
        "스캔일": scan.get("scan_date") or "-",
        "신뢰도": scan.get("confidence") or "-",
        "종합 점수": f"{overall}/100" if overall is not None else "-",
    }


def _investment_review_row(scan: dict) -> dict:
    return {
        "회사명": scan.get("target_company") or "-",
        "추천 신호": scan.get("recommendation_signal") or "-",
        "검토일": scan.get("scan_date") or "-",
    }


def _source_health_row(source: dict) -> dict:
    return {
        "Source": source.get("source_name") or "-",
        "가동 상태": "가동중" if source.get("active") else "미가동",
        "안정성 참고": source.get("historical_stability") or "-",
    }


def _news_row(article: dict) -> dict:
    return {
        "날짜": (article.get("collected_at") or "")[:10] or "-",
        "제목": article.get("title_original") or "-",
        "출처": article.get("source_url") or "-",
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

    `articles`는 6개 Widget 중 어디에도 쓰이지 않지만(Round 8부터 Today's
    Intelligence/Critical Risk/Future Opportunity는 INTELLIGENCE_DB 기준으로 재정의됨),
    Round 11의 Home Dashboard "최근 뉴스" 섹션이 `recent_news` 키로 그대로 소비한다 —
    AI가 해석한 Intelligence(사실 요약)와 원문 뉴스 목록은 서로 다른 것이라 구분해서
    보여준다.
    """
    company_scans = company_scans or []
    sources = sources or []

    today_intelligence = _most_recent([_intelligence_row(i) for i in intelligences])
    critical_risk = _most_recent([
        _intelligence_row(i)
        for i in intelligences
        if "risk_management" in (i.get("mission_category") or [])
    ])
    future_opportunity = _most_recent([
        _intelligence_row(i)
        for i in intelligences
        if "future_readiness" in (i.get("mission_category") or [])
    ])

    return {
        "generated_at_kst": generated_at_kst,
        "topic_display_name": topic_display_name,
        "today_intelligence": today_intelligence,
        "critical_risk": critical_risk,
        "future_opportunity": future_opportunity,
        "quick_company_scan": _most_recent([_quick_scan_row(s) for s in company_scans]),
        "investment_review": _most_recent([
            _investment_review_row(s) for s in company_scans if s.get("recommendation_signal")
        ]),
        "source_health": [_source_health_row(s) for s in sources],
        "recent_news": _most_recent([_news_row(a) for a in articles]),
    }
