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
    assert "today_intelligence" in data
    expected = json.loads((ROOT / "dashboard" / "sample_data.json").read_text(encoding="utf-8"))
    assert data == expected


def test_pipeline_dashboard_data_provider_reads_intelligence_from_storage(tmp_path):
    storage = LocalJSONLStorage(tmp_path)
    storage.append(
        "INTELLIGENCE_DB",
        {
            "intelligence_id": "INT-20260805-0001",
            "article_ids": ["ART-20260805-0001"],
            "mission_category": ["risk_management"],
            "fact_summary": "샘플 기사 관련 사실 요약",
            "confidence_score": "medium",
            "evidence": ["https://example.com/a"],
            "created_at": "2026-08-05T00:00:00Z",
        },
    )

    provider = PipelineDashboardDataProvider(
        storage, topic_display_name="테스트 Topic", generated_at_kst="2026-08-05 09:00"
    )
    data = provider.get_data()
    assert data["topic_display_name"] == "테스트 Topic"
    assert len(data["today_intelligence"]) == 1
    assert len(data["critical_risk"]) == 1
    assert data["today_intelligence"][0]["fact_summary"] == "샘플 기사 관련 사실 요약"


def test_pipeline_dashboard_data_provider_reads_company_scan_from_storage(tmp_path):
    storage = LocalJSONLStorage(tmp_path)
    storage.append(
        "COMPANY_SCAN_DB",
        {
            "company_id": "LX_HAUSYS",
            "target_company": "LX Hausys",
            "scan_date": "2026-08-07",
            "confidence": "low",
            "recommendation_signal": "monitor",
            "company_intelligence_score": {"overall": 42.3},
        },
    )
    provider = PipelineDashboardDataProvider(storage, "Topic", "2026-08-05 09:00")
    data = provider.get_data()
    assert len(data["quick_company_scan"]) == 1
    assert data["quick_company_scan"][0]["intelligence_score"] == 42.3
    assert len(data["investment_review"]) == 1
    assert data["investment_review"][0]["recommendation_signal"] == "monitor"


def test_pipeline_dashboard_data_provider_includes_source_health_from_config(tmp_path):
    storage = LocalJSONLStorage(tmp_path)
    provider = PipelineDashboardDataProvider(storage, "Topic", "2026-08-05 09:00")
    data = provider.get_data()
    assert len(data["source_health"]) >= 11  # config/sources.yaml — Round 6 TASK-K03 기준 11개


def test_pipeline_dashboard_data_provider_empty_storage_returns_empty_lists(tmp_path):
    storage = LocalJSONLStorage(tmp_path)
    provider = PipelineDashboardDataProvider(storage, "Topic", "2026-08-05 09:00")
    data = provider.get_data()
    assert data["today_intelligence"] == []
    assert data["quick_company_scan"] == []
