import json
from pathlib import Path

import build_dashboard

ROOT = Path(__file__).resolve().parent.parent


def test_build_html_with_sample_data_contains_all_required_sections():
    data = json.loads((ROOT / "dashboard" / "sample_data.json").read_text(encoding="utf-8"))
    html = build_dashboard.build_html(data)

    assert "실리코시스 소송 Tracker" in html
    assert "미국 외 실리코시스 이슈 현황" in html
    assert "미국 주별 규제·입법 현황" in html
    assert "글로벌 규제·생산금지 현황" in html
    assert "세이프가드 관련 소식" in html
    assert "소송금액 추이" in html
    assert "{{" not in html, "치환되지 않은 템플릿 토큰이 남아있음"


def test_build_html_shows_no_change_message_when_empty():
    data = {
        "topic_display_name": "테스트",
        "generated_at_kst": "2026-08-05 09:00",
        "today_changes": [],
        "today_changes_summary": "신규 주요 변화 없음",
        "tracker_rows": [],
        "non_us_issues": [],
        "us_state_regulations": [],
        "global_regulations": [],
        "safeguard_news": [],
        "litigation_amount_trend": [],
    }
    html = build_dashboard.build_html(data)
    assert "신규 주요 변화 없음" in html
    assert "등록된 Tracker 항목 없음" in html


def test_tracker_row_amount_formatting_no_null_crash():
    row = {
        "published_at": "2026-07-30", "region": "US-CA", "title": "샘플",
        "defendant": "샘플기업", "event_type": "소송", "total_amount_usd": None,
        "claimant_count": None, "avg_amount_per_person_usd": None, "status": "진행중",
        "source_url": "https://example.com", "note": "",
    }
    html_fragment = build_dashboard.render_tracker_rows([row])
    assert "-" in html_fragment
    assert "None" not in html_fragment


def test_html_output_has_no_broken_word_wrap_css():
    styles = (ROOT / "dashboard" / "styles.css").read_text(encoding="utf-8")
    assert "word-break: keep-all" in styles
