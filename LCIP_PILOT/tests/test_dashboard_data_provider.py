import json
from datetime import datetime, timezone
from pathlib import Path

from dashboard_data_provider import (
    DashboardDataProvider,
    PipelineDashboardDataProvider,
    StaticJSONDataProvider,
)
from storage.local_jsonl_storage import LocalJSONLStorage

ROOT = Path(__file__).resolve().parent.parent


def test_static_json_data_provider_is_a_dashboard_data_provider():
    provider = StaticJSONDataProvider(ROOT / "dashboard" / "sample_data.json")
    assert isinstance(provider, DashboardDataProvider)


def test_static_json_data_provider_loads_sample_data():
    provider = StaticJSONDataProvider(ROOT / "dashboard" / "sample_data.json")
    data = provider.get_data()
    assert "tracker_rows" in data
    expected = json.loads((ROOT / "dashboard" / "sample_data.json").read_text(encoding="utf-8"))
    assert data == expected


def test_pipeline_dashboard_data_provider_reads_from_storage(tmp_path):
    storage = LocalJSONLStorage(tmp_path)
    now = datetime(2026, 8, 5, tzinfo=timezone.utc)
    article = {
        "article_id": "ART-20260805-0001",
        "title_original": "샘플 기사",
        "source_url": "https://example.com/a",
        "published_at": "2026-08-05T00:00:00Z",
        "country": "US",
        "related_companies": [],
        "event_type": "litigation",
        "litigation_amount_total_usd": None,
        "claimant_count": None,
        "average_amount_per_person_usd": None,
        "status": "collected",
        "is_new_change": True,
    }
    storage.append("ARTICLE_DB", article)

    provider = PipelineDashboardDataProvider(
        storage, topic_display_name="테스트 Topic", generated_at_kst="2026-08-05 09:00"
    )
    data = provider.get_data()
    assert data["topic_display_name"] == "테스트 Topic"
    assert len(data["tracker_rows"]) == 1
    assert data["tracker_rows"][0]["title"] == "샘플 기사"


def test_pipeline_dashboard_data_provider_empty_storage_returns_empty_tracker(tmp_path):
    storage = LocalJSONLStorage(tmp_path)
    provider = PipelineDashboardDataProvider(storage, "Topic", "2026-08-05 09:00")
    data = provider.get_data()
    assert data["tracker_rows"] == []
