import json
from pathlib import Path

import build_dashboard
from dashboard_widgets import (
    DEFAULT_WIDGETS,
    LitigationWidget,
    RegulationWidget,
    RiskTrackerWidget,
    StatisticsWidget,
    TimelineWidget,
    TodayChangeWidget,
    Widget,
)

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DATA = json.loads((ROOT / "dashboard" / "sample_data.json").read_text(encoding="utf-8"))


def test_all_default_widgets_are_widget_instances_with_unique_tokens():
    assert all(isinstance(w, Widget) for w in DEFAULT_WIDGETS)
    tokens = [w.token for w in DEFAULT_WIDGETS]
    assert len(tokens) == len(set(tokens)), "Widget 토큰이 중복되면 서로 덮어쓴다"


def test_statistics_widget_counts_items_across_sections():
    data = {
        "tracker_rows": [{}, {}],
        "non_us_issues": [{}],
        "us_state_regulations": [],
        "global_regulations": [{}],
        "safeguard_news": [],
    }
    html = StatisticsWidget().render(data)
    assert '<div class="lcip-stat-value">2</div>' in html  # tracker_rows
    assert '<div class="lcip-stat-value">4</div>' in html  # total (2+1+0+1+0)
    assert "lcip-stat-grid" in html


def test_statistics_widget_handles_empty_data():
    html = StatisticsWidget().render({})
    assert "lcip-stat-grid" in html
    assert '<div class="lcip-stat-value">0</div>' in html


def test_today_change_widget_matches_free_function():
    assert TodayChangeWidget().render(SAMPLE_DATA) == build_dashboard.render_today_changes(
        SAMPLE_DATA
    )


def test_risk_tracker_widget_matches_free_function():
    assert RiskTrackerWidget().render(SAMPLE_DATA) == build_dashboard.render_tracker_rows(
        SAMPLE_DATA.get("tracker_rows") or []
    )


def test_litigation_widget_matches_free_function():
    assert LitigationWidget().render(SAMPLE_DATA) == build_dashboard.render_generic_list(
        SAMPLE_DATA.get("non_us_issues") or [], "등록된 미국 외 이슈 없음"
    )


def test_regulation_widget_is_reusable_across_three_sections():
    widgets = [
        RegulationWidget("US_STATE_REGULATIONS_HTML", "us_state_regulations", "없음"),
        RegulationWidget("GLOBAL_REGULATIONS_HTML", "global_regulations", "없음"),
        RegulationWidget("SAFEGUARD_NEWS_HTML", "safeguard_news", "없음"),
    ]
    tokens = [w.token for w in widgets]
    assert tokens == ["US_STATE_REGULATIONS_HTML", "GLOBAL_REGULATIONS_HTML", "SAFEGUARD_NEWS_HTML"]
    for w in widgets:
        assert w.render({}) == '<p class="lcip-empty">없음</p>'


def test_timeline_widget_serializes_trend_json():
    data = {"litigation_amount_trend": [{"date": "2026-07-01", "amount_usd": 1000}]}
    result = TimelineWidget().render(data)
    assert json.loads(result) == data["litigation_amount_trend"]


def test_removing_a_widget_drops_only_its_section():
    """Round 4 요구사항 검증: Widget 목록에서 하나를 빼면 그 섹션 토큰만 사라지고
    나머지는 그대로 유지된다(독립적으로 추가/제거 가능)."""
    reduced_widgets = [w for w in DEFAULT_WIDGETS if w.token != "STATISTICS_HTML"]
    tokens = build_dashboard._render_common_tokens(SAMPLE_DATA, widgets=reduced_widgets)
    assert "{{STATISTICS_HTML}}" not in tokens
    assert "{{TRACKER_ROWS_HTML}}" in tokens


def test_build_html_includes_statistics_section():
    html = build_dashboard.build_html(SAMPLE_DATA)
    assert "통계 요약" in html
    assert "lcip-stat-grid" in html
    assert "{{" not in html
