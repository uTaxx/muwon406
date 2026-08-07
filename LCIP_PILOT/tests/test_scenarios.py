"""Round 7 — Scenario 5종 검증.

Architect Review Round 7 지시: "Pilot Demo가 아니라 Scenario 개념으로 변경한다 ... 모든
Scenario는 독립 실행 가능해야 한다." 각 Scenario 모듈의 `run()`을 직접 호출해(서브프로세스
없이) 전 구간이 실제로 동작하는지, 그리고 서로 다른 Scenario를 import 순서와 무관하게
개별적으로 실행할 수 있는지 검증한다.
"""
from __future__ import annotations

import json

from scenarios import (
    scenario_1_news_analysis,
    scenario_2_quick_company_scan,
    scenario_3_investment_review,
    scenario_4_policy_impact,
    scenario_5_competitor_change_detection,
)


def test_scenario_1_runs_end_to_end_and_returns_article_and_intelligence():
    result = scenario_1_news_analysis.run(verbose=False)
    assert result["article"]["article_id"].startswith("ART-")
    assert result["intelligence"]["intelligence_id"].startswith("INT-")
    assert result["dashboard_path"].endswith("dashboard.html")


def test_scenario_2_runs_independently_of_scenario_1():
    result = scenario_2_quick_company_scan.run("LX Hausys", verbose=False)
    assert result["company"].resolved is True
    assert result["quick_report"]["target_company"] == "LX Hausys"
    assert "financial_snapshot" in result["review_input"]


def test_scenario_2_handles_unregistered_company_honestly():
    result = scenario_2_quick_company_scan.run("존재하지않는가상회사12345", verbose=False)
    assert result["company"].resolved is False


def test_scenario_3_runs_independently_and_internally_calls_scenario_2():
    result = scenario_3_investment_review.run("LX Hausys", verbose=False)
    assert "peer_average" in result["review"]
    assert result["review"]["recommendation"]["signal"]
    assert result["quick_report"]["target_company"] == "LX Hausys"


def test_scenario_4_runs_independently_and_matches_policy_schema():
    import json as _json
    from pathlib import Path

    schema = _json.loads(
        (Path(__file__).resolve().parent.parent / "schemas" / "claude_output.schema.json").read_text()
    )
    result = scenario_4_policy_impact.run(verbose=False)
    assert result["analysis"]["regulatory_stage"] in schema["$defs"]["policy_analysis_output"][
        "properties"
    ]["regulatory_stage"]["enum"]


def test_scenario_5_first_run_reports_no_baseline(tmp_path, monkeypatch):
    monkeypatch.setattr(scenario_5_competitor_change_detection, "project_root", lambda: tmp_path)
    result = scenario_5_competitor_change_detection.run("CAESARSTONE", verbose=False)
    assert result["is_first_snapshot"] is True
    assert result["changed_fields"] == []


def test_scenario_5_second_run_with_identical_mock_output_reports_no_change(tmp_path, monkeypatch):
    monkeypatch.setattr(scenario_5_competitor_change_detection, "project_root", lambda: tmp_path)
    scenario_5_competitor_change_detection.run("COSENTINO", verbose=False)
    second = scenario_5_competitor_change_detection.run("COSENTINO", verbose=False)
    assert second["is_first_snapshot"] is False
    assert second["changed_fields"] == []


def test_scenario_5_snapshot_file_is_valid_json(tmp_path, monkeypatch):
    monkeypatch.setattr(scenario_5_competitor_change_detection, "project_root", lambda: tmp_path)
    scenario_5_competitor_change_detection.run("CAESARSTONE", verbose=False)
    snapshot_path = scenario_5_competitor_change_detection._latest_snapshot_path("CAESARSTONE")
    assert snapshot_path.exists()
    json.loads(snapshot_path.read_text(encoding="utf-8"))


def test_all_5_scenario_modules_expose_a_run_function():
    for module in (
        scenario_1_news_analysis,
        scenario_2_quick_company_scan,
        scenario_3_investment_review,
        scenario_4_policy_impact,
        scenario_5_competitor_change_detection,
    ):
        assert callable(module.run)
