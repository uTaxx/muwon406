from pathlib import Path

import pytest

from adapters.base import RawArticle, SourceAdapter, SourceAdapterDisabledError
from adapters.future_adapters import (
    DartFilingAdapter,
    GovernmentPressReleaseAdapter,
    IRPageAdapter,
    NaverNewsAdapter,
)
from adapters.google_rss_adapter import GoogleRSSAdapter

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_RSS_TEXT = (ROOT / "tests" / "fixtures" / "sample_google_news_rss.xml").read_text(
    encoding="utf-8"
)

SRC_0001_CONFIG = {
    "source_id": "SRC-0001",
    "source_name": "Google News RSS (English)",
    "endpoint_url": "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en",
    "access_method": "rss",
    "language": "en",
    "active": True,
}


def test_google_rss_adapter_is_a_source_adapter():
    assert isinstance(GoogleRSSAdapter(SRC_0001_CONFIG), SourceAdapter)


def test_google_rss_adapter_disabled_by_default():
    adapter = GoogleRSSAdapter(SRC_0001_CONFIG)
    assert adapter.enabled is False
    with pytest.raises(SourceAdapterDisabledError):
        adapter.collect("engineered stone silicosis")


def test_google_rss_adapter_default_enabled_follows_feature_flag():
    """Round 6: enabled를 명시하지 않으면 config/feature_flags.yaml의
    real_network_calls를 따른다(현재는 false)."""
    from feature_flags import is_enabled

    adapter = GoogleRSSAdapter(SRC_0001_CONFIG)
    assert adapter.enabled == is_enabled("real_network_calls")


def test_google_rss_adapter_explicit_enabled_overrides_feature_flag():
    adapter = GoogleRSSAdapter(SRC_0001_CONFIG, enabled=True, http_get=lambda url: "")
    assert adapter.enabled is True


def test_google_rss_adapter_parse_feed_extracts_articles():
    adapter = GoogleRSSAdapter(SRC_0001_CONFIG)
    articles = adapter.parse_feed(SAMPLE_RSS_TEXT)
    assert len(articles) == 2
    assert all(isinstance(a, RawArticle) for a in articles)
    titles = [a.title_original for a in articles]
    assert "Engineered stone silicosis lawsuit filed in California court" in titles
    assert articles[0].source_url == "https://example.com/news/silicosis-lawsuit-california"
    assert articles[0].source_name == "Google News RSS (English)"
    assert articles[0].language == "en"
    assert articles[0].published_at == "2026-07-30T09:00:00Z"


def test_google_rss_adapter_collect_uses_injected_http_get_when_enabled():
    calls: list[str] = []

    def fake_http_get(url: str) -> str:
        calls.append(url)
        return SAMPLE_RSS_TEXT

    adapter = GoogleRSSAdapter(SRC_0001_CONFIG, enabled=True, http_get=fake_http_get)
    articles = adapter.collect("engineered stone silicosis")
    assert len(articles) == 2
    assert len(calls) == 1
    assert "engineered stone silicosis" in calls[0]


@pytest.mark.parametrize(
    "adapter_cls,source_id",
    [
        (NaverNewsAdapter, "SRC-0003"),
        (DartFilingAdapter, "SRC-0004"),
        (GovernmentPressReleaseAdapter, "SRC-0005"),
        (IRPageAdapter, "SRC-0006"),
    ],
)
def test_future_adapters_are_source_adapters_but_not_implemented(adapter_cls, source_id):
    adapter = adapter_cls({"source_id": source_id, "active": False})
    assert isinstance(adapter, SourceAdapter)
    with pytest.raises(NotImplementedError):
        adapter.collect("query")


def test_adapters_are_interchangeable_same_call_signature():
    """Adapter 교체 가능성 검증: 동일한 시그니처로 여러 Adapter를 리스트에 담아 다룰 수 있다."""
    adapters: list[SourceAdapter] = [
        GoogleRSSAdapter(SRC_0001_CONFIG, enabled=True, http_get=lambda url: SAMPLE_RSS_TEXT)
    ]
    for adapter in adapters:
        result = adapter.collect("engineered stone silicosis")
        assert all(isinstance(a, RawArticle) for a in result)
