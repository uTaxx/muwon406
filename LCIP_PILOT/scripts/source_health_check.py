#!/usr/bin/env python3
"""TASK-014 준비 — Source Health 판정 로직 (순수 함수).

실제 HTTP 호출로 각 Source를 점검하는 오케스트레이션은 n8n(WF-P08)이 담당한다. 이 모듈은
"점검 결과를 어떤 health_status로 분류할지" 판정 로직만 제공하며, 로컬에서 mock 응답으로
테스트 가능하다 (TASK-014 완료조건: "Mock 정상·404·429·HTML 오류페이지 테스트").
"""
from __future__ import annotations

from dataclasses import dataclass

VALID_STATUSES = {
    "HEALTHY", "DEGRADED", "STALE", "BROKEN_LINK", "SCHEMA_CHANGED",
    "AUTH_ERROR", "RATE_LIMITED", "CONTENT_INVALID", "ANOMALY",
}


@dataclass(frozen=True)
class HealthCheckInput:
    http_status: int | None
    response_ms: int | None
    content_type: str | None
    record_count: int | None
    expected_min_record_count: int = 1
    parse_ok: bool = True
    freshness_hours: float | None = None
    expected_freshness_hours: float = 24.0


def classify(check: HealthCheckInput) -> str:
    if check.http_status is None:
        return "BROKEN_LINK"
    if check.http_status == 429:
        return "RATE_LIMITED"
    if check.http_status in (401, 403):
        return "AUTH_ERROR"
    if check.http_status >= 500 or check.http_status == 404:
        return "BROKEN_LINK"
    if check.http_status >= 400:
        return "CONTENT_INVALID"

    if not check.parse_ok:
        return "SCHEMA_CHANGED"

    if check.content_type and "html" in check.content_type.lower():
        # RSS/JSON/XML을 기대했는데 HTML(로그인/오류 페이지 등)이 오면 콘텐츠 이상으로 판정
        return "CONTENT_INVALID"

    if check.record_count is not None and check.record_count < check.expected_min_record_count:
        return "ANOMALY"

    if (
        check.freshness_hours is not None
        and check.freshness_hours > check.expected_freshness_hours
    ):
        return "STALE"

    if check.response_ms is not None and check.response_ms > 10_000:
        return "DEGRADED"

    return "HEALTHY"


def next_retry_delay_minutes(consecutive_failures: int) -> int | None:
    """TASK-014 재시도 규칙: 1회 실패 5분 후, 2회 실패 15분 후, 3회 이상은 즉시 알림(재시도 없음)."""
    if consecutive_failures <= 0:
        return None
    if consecutive_failures == 1:
        return 5
    if consecutive_failures == 2:
        return 15
    return None  # 3회 이상 연속 실패 -> 관리자 알림 (재시도 대신)


def should_alert(consecutive_failures: int) -> bool:
    return consecutive_failures >= 3
