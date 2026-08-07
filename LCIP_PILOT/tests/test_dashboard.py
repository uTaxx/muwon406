import json
from pathlib import Path

import pytest

import build_dashboard

ROOT = Path(__file__).resolve().parent.parent


def test_build_html_with_sample_data_contains_all_required_sections():
    data = json.loads((ROOT / "dashboard" / "sample_data.json").read_text(encoding="utf-8"))
    html = build_dashboard.build_html(data)

    assert "Today's Intelligence" in html
    assert "Critical Risk" in html
    assert "Future Opportunity" in html
    assert "Quick Company Scan" in html
    assert "Investment Review" in html
    assert "Source Health" in html
    assert "{{" not in html, "치환되지 않은 템플릿 토큰이 남아있음"


def test_build_html_contains_home_section_with_five_required_items():
    """Round 11 지시: Home 화면은 1)오늘의 핵심 Intelligence 2)Quick Company Scan 실행
    3)Investment Review 실행 4)최근 분석 결과 5)최근 뉴스를 반드시 포함해야 한다."""
    data = json.loads((ROOT / "dashboard" / "sample_data.json").read_text(encoding="utf-8"))
    html = build_dashboard.build_html(data)

    assert 'id="home"' in html
    assert "오늘의 핵심 Intelligence" in html
    assert "Quick Company Scan 실행" in html
    assert "Investment Review 실행" in html
    assert "최근 분석 결과" in html
    assert "최근 뉴스" in html
    assert "scenario_3_investment_review.py" in html
    assert "{{" not in html, "치환되지 않은 HOME_* 토큰이 남아있음"


def test_build_html_home_section_falls_back_when_recent_news_missing():
    data = {
        "topic_display_name": "테스트",
        "generated_at_kst": "2026-08-05 09:00",
        "today_intelligence": [],
        "critical_risk": [],
        "future_opportunity": [],
        "quick_company_scan": [],
        "investment_review": [],
        "source_health": [],
    }
    html = build_dashboard.build_html(data)
    assert "최근 수집된 뉴스 없음" in html
    assert "{{" not in html


def test_build_html_shows_empty_placeholders_when_data_is_empty():
    data = {
        "topic_display_name": "테스트",
        "generated_at_kst": "2026-08-05 09:00",
        "today_intelligence": [],
        "critical_risk": [],
        "future_opportunity": [],
        "quick_company_scan": [],
        "investment_review": [],
        "source_health": [],
    }
    html = build_dashboard.build_html(data)
    assert "오늘 신규 Intelligence 없음" in html
    assert "등록된 Critical Risk 없음" in html


def test_render_generic_list_no_null_crash():
    html_fragment = build_dashboard.render_generic_list(
        [{"a": None, "b": "샘플"}], "없음"
    )
    assert "None" not in html_fragment


def test_html_output_has_no_broken_word_wrap_css():
    styles = (ROOT / "dashboard" / "styles.css").read_text(encoding="utf-8")
    assert "word-break: keep-all" in styles


def test_split_mode_returns_three_files_with_external_refs():
    data = json.loads((ROOT / "dashboard" / "sample_data.json").read_text(encoding="utf-8"))
    result = build_dashboard.build_html(data, mode="split")

    assert set(result.keys()) == {"dashboard.html", "styles.css", "app.js"}
    assert '<link rel="stylesheet" href="styles.css">' in result["dashboard.html"]
    assert '<script src="app.js"></script>' in result["dashboard.html"]
    assert "{{" not in result["dashboard.html"]
    assert "word-break: keep-all" in result["styles.css"]
    assert result["app.js"] == (ROOT / "dashboard" / "app.js").read_text(encoding="utf-8")


def test_single_mode_is_default_and_returns_self_contained_string():
    data = json.loads((ROOT / "dashboard" / "sample_data.json").read_text(encoding="utf-8"))
    html_default = build_dashboard.build_html(data)
    html_explicit = build_dashboard.build_html(data, mode="single")
    assert html_default == html_explicit
    assert isinstance(html_default, str)
    assert "<style>" in html_default and "word-break: keep-all" in html_default


def test_invalid_mode_raises():
    data = json.loads((ROOT / "dashboard" / "sample_data.json").read_text(encoding="utf-8"))
    with pytest.raises(ValueError):
        build_dashboard.build_html(data, mode="bogus")
