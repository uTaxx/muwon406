"""NaverNewsAdapter — Naver News Search API(SRC-0003)를 수집하는 실동작 Adapter.

뉴스 수집 실체화 라운드(2026-08-08)에서 `future_adapters.py`의 stub을 대체했다 —
`GoogleRSSAdapter`와 동일한 구조(생성자 `enabled`/`http_get` 주입,
`feature_flags.real_network_calls` 기본 게이트, `SourceAdapterDisabledError`)를
그대로 따른다. Naver Developer Center에 등록한 Client ID/Secret(`.env`의
`NAVER_CLIENT_ID`/`NAVER_CLIENT_SECRET`)이 필요하다.
"""
from __future__ import annotations

import html
import re
from urllib.parse import quote
from typing import Callable

from _common import env_or_none
from feature_flags import is_enabled
from .base import RawArticle, SourceAdapter, SourceAdapterDisabledError

_TAG_RE = re.compile(r"<[^>]+>")


def _default_http_get(url: str, headers: dict) -> str:
    import requests

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.text


class NaverNewsAdapter(SourceAdapter):
    """`config/sources.yaml`의 SRC-0003(Naver News Search API)용."""

    def __init__(
        self,
        source_config: dict,
        enabled: bool | None = None,
        http_get: Callable[[str, dict], str] | None = None,
    ):
        super().__init__(source_config)
        self.enabled = enabled if enabled is not None else is_enabled("real_network_calls")
        self._http_get = http_get or _default_http_get

    def collect(self, query: str) -> list[RawArticle]:
        if not self.enabled:
            raise SourceAdapterDisabledError(
                f"{self.source_id}: NaverNewsAdapter.enabled=False — 실제 Naver API 호출은 "
                "feature_flags.real_network_calls=True 이후에만 활성화한다. 지금은 fixture/"
                "mock을 사용하라."
            )
        client_id = env_or_none("NAVER_CLIENT_ID")
        client_secret = env_or_none("NAVER_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise RuntimeError(
                f"{self.source_id}: NAVER_CLIENT_ID/NAVER_CLIENT_SECRET이 .env에 없다 — "
                "임의로 추정하지 않는다."
            )
        endpoint = self.source_config.get("endpoint_url", "")
        url = f"{endpoint}?query={quote(query)}&display=100&sort=date"
        headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret,
        }
        raw_json = self._http_get(url, headers)
        return self.parse_response(raw_json)

    def parse_response(self, raw_json_text: str) -> list[RawArticle]:
        """Naver News Search API JSON 응답 → RawArticle 목록. 네트워크와 무관한 순수
        파싱 로직이라 `enabled` 상태와 무관하게 직접 호출해 테스트할 수 있다."""
        import json

        parsed = json.loads(raw_json_text)
        source_name = self.source_config.get("source_name", "Naver News")
        language = self.source_config.get("language", "ko")
        articles: list[RawArticle] = []
        for item in parsed.get("items", []):
            articles.append(
                RawArticle(
                    title_original=self._clean_naver_text(item.get("title", "")),
                    source_url=item.get("originallink") or item.get("link", ""),
                    source_name=source_name,
                    published_at=self._to_iso8601(item.get("pubDate")),
                    language=language,
                    summary_raw=self._clean_naver_text(item.get("description", "")),
                )
            )
        return articles

    @staticmethod
    def _clean_naver_text(text: str) -> str:
        """Naver 응답은 검색어 강조를 위해 `<b>` 태그와 HTML 엔티티(`&quot;` 등)를
        포함한다 — 원문 판단에 방해되므로 제거한다."""
        return html.unescape(_TAG_RE.sub("", text)).strip()

    @staticmethod
    def _to_iso8601(pub_date: str | None) -> str | None:
        """Naver의 `pubDate`는 RFC822 형식(예: "Mon, 26 Sep 2016 07:50:00 +0900")이다."""
        if not pub_date:
            return None
        from email.utils import parsedate_to_datetime

        try:
            dt = parsedate_to_datetime(pub_date)
        except (TypeError, ValueError):
            return None
        from datetime import timezone

        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
