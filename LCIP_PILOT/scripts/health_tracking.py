"""TASK-014 연동 — Source Health 판정 로직을 실제 SourceAdapter 호출과 연결한다.

`source_health_check.py`는 순수 판정 함수(HealthCheckInput -> health_status)만 제공했다.
이 모듈은 실제 Adapter.collect() 호출 결과(성공/응답시간/건수/예외)를 HealthCheckInput으로
변환해 그 판정 함수에 넘긴다 — Adapter의 `enabled`/`http_get` 주입 설계 덕분에, 테스트에서는
fixture 데이터로 실제 네트워크 호출 없이 이 연동 전체를 검증할 수 있다.
"""
from __future__ import annotations

import time

from adapters.base import SourceAdapter, SourceAdapterDisabledError
from source_health_check import HealthCheckInput, classify


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
