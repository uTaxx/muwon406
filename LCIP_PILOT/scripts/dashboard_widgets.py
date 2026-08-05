"""TASK-012 — Widget 기반 대시보드 구성 요소.

Round 4 지시: "대시보드는 오늘의 주요변화/리스크 Tracker/소송/규제/통계/타임라인을 독립적으로
추가·제거 가능한 Widget 클래스로 구성한다." 각 Widget은 `render_dashboard.data`(dict)를
입력받아 자신이 담당하는 템플릿 토큰 하나를 채우는 HTML 조각만 반환한다 — 서로 의존하지
않으므로 `DEFAULT_WIDGETS` 목록에서 순서를 바꾸거나 항목을 빼고 넣어도 나머지 Widget은
영향받지 않는다.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from html import escape

NUM_FIELDS = {"total_amount_usd", "claimant_count", "avg_amount_per_person_usd"}


def _fmt_num(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return f"{value:,}"


def render_tracker_rows(rows: list[dict]) -> str:
    if not rows:
        return '        <tr><td colspan="11" class="lcip-empty">등록된 Tracker 항목 없음</td></tr>'
    out = []
    for r in rows:
        out.append(
            "        <tr>"
            f"<td>{escape(r.get('published_at') or '-')}</td>"
            f"<td>{escape(r.get('region') or '-')}</td>"
            f"<td>{escape(r.get('title') or '-')}</td>"
            f"<td>{escape(r.get('defendant') or '-')}</td>"
            f"<td>{escape(r.get('event_type') or '-')}</td>"
            f"<td class=\"lcip-num\">{_fmt_num(r.get('total_amount_usd'))}</td>"
            f"<td class=\"lcip-num\">{_fmt_num(r.get('claimant_count'))}</td>"
            f"<td class=\"lcip-num\">{_fmt_num(r.get('avg_amount_per_person_usd'))}</td>"
            f"<td>{escape(r.get('status') or '-')}</td>"
            f"<td><a href=\"{escape(r.get('source_url') or '#')}\" target=\"_blank\" rel=\"noopener\">원문 보기</a></td>"
            f"<td>{escape(r.get('note') or '')}</td>"
            "</tr>"
        )
    return "\n".join(out)


def render_generic_list(items: list[dict], empty_label: str) -> str:
    if not items:
        return f'<p class="lcip-empty">{escape(empty_label)}</p>'
    rows = []
    for item in items:
        cols = "".join(f"<td>{escape(str(v))}</td>" for v in item.values())
        rows.append(f"<tr>{cols}</tr>")
    headers = "".join(f"<th>{escape(k)}</th>" for k in items[0].keys())
    return (
        '<table class="lcip-table"><thead><tr>'
        + headers
        + "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def render_today_changes(data: dict) -> str:
    changes = data.get("today_changes") or []
    if not changes:
        return escape(data.get("today_changes_summary") or "신규 주요 변화 없음")
    return "<ul>" + "".join(f"<li>{escape(str(c))}</li>" for c in changes) + "</ul>"


class Widget(ABC):
    """모든 대시보드 Widget이 구현해야 하는 계약. `token`이 가리키는 template.html의
    {{TOKEN}} 자리에 `render(data)`의 반환값이 그대로 치환된다."""

    @property
    @abstractmethod
    def token(self) -> str:
        """template.html에서 이 Widget이 채우는 플레이스홀더 이름 (예: "TODAY_CHANGES_HTML")."""

    @abstractmethod
    def render(self, data: dict) -> str:
        """data(dashboard 입력 JSON)를 받아 이 Widget의 HTML 조각을 반환한다."""


class TodayChangeWidget(Widget):
    token = "TODAY_CHANGES_HTML"

    def render(self, data: dict) -> str:
        return render_today_changes(data)


class RiskTrackerWidget(Widget):
    """소송 Tracker — Round 4 명명상 "Risk Tracker"."""

    token = "TRACKER_ROWS_HTML"

    def render(self, data: dict) -> str:
        return render_tracker_rows(data.get("tracker_rows") or [])


class LitigationWidget(Widget):
    """Round 4 명명상 "Litigation" — 미국 외 실리코시스 소송/이슈 현황."""

    token = "NON_US_ISSUES_HTML"

    def render(self, data: dict) -> str:
        return render_generic_list(data.get("non_us_issues") or [], "등록된 미국 외 이슈 없음")


class RegulationWidget(Widget):
    """Round 4 명명상 "Regulation" — 데이터 키/토큰/빈 상태 문구를 주입받아 재사용 가능한
    범용 Widget이다. 같은 클래스를 여러 인스턴스로 만들어 미국 주별/글로벌/세이프가드 세
    구역을 독립적으로 구성한다."""

    def __init__(self, token: str, data_key: str, empty_label: str):
        self._token = token
        self._data_key = data_key
        self._empty_label = empty_label

    @property
    def token(self) -> str:
        return self._token

    def render(self, data: dict) -> str:
        return render_generic_list(data.get(self._data_key) or [], self._empty_label)


class StatisticsWidget(Widget):
    """신규 Widget (Round 4 지시) — 오늘 대시보드에 반영된 각 구역의 건수를 한눈에 요약한다.

    기존 sample_data.json 스키마를 변경하지 않고, 이미 다른 Widget들이 사용하는 데이터
    키(tracker_rows/non_us_issues/...)만 세어 계산한다 — 별도 입력 필드가 필요 없다.
    """

    token = "STATISTICS_HTML"

    _COUNTED_KEYS = [
        ("tracker_rows", "소송 Tracker"),
        ("non_us_issues", "미국 외 이슈"),
        ("us_state_regulations", "미국 주별 규제"),
        ("global_regulations", "글로벌 규제"),
        ("safeguard_news", "세이프가드 소식"),
    ]

    def render(self, data: dict) -> str:
        stats = [(label, len(data.get(key) or [])) for key, label in self._COUNTED_KEYS]
        total = sum(count for _, count in stats)
        items = "".join(
            f'<div class="lcip-stat"><div class="lcip-stat-value">{count}</div>'
            f'<div class="lcip-stat-label">{escape(label)}</div></div>'
            for label, count in stats
        )
        items += (
            f'<div class="lcip-stat lcip-stat-total"><div class="lcip-stat-value">{total}</div>'
            f'<div class="lcip-stat-label">전체 항목</div></div>'
        )
        return f'<div class="lcip-stat-grid">{items}</div>'


class TimelineWidget(Widget):
    """소송금액 추이 — 실제 그래프는 app.js가 클라이언트에서 그리므로, 이 Widget은 데이터를
    JSON으로 직렬화해 `<script>` 태그에 심는 역할만 한다."""

    token = "TREND_DATA_JSON"

    def render(self, data: dict) -> str:
        return json.dumps(data.get("litigation_amount_trend") or [], ensure_ascii=False)


DEFAULT_WIDGETS: list[Widget] = [
    TodayChangeWidget(),
    StatisticsWidget(),
    RiskTrackerWidget(),
    LitigationWidget(),
    RegulationWidget("US_STATE_REGULATIONS_HTML", "us_state_regulations", "등록된 미국 주별 규제 동향 없음"),
    RegulationWidget("GLOBAL_REGULATIONS_HTML", "global_regulations", "등록된 글로벌 규제 동향 없음"),
    RegulationWidget("SAFEGUARD_NEWS_HTML", "safeguard_news", "등록된 세이프가드 소식 없음"),
    TimelineWidget(),
]
