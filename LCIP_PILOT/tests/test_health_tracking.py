import pytest

from adapters.base import SourceAdapterDisabledError
from adapters.google_rss_adapter import GoogleRSSAdapter
from health_tracking import run_health_check

SRC_CONFIG = {
    "source_id": "SRC-0001",
    "source_name": "Google News RSS (English)",
    "endpoint_url": "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en",
    "language": "en",
}

from pathlib import Path

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
