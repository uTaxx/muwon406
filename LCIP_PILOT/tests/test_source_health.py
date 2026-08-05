from pathlib import Path

import pytest

from adapters.base import SourceAdapterDisabledError
from adapters.google_rss_adapter import GoogleRSSAdapter
from source_health_check import (
    HealthCheckInput,
    classify,
    next_retry_delay_minutes,
    run_health_check,
    should_alert,
)


def test_healthy_response():
    check = HealthCheckInput(
        http_status=200, response_ms=800, content_type="application/rss+xml",
        record_count=10, freshness_hours=1.0,
    )
    assert classify(check) == "HEALTHY"


def test_404_is_broken_link():
    check = HealthCheckInput(http_status=404, response_ms=200, content_type=None, record_count=None)
    assert classify(check) == "BROKEN_LINK"


def test_429_is_rate_limited():
    check = HealthCheckInput(http_status=429, response_ms=100, content_type=None, record_count=None)
    assert classify(check) == "RATE_LIMITED"


def test_html_error_page_is_content_invalid():
    check = HealthCheckInput(
        http_status=200, response_ms=300, content_type="text/html; charset=utf-8", record_count=None
    )
    assert classify(check) == "CONTENT_INVALID"


def test_no_http_status_is_broken_link():
    check = HealthCheckInput(http_status=None, response_ms=None, content_type=None, record_count=None)
    assert classify(check) == "BROKEN_LINK"


def test_stale_when_freshness_exceeded():
    check = HealthCheckInput(
        http_status=200, response_ms=500, content_type="application/rss+xml",
        record_count=5, freshness_hours=48.0, expected_freshness_hours=24.0,
    )
    assert classify(check) == "STALE"


def test_retry_schedule():
    assert next_retry_delay_minutes(1) == 5
    assert next_retry_delay_minutes(2) == 15
    assert next_retry_delay_minutes(3) is None


def test_should_alert_after_3_failures():
    assert should_alert(2) is False
    assert should_alert(3) is True


# --- run_health_check(): SourceAdapter 연동 (Round 5 Technical Debt 정리로
# health_tracking.py에서 이 모듈로 병합됨) ---

SRC_CONFIG = {
    "source_id": "SRC-0001",
    "source_name": "Google News RSS (English)",
    "endpoint_url": "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en",
    "language": "en",
}

SAMPLE_RSS_TEXT = (
    Path(__file__).resolve().parent / "fixtures" / "sample_google_news_rss.xml"
).read_text(encoding="utf-8")


def test_run_health_check_healthy_when_adapter_returns_articles():
    adapter = GoogleRSSAdapter(SRC_CONFIG, enabled=True, http_get=lambda url: SAMPLE_RSS_TEXT)
    status, check = run_health_check(adapter, "engineered stone silicosis")
    assert status == "HEALTHY"
    assert check.record_count == 2
    assert check.http_status == 200


def test_run_health_check_anomaly_when_below_expected_min_record_count():
    adapter = GoogleRSSAdapter(SRC_CONFIG, enabled=True, http_get=lambda url: SAMPLE_RSS_TEXT)
    status, check = run_health_check(adapter, "query", expected_min_record_count=10)
    assert status == "ANOMALY"


def test_run_health_check_broken_link_when_adapter_raises():
    def failing_http_get(url: str) -> str:
        raise ConnectionError("network unreachable")

    adapter = GoogleRSSAdapter(SRC_CONFIG, enabled=True, http_get=failing_http_get)
    status, check = run_health_check(adapter, "query")
    assert status == "BROKEN_LINK"
    assert check.http_status is None
    assert check.parse_ok is False


def test_run_health_check_propagates_disabled_error():
    adapter = GoogleRSSAdapter(SRC_CONFIG)  # enabled=False by default
    with pytest.raises(SourceAdapterDisabledError):
        run_health_check(adapter, "query")
