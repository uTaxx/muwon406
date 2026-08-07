"""TASK-012/012A — Widget 기반 대시보드 구성 요소.

Round 4: "대시보드는 오늘의 주요변화/리스크 Tracker/소송/규제/통계/타임라인을 독립적으로
추가·제거 가능한 Widget 클래스로 구성한다."

Round 5(TASK-012A): "Widget은 HTML을 직접 생성하지 않는다. Widget Data를 반환한다." —
구조를 **Data Provider → Widget → Dashboard**로 바꾼다. 각 Widget은
`get_data(data)`(구조화된 데이터만 반환, HTML 없음)와 `render_html(widget_data)`(그
데이터를 HTML로 바꾸는 순수 렌더러)로 나뉜다. `render(data)`는 하위호환을 위해 남겨두되
`render_html(get_data(data))`를 호출하는 조합으로만 구현된다.

Round 8: "Dashboard는 HTML Viewer가 아니라 Executive Dashboard가 되어야 한다." 기존
소송·규제 특화 Widget 6종(Today's Change/Risk Tracker/Litigation/Regulation×3/
Statistics/Timeline)을 전부 제거하고, Architect가 지정한 우선순위 그대로 6개 Widget만
남긴다: Today's Intelligence → Critical Risk → Future Opportunity → Quick Company
Scan → Investment Review → Source Health. 각 Widget은 실제 Pipeline 산출물
(INTELLIGENCE_DB/COMPANY_SCAN_DB/Source Registry)을 반영한다 — 정적 HTML을 그냥
보여주는 Viewer가 아니라, 그 산출물이 바뀌면 대시보드도 그대로 바뀐다.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from html import escape
from typing import Any


def _fmt_cell(value) -> str:
    if value is None:
        return "-"
    return escape(str(value))


def render_generic_list(items: list[dict], empty_label: str) -> str:
    if not items:
        return f'<p class="lcip-empty">{escape(empty_label)}</p>'
    rows = []
    for item in items:
        cols = "".join(f"<td>{_fmt_cell(v)}</td>" for v in item.values())
        rows.append(f"<tr>{cols}</tr>")
    headers = "".join(f"<th>{escape(k)}</th>" for k in items[0].keys())
    return (
        '<table class="lcip-table"><thead><tr>'
        + headers
        + "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


class Widget(ABC):
    """모든 대시보드 Widget이 구현해야 하는 계약. `token`이 가리키는 template.html의
    {{TOKEN}} 자리에 `render(data)`의 반환값이 그대로 치환된다."""

    @property
    @abstractmethod
    def token(self) -> str:
        """template.html에서 이 Widget이 채우는 플레이스홀더 이름."""

    @abstractmethod
    def get_data(self, data: dict) -> Any:
        """dashboard 입력 데이터에서 이 Widget에 필요한 부분만 구조화해 반환한다.
        HTML은 만들지 않는다(Round 5: Data Provider → Widget → Dashboard)."""

    @abstractmethod
    def render_html(self, widget_data: Any) -> str:
        """get_data()가 반환한 구조화 데이터를 HTML 조각으로 변환하는 순수 렌더러."""

    def render(self, data: dict) -> str:
        """하위호환 편의 메서드 — get_data() + render_html()을 합쳐서 수행한다."""
        return self.render_html(self.get_data(data))


class TodayIntelligenceWidget(Widget):
    """1순위 — 오늘 새로 생성된 INTELLIGENCE_DB 레코드(사실 요약)."""

    token = "TODAY_INTELLIGENCE_HTML"

    def get_data(self, data: dict) -> list[dict]:
        return data.get("today_intelligence") or []

    def render_html(self, widget_data: list[dict]) -> str:
        return render_generic_list(widget_data, "오늘 신규 Intelligence 없음")


class CriticalRiskWidget(Widget):
    """2순위 — mission_category에 risk_management가 포함된 INTELLIGENCE_DB 레코드."""

    token = "CRITICAL_RISK_HTML"

    def get_data(self, data: dict) -> list[dict]:
        return data.get("critical_risk") or []

    def render_html(self, widget_data: list[dict]) -> str:
        return render_generic_list(widget_data, "등록된 Critical Risk 없음")


class FutureOpportunityWidget(Widget):
    """3순위 — mission_category에 future_readiness가 포함된 INTELLIGENCE_DB 레코드."""

    token = "FUTURE_OPPORTUNITY_HTML"

    def get_data(self, data: dict) -> list[dict]:
        return data.get("future_opportunity") or []

    def render_html(self, widget_data: list[dict]) -> str:
        return render_generic_list(widget_data, "등록된 Future Opportunity 신호 없음")


class QuickCompanyScanWidget(Widget):
    """4순위 — COMPANY_SCAN_DB의 최근 Quick Company Scan 결과."""

    token = "QUICK_COMPANY_SCAN_HTML"

    def get_data(self, data: dict) -> list[dict]:
        return data.get("quick_company_scan") or []

    def render_html(self, widget_data: list[dict]) -> str:
        return render_generic_list(widget_data, "실행된 Quick Company Scan 없음")


class InvestmentReviewWidget(Widget):
    """5순위 — COMPANY_SCAN_DB에 함께 저장된 Investment Review 추천 신호."""

    token = "INVESTMENT_REVIEW_HTML"

    def get_data(self, data: dict) -> list[dict]:
        return data.get("investment_review") or []

    def render_html(self, widget_data: list[dict]) -> str:
        return render_generic_list(widget_data, "실행된 Investment Review 없음")


class SourceHealthWidget(Widget):
    """6순위 — Source Registry(`config/sources.yaml`) 기준 현재 활성 상태.

    실제 주기적 Health Check(TASK-014)는 아직 스케줄되지 않으므로, `active` 필드와
    Round 7이 추가한 `historical_stability`를 있는 그대로 보여준다 — 실제로 확인한 적
    없는 상태를 "정상"이라고 지어내지 않는다.
    """

    token = "SOURCE_HEALTH_HTML"

    def get_data(self, data: dict) -> list[dict]:
        return data.get("source_health") or []

    def render_html(self, widget_data: list[dict]) -> str:
        return render_generic_list(widget_data, "등록된 Source 없음")


DEFAULT_WIDGETS: list[Widget] = [
    TodayIntelligenceWidget(),
    CriticalRiskWidget(),
    FutureOpportunityWidget(),
    QuickCompanyScanWidget(),
    InvestmentReviewWidget(),
    SourceHealthWidget(),
]
