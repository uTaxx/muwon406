"""GoogleRSSAdapter — Google News RSS(SRC-0001/SRC-0002)를 수집하는 실동작 Adapter.

RSS XML 파싱(`parse_feed()`)은 Round 4부터 이미 실제 로직이다(Mock이 아니다) — feedparser로
실제 RSS 문서를 파싱해 `RawArticle`을 만든다. 실제 HTTP 요청 함수(`http_get`)는 생성자에서
주입받으며, 기본값은 `requests.get(...).text`를 쓰는 실제 구현이다.

Round 6부터 `enabled`의 기본값은 하드코딩된 `False`가 아니라 `config/feature_flags.yaml`의
`real_network_calls` 전역 스위치를 따른다(다음 Architect 승인 전까지 그 값은 `false`로
유지된다) — `enabled`를 명시적으로 넘기면 그 값이 항상 우선한다(테스트가 하는 것처럼).
`enabled`가 꺼져 있는 동안은 `collect()`가 즉시 `SourceAdapterDisabledError`를 발생시켜
실제 네트워크 호출까지 도달하지 않는다. Fixture 기반 테스트(`tests/test_adapters.py`)는
`enabled=True` + 주입한 fixture 문자열로 파싱 로직을 실제 네트워크 없이 완전히 검증한다.
"""
from __future__ import annotations

import calendar
from datetime import datetime, timezone
from typing import Callable

import feedparser

from feature_flags import is_enabled
from .base import RawArticle, SourceAdapter, SourceAdapterDisabledError


def _default_http_get(url: str) -> str:
    import requests

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.text


class GoogleRSSAdapter(SourceAdapter):
    """`config/sources.yaml`의 SRC-0001(영문)/SRC-0002(한글) 등 `access_method: rss` 소스용."""

    def __init__(
        self,
        source_config: dict,
        enabled: bool | None = None,
        http_get: Callable[[str], str] | None = None,
    ):
        super().__init__(source_config)
        self.enabled = enabled if enabled is not None else is_enabled("real_network_calls")
        self._http_get = http_get or _default_http_get

    def collect(self, query: str) -> list[RawArticle]:
        if not self.enabled:
            raise SourceAdapterDisabledError(
                f"{self.source_id}: GoogleRSSAdapter.enabled=False — 실제 RSS 호출은 "
                "TASK-010 본구현 승인 후에만 활성화한다. 지금은 fixture/mock을 사용하라."
            )
        endpoint_template = self.source_config.get("endpoint_url", "")
        url = endpoint_template.format(query=query)
        raw_text = self._http_get(url)
        return self.parse_feed(raw_text)

    def parse_feed(self, raw_feed_text: str) -> list[RawArticle]:
        """RSS XML 문자열 → RawArticle 목록. 네트워크와 무관한 순수 파싱 로직이라
        `enabled` 상태와 무관하게 직접 호출해 테스트할 수 있다."""
        parsed = feedparser.parse(raw_feed_text)
        source_name = self.source_config.get("source_name", "Google News RSS")
        language = self.source_config.get("language", "en")
        articles: list[RawArticle] = []
        for entry in parsed.entries:
            published_at = self._to_iso8601(entry.get("published_parsed")) or entry.get(
                "published"
            )
            articles.append(
                RawArticle(
                    title_original=entry.get("title", "").strip(),
                    source_url=entry.get("link", ""),
                    source_name=source_name,
                    published_at=published_at,
                    language=language,
                    summary_raw=entry.get("summary"),
                )
            )
        return articles

    @staticmethod
    def _to_iso8601(published_parsed) -> str | None:
        """feedparser의 `published_parsed`(struct_time, UTC)를 ISO8601 문자열로 변환한다.

        RSS의 pubDate 포맷(RFC822 등)은 소스마다 제각각이므로, 이후 Pipeline의 Normalize
        단계가 `schemas/article.schema.json`의 `format: date-time`을 그대로 받을 수 있도록
        이 시점에서 표준화한다.
        """
        if not published_parsed:
            return None
        timestamp = calendar.timegm(published_parsed)
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
