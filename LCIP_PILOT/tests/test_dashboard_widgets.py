import json
from pathlib import Path

import build_dashboard
from dashboard_widgets import (
    DEFAULT_WIDGETS,
    CriticalRiskWidget,
    FutureOpportunityWidget,
    InvestmentReviewWidget,
    QuickCompanyScanWidget,
    SourceHealthWidget,
    TodayIntelligenceWidget,
    Widget,
    render_generic_list,
)

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DATA = json.loads((ROOT / "dashboard" / "sample_data.json").read_text(encoding="utf-8"))


def test_all_default_widgets_are_widget_instances_with_unique_tokens():
    assert all(isinstance(w, Widget) for w in DEFAULT_WIDGETS)
    tokens = [w.token for w in DEFAULT_WIDGETS]
    assert len(tokens) == len(set(tokens)), "Widget 토큰이 중복되면 서로 덮어쓴다"


def test_pilot_has_exactly_6_widgets_in_architect_priority_order():
    """Architect Review Round 8: "Pilot에서는 6개 Widget만 구현한다" — 우선순위 순서까지
    고정되어 있다."""
    assert len(DEFAULT_WIDGETS) == 6
    assert [type(w).__name__ for w in DEFAULT_WIDGETS] == [
        "TodayIntelligenceWidget",
        "CriticalRiskWidget",
        "FutureOpportunityWidget",
        "QuickCompanyScanWidget",
        "InvestmentReviewWidget",
        "SourceHealthWidget",
    ]


def test_render_generic_list_handles_empty():
    assert render_generic_list([], "없음") == '<p class="lcip-empty">없음</p>'


def test_render_generic_list_renders_table():
    html = render_generic_list([{"a": 1, "b": 2}], "없음")
    assert "<table" in html and "<th>a</th>" in html and "<td>1</td>" in html


def test_today_intelligence_widget_uses_sample_data():
    widget_data = TodayIntelligenceWidget().get_data(SAMPLE_DATA)
    assert widget_data == SAMPLE_DATA["today_intelligence"]
    assert "샘플" in TodayIntelligenceWidget().render(SAMPLE_DATA) or "표본" in TodayIntelligenceWidget().render(SAMPLE_DATA)


def test_critical_risk_widget_empty_shows_placeholder():
    html = CriticalRiskWidget().render({})
    assert "Critical Risk 없음" in html


def test_future_opportunity_widget_empty_shows_placeholder():
    html = FutureOpportunityWidget().render({})
    assert "Future Opportunity" in html


def test_quick_company_scan_widget_uses_sample_data():
    widget_data = QuickCompanyScanWidget().get_data(SAMPLE_DATA)
    assert widget_data == SAMPLE_DATA["quick_company_scan"]


def test_investment_review_widget_uses_sample_data():
    widget_data = InvestmentReviewWidget().get_data(SAMPLE_DATA)
    assert widget_data == SAMPLE_DATA["investment_review"]


def test_source_health_widget_uses_sample_data():
    widget_data = SourceHealthWidget().get_data(SAMPLE_DATA)
    assert widget_data == SAMPLE_DATA["source_health"]


def test_removing_a_widget_drops_only_its_section():
    """Round 4 요구사항 검증: Widget 목록에서 하나를 빼면 그 섹션 토큰만 사라지고
    나머지는 그대로 유지된다(독립적으로 추가/제거 가능)."""
    reduced_widgets = [w for w in DEFAULT_WIDGETS if w.token != "SOURCE_HEALTH_HTML"]
    tokens = build_dashboard._render_common_tokens(SAMPLE_DATA, widgets=reduced_widgets)
    assert "{{SOURCE_HEALTH_HTML}}" not in tokens
    assert "{{TODAY_INTELLIGENCE_HTML}}" in tokens


def test_build_html_includes_all_6_widget_sections():
    html = build_dashboard.build_html(SAMPLE_DATA)
    assert "Today's Intelligence" in html
    assert "Critical Risk" in html
    assert "Future Opportunity" in html
    assert "Quick Company Scan" in html
    assert "Investment Review" in html
    assert "Source Health" in html
    assert "{{" not in html


def test_widget_get_data_returns_data_not_html():
    """Round 5 핵심 요구사항: Widget은 HTML을 직접 만들지 않고 데이터를 반환한다."""
    widget_data = QuickCompanyScanWidget().get_data(SAMPLE_DATA)
    assert isinstance(widget_data, list)
    assert all("<td>" not in str(item) for item in widget_data)


def test_widget_render_equals_render_html_of_get_data():
    for widget in DEFAULT_WIDGETS:
        assert widget.render(SAMPLE_DATA) == widget.render_html(widget.get_data(SAMPLE_DATA))
