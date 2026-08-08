import json
from datetime import datetime, timezone
from pathlib import Path

import reference_library
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
    assert data["today_intelligence"][0]["핵심 내용"] == "샘플 기사 관련 사실 요약"


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
    assert data["quick_company_scan"][0]["종합 점수"] == "42.3/100"
    assert len(data["investment_review"]) == 1
    assert data["investment_review"][0]["추천 신호"] == "monitor"


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


def test_pipeline_dashboard_data_provider_includes_reference_library_summary(tmp_path, monkeypatch):
    """Round 12 TASK 2: Home Dashboard "Reference Library" 카드가 실제 Reference
    Library 색인을 반영해야 한다. 이 Provider가 유일하게 reference_library 파일시스템을
    읽는 지점이므로, 여기서만 `reference_library.project_root`를 격리하면 된다."""
    monkeypatch.setattr(reference_library, "project_root", lambda: tmp_path / "reflib_root")
    reference_library.ensure_directories()
    reference_library.save_index([{
        "reference_id": "REF-0001", "title": "LX Hausys 사업보고서", "company": "LX_HAUSYS",
        "document_type": "annual_report", "source_type": "official_company", "source_url": None,
        "file_path": None, "published_date": "2024-03-01", "added_at": "2026-08-01T00:00:00Z",
        "official_source": True, "reliability_grade": "A", "status": "active",
        "latest_version": True, "applicable_services": [], "last_verified": None,
    }])

    storage = LocalJSONLStorage(tmp_path / "pilot_data")
    provider = PipelineDashboardDataProvider(storage, "Topic", "2026-08-05 09:00")
    data = provider.get_data()

    assert len(data["reference_library_rows"]) == 1
    assert data["reference_library_rows"][0]["등록 자료 수"] == "1건"
    assert data["reference_library_rows"][0]["최신 자료"] == "LX Hausys 사업보고서"


def test_pipeline_dashboard_data_provider_reference_library_empty_by_default(tmp_path, monkeypatch):
    monkeypatch.setattr(reference_library, "project_root", lambda: tmp_path / "reflib_root")
    storage = LocalJSONLStorage(tmp_path / "pilot_data")
    provider = PipelineDashboardDataProvider(storage, "Topic", "2026-08-05 09:00")
    data = provider.get_data()
    assert data["reference_library_rows"] == []
