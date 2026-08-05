from source_health_check import HealthCheckInput, classify, next_retry_delay_minutes, should_alert


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
