from datetime import datetime, timezone

from adapters.base import RawArticle, SourceAdapterDisabledError
from notifiers import EmailNotifier, TelegramNotifier
from providers.mock_provider import MockProvider
from run_news_collection import build_group_query, run
from storage.local_jsonl_storage import LocalJSONLStorage

GROUPS = [
    {
        "group_id": "GRP-0001",
        "topic_id": "TOP-0001",
        "group_name": "실리코시스",
        "include_keywords": ["silicosis", "engineered stone"],
        "exclude_keywords": ["sports"],
        "ai_instructions": "LX하우시스 관점에서 판단한다.",
        "sources": ["SRC-0001"],
        "enabled": True,
    }
]

RELEVANT_ARTICLE = RawArticle(
    title_original="Engineered stone silicosis lawsuit filed in California",
    source_url="https://example.com/silicosis-a",
    source_name="Example News",
    published_at="2026-08-07T09:00:00Z",
    language="en",
)
UNRELATED_ARTICLE = RawArticle(
    title_original="Local weather forecast update",
    source_url="https://example.com/weather",
    source_name="Example News",
    published_at="2026-08-07T09:00:00Z",
    language="en",
)
EXCLUDED_ARTICLE = RawArticle(
    title_original="Sports update: silicosis charity match",
    source_url="https://example.com/sports",
    source_name="Example News",
    published_at="2026-08-07T09:00:00Z",
    language="en",
)


class _FakeAdapter:
    def __init__(self, articles):
        self._articles = articles
        self.queries: list[str] = []

    def collect(self, query: str):
        self.queries.append(query)
        return self._articles


class _DisabledAdapter:
    def collect(self, query: str):
        raise SourceAdapterDisabledError("disabled in test")


def test_build_group_query_quotes_multi_word_keywords():
    query = build_group_query(GROUPS[0])
    assert query == '"engineered stone" OR silicosis' or query == 'silicosis OR "engineered stone"'
    assert '"engineered stone"' in query


def test_run_accumulates_all_articles_including_rejected(tmp_path):
    storage = LocalJSONLStorage(tmp_path)
    fake_adapter = _FakeAdapter([RELEVANT_ARTICLE, UNRELATED_ARTICLE, EXCLUDED_ARTICLE])

    result = run(
        provider=MockProvider(),
        adapters_by_source_id={"SRC-0001": fake_adapter},
        groups=GROUPS,
        email_notifier=EmailNotifier(),
        telegram_notifier=TelegramNotifier(),
        storage=storage,
        now=datetime(2026, 8, 7, tzinfo=timezone.utc),
        verbose=False,
    )

    all_articles = storage.load_all("ARTICLE_DB")
    assert len(all_articles) == 3  # 전부 적재 — 탈락해도 버리지 않는다
    statuses = {a["title_original"]: a["status"] for a in all_articles}
    assert statuses[RELEVANT_ARTICLE.title_original] in ("classified", "analyzed")
    assert statuses[UNRELATED_ARTICLE.title_original] == "rejected"
    assert statuses[EXCLUDED_ARTICLE.title_original] == "rejected"
    assert result["counters"]["collected"] == 3
    assert result["counters"]["stored"] == 3


def test_run_deep_analyzes_needs_deep_analysis_articles_and_builds_digest(tmp_path):
    storage = LocalJSONLStorage(tmp_path)
    fake_adapter = _FakeAdapter([RELEVANT_ARTICLE])

    result = run(
        provider=MockProvider(),
        adapters_by_source_id={"SRC-0001": fake_adapter},
        groups=GROUPS,
        storage=storage,
        now=datetime(2026, 8, 7, tzinfo=timezone.utc),
        verbose=False,
    )

    intelligence_records = storage.load_all("INTELLIGENCE_DB")
    assert len(intelligence_records) == 1
    assert intelligence_records[0]["importance_level"] in ("긴급", "중요", "참고")
    assert len(result["digest_records"]) == 1
    assert result["email_result"].sent is False  # test_mode 기본값 — dry-run


def test_run_deduplicates_same_canonical_url_across_groups(tmp_path):
    storage = LocalJSONLStorage(tmp_path)
    duplicate_group = {**GROUPS[0], "group_id": "GRP-0002"}
    fake_adapter = _FakeAdapter([RELEVANT_ARTICLE])

    run(
        provider=MockProvider(),
        adapters_by_source_id={"SRC-0001": fake_adapter},
        groups=[GROUPS[0], duplicate_group],
        storage=storage,
        now=datetime(2026, 8, 7, tzinfo=timezone.utc),
        verbose=False,
    )

    assert len(storage.load_all("ARTICLE_DB")) == 1  # 같은 URL은 한 번만 적재


def test_run_skips_disabled_adapter_without_crashing(tmp_path):
    storage = LocalJSONLStorage(tmp_path)
    result = run(
        provider=MockProvider(),
        adapters_by_source_id={"SRC-0001": _DisabledAdapter()},
        groups=GROUPS,
        storage=storage,
        now=datetime(2026, 8, 7, tzinfo=timezone.utc),
        verbose=False,
    )
    assert result["counters"]["collected"] == 0
    assert storage.load_all("ARTICLE_DB") == []


def test_run_writes_dashboard_html(tmp_path):
    storage = LocalJSONLStorage(tmp_path)
    result = run(
        provider=MockProvider(),
        adapters_by_source_id={"SRC-0001": _FakeAdapter([RELEVANT_ARTICLE])},
        groups=GROUPS,
        storage=storage,
        now=datetime(2026, 8, 7, tzinfo=timezone.utc),
        verbose=False,
    )
    assert (tmp_path / "dashboard.html").exists()
    assert result["dashboard_path"] == str(tmp_path / "dashboard.html")
