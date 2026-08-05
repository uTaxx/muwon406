#!/usr/bin/env python3
"""TASK-014 — Source Health 판정 로직 + Source Adapter 연동.

`docs/03_BUILD_SPECIFICATION.md`가 지정한 파일명(`source_health_check.py`)을 그대로
유지한다. 두 계층을 한 모듈에 담는다:

1. **판정 로직(순수 함수)** — `classify()`는 "점검 결과를 어떤 health_status로 분류할지"만
   담당하며, 로컬에서 mock 응답으로 테스트 가능하다 (TASK-014 완료조건: "Mock 정상·404·
   429·HTML 오류페이지 테스트"). 실제 HTTP 호출로 각 Source를 점검하는 오케스트레이션은
   n8n(WF-P08)이 담당한다.
2. **Adapter 연동(`run_health_check()`)** — 실제 `SourceAdapter.collect()` 호출 결과(성공/
   응답시간/건수/예외)를 `HealthCheckInput`으로 변환해 위 판정 로직에 넘긴다. Round 5
   Technical Debt 정리 전에는 `scripts/health_tracking.py`로 분리되어 있었으나, "판정
   로직과 연동을 굳이 나눌 이유가 없다"는 Architect Review Round 5 지시로 한 파일로
   합쳤다. Adapter의 `enabled`/`http_get` 주입 설계 덕분에, 테스트에서는 fixture
   데이터로 실제 네트워크 호출 없이 이 연동 전체를 검증할 수 있다.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from adapters.base import SourceAdapter, SourceAdapterDisabledError

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


def run_health_check(
    adapter: SourceAdapter,
    query: str,
    expected_min_record_count: int = 1,
    expected_freshness_hours: float = 24.0,
) -> tuple[str, HealthCheckInput]:
    """Adapter를 실제로 호출해 (health_status, HealthCheckInput)을 반환한다.

    `SourceAdapterDisabledError`는 그대로 전파한다 — 비활성 Adapter는 "점검 대상이 아직
    아님"이지 "점검 결과 비정상"이 아니므로, 호출자가 이 둘을 구분해서 처리해야 한다.
    """
    started = time.monotonic()
    try:
        articles = adapter.collect(query)
    except SourceAdapterDisabledError:
        raise
    except Exception:
        elapsed_ms = int((time.monotonic() - started) * 1000)
        check = HealthCheckInput(
            http_status=None,
            response_ms=elapsed_ms,
            content_type=None,
            record_count=None,
            expected_min_record_count=expected_min_record_count,
            parse_ok=False,
            expected_freshness_hours=expected_freshness_hours,
        )
        return classify(check), check

    elapsed_ms = int((time.monotonic() - started) * 1000)
    check = HealthCheckInput(
        http_status=200,
        response_ms=elapsed_ms,
        content_type="application/rss+xml",
        record_count=len(articles),
        expected_min_record_count=expected_min_record_count,
        parse_ok=True,
        expected_freshness_hours=expected_freshness_hours,
    )
    return classify(check), check
