"""Round 7 — Scenario 5종 검증.

Architect Review Round 7 지시: "Pilot Demo가 아니라 Scenario 개념으로 변경한다 ... 모든
Scenario는 독립 실행 가능해야 한다." 각 Scenario 모듈의 `run()`을 직접 호출해(서브프로세스
없이) 전 구간이 실제로 동작하는지, 그리고 서로 다른 Scenario를 import 순서와 무관하게
개별적으로 실행할 수 있는지 검증한다.
"""
from __future__ import annotations

import json
from pathlib import Path

import reference_library
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


def test_scenario_1_includes_email_preview_step():
    """Round 9 지시: "뉴스 1건→Rule Filter→AI 분석→Dashboard→Email Preview→완료"를
    하나의 Pipeline으로 만든다. dry-run(test_mode)이라 실제 발송은 없어야 한다."""
    result = scenario_1_news_analysis.run(verbose=False)
    preview = result["email_preview"]
    assert preview.sent is False
    assert preview.test_mode is True
    assert preview.channel == "email"
    assert result["article"]["title_original"] in preview.subject


def test_scenario_1_returns_empty_reference_entries_when_none_registered():
    result = scenario_1_news_analysis.run(verbose=False)
    assert result["reference_entries"] == []


def test_scenario_1_includes_registered_reference_for_related_company(tmp_path, monkeypatch):
    """Round 12 TASK 2: Topic의 related_lx_companies(LX_HAUSYS) 기준으로 Reference
    Library `active/` 자료를 조회해 반환해야 한다."""
    monkeypatch.setattr(scenario_1_news_analysis, "project_root", lambda: tmp_path)
    monkeypatch.setattr(reference_library, "project_root", lambda: tmp_path)

    reference_library.ensure_directories()
    reference_library.save_index([{
        "reference_id": "REF-0001",
        "title": "LX Hausys 사업보고서",
        "company": "LX_HAUSYS",
        "document_type": "annual_report",
        "source_type": "official_company",
        "source_url": None,
        "file_path": None,
        "published_date": "2024-03-01",
        "added_at": "2026-08-01T00:00:00Z",
        "official_source": True,
        "reliability_grade": "A",
        "status": "active",
        "latest_version": True,
        "applicable_services": [],
        "last_verified": None,
    }])

    result = scenario_1_news_analysis.run(verbose=False)
    assert [e["reference_id"] for e in result["reference_entries"]] == ["REF-0001"]


def test_scenario_2_runs_independently_of_scenario_1():
    result = scenario_2_quick_company_scan.run("LX Hausys", verbose=False)
    assert result["company"].resolved is True
    assert result["quick_report"]["target_company"] == "LX Hausys"
    assert "financial_snapshot" in result["review_input"]
    assert result["sources"]  # Round 8: Source Selection 결과도 반환한다


def test_scenario_2_includes_knowledge_retrieval_step():
    """Round 8 지시: Input -> Company Registry -> Knowledge Retrieval -> Source
    Selection 순서를 실제로 거치는지 확인한다."""
    result = scenario_2_quick_company_scan.run("LX Hausys", verbose=False)
    assert "Knowledge Base 발췌 없음" not in str(result["quick_report"].get("unknowns", []))


def test_scenario_2_handles_unregistered_company_honestly():
    result = scenario_2_quick_company_scan.run("존재하지않는가상회사12345", verbose=False)
    assert result["company"].resolved is False


def test_scenario_2_returns_empty_reference_entries_when_none_registered():
    """Round 12 TASK 2: Reference Library가 비어 있으면 정직하게 빈 목록을 반환한다."""
    result = scenario_2_quick_company_scan.run("LX Hausys", verbose=False)
    assert result["reference_entries"] == []


def test_scenario_3_export_includes_registered_reference_citations(tmp_path, monkeypatch):
    """Round 12 TASK 2 완료조건("결과물에서 어떤 Reference를 사용했는지 표시"): active/에
    등록된 자료가 있으면 Markdown/Executive Report의 "참조 근거" 절과 COMPANY_SCAN_DB의
    reference_ids_used에 반영돼야 한다."""
    monkeypatch.setattr(scenario_3_investment_review, "project_root", lambda: tmp_path)
    monkeypatch.setattr(reference_library, "project_root", lambda: tmp_path)

    reference_library.ensure_directories()
    entries = [{
        "reference_id": "REF-0001",
        "title": "LX Hausys 지속가능경영보고서 2024",
        "company": "LX_HAUSYS",
        "document_type": "sustainability_report",
        "source_type": "official_company",
        "source_url": "https://example.com/lx-hausys-2024.html",
        "file_path": None,
        "published_date": "2024-05-01",
        "added_at": "2026-08-01T00:00:00Z",
        "official_source": True,
        "reliability_grade": "A",
        "status": "active",
        "latest_version": True,
        "applicable_services": [],
        "last_verified": None,
    }]
    reference_library.save_index(entries)

    result = scenario_3_investment_review.run("LX Hausys", verbose=False)

    assert len(result["reference_entries"]) == 1
    assert result["reference_entries"][0]["reference_id"] == "REF-0001"

    md_text = Path(result["export"]["md_path"]).read_text(encoding="utf-8")
    assert "참조 근거 (Reference Library — AI 참고자료)" in md_text
    assert "LX Hausys 지속가능경영보고서 2024" in md_text
    assert "AI 학습 완료" not in md_text

    executive_html = Path(result["export"]["executive_report_path"]).read_text(encoding="utf-8")
    assert "LX Hausys 지속가능경영보고서 2024" in executive_html

    from storage.local_jsonl_storage import LocalJSONLStorage

    storage = LocalJSONLStorage(tmp_path / "output" / "pilot_data")
    records = storage.load_all(scenario_3_investment_review.COMPANY_SCAN_DB)
    assert records[0]["reference_ids_used"] == ["REF-0001"]


def test_scenario_3_runs_independently_and_internally_calls_scenario_2():
    result = scenario_3_investment_review.run("LX Hausys", verbose=False)
    assert "peer_average" in result["review"]
    assert result["review"]["recommendation"]["signal"]
    assert result["quick_report"]["target_company"] == "LX Hausys"


def test_scenario_3_computes_company_intelligence_score():
    result = scenario_3_investment_review.run("LX Hausys", verbose=False)
    score = result["intelligence_score"]
    assert 0.0 <= score["overall"] <= 100.0
    for key in (
        "business_understanding", "market_position", "financial_visibility",
        "strategic_importance", "risk_visibility", "source_reliability",
        "knowledge_coverage",
    ):
        assert key in score


def test_scenario_3_exports_json_and_markdown():
    result = scenario_3_investment_review.run("LX Hausys", verbose=False)
    assert result["export"]["json_path"].exists()
    assert result["export"]["md_path"].exists()


def test_scenario_3_stores_result_for_dashboard_widget(tmp_path, monkeypatch):
    """Dashboard Widget 반영 단계 — COMPANY_SCAN_DB에 실제로 저장되는지 확인한다."""
    monkeypatch.setattr(scenario_3_investment_review, "project_root", lambda: tmp_path)
    scenario_3_investment_review.run("LX Hausys", verbose=False)

    from storage.local_jsonl_storage import LocalJSONLStorage

    storage = LocalJSONLStorage(tmp_path / "output" / "pilot_data")
    records = storage.load_all(scenario_3_investment_review.COMPANY_SCAN_DB)
    assert len(records) == 1
    assert records[0]["company_id"] == "LX_HAUSYS"
    assert "company_intelligence_score" in records[0]


def test_scenario_3_updates_home_dashboard_without_needing_scenario_1(tmp_path, monkeypatch):
    """Round 12 TASK 1(TD-006): "Scenario 3 실행 직후 Dashboard에 해당 회사가 보인다.
    Scenario 1을 별도로 실행할 필요가 없다." """
    monkeypatch.setattr(scenario_3_investment_review, "project_root", lambda: tmp_path)
    result = scenario_3_investment_review.run("LX Hausys", verbose=False)

    dashboard_path = Path(result["dashboard_path"])
    assert dashboard_path.exists()
    assert dashboard_path.name == "dashboard.html"
    html = dashboard_path.read_text(encoding="utf-8")
    assert "LX Hausys" in html
    assert "{{" not in html


def test_scenario_3_dashboard_update_preserves_existing_news_intelligence(tmp_path, monkeypatch):
    """완료조건: "기존 News Intelligence 데이터가 삭제되지 않는다." Scenario 1을 먼저
    실행해 뉴스 Intelligence를 쌓아 두고, Scenario 3을 실행해도 그대로 남아 있어야 한다."""
    monkeypatch.setattr(scenario_1_news_analysis, "project_root", lambda: tmp_path)
    monkeypatch.setattr(scenario_3_investment_review, "project_root", lambda: tmp_path)

    scenario_1_news_analysis.run(verbose=False)

    from storage.local_jsonl_storage import LocalJSONLStorage

    storage = LocalJSONLStorage(tmp_path / "output" / "pilot_data")
    intelligence_before = storage.load_all("INTELLIGENCE_DB")
    assert len(intelligence_before) == 1

    result = scenario_3_investment_review.run("KCC", verbose=False)

    intelligence_after = storage.load_all("INTELLIGENCE_DB")
    assert intelligence_after == intelligence_before  # 삭제되지 않았다

    html = Path(result["dashboard_path"]).read_text(encoding="utf-8")
    assert "KCC" in html  # 새로 스캔한 회사도 반영됐다


def test_scenario_3_repeated_run_same_company_does_not_duplicate_in_dashboard(tmp_path, monkeypatch):
    """완료조건: "같은 회사 반복 실행 시 무한 중복 누적하지 않는다." COMPANY_SCAN_DB
    Storage 자체는 감사 목적으로 계속 쌓이지만(Round 9 원칙), Dashboard 위젯에는 같은
    회사가 여러 번 나열되지 않아야 한다."""
    monkeypatch.setattr(scenario_3_investment_review, "project_root", lambda: tmp_path)

    scenario_3_investment_review.run("LX Hausys", verbose=False)
    result = scenario_3_investment_review.run("LX Hausys", verbose=False)

    from storage.local_jsonl_storage import LocalJSONLStorage

    storage = LocalJSONLStorage(tmp_path / "output" / "pilot_data")
    assert len(storage.load_all(scenario_3_investment_review.COMPANY_SCAN_DB)) == 2  # 이력은 보존

    html = Path(result["dashboard_path"]).read_text(encoding="utf-8")
    # Home 카드 2곳(최근 분석 결과 - Scan/Investment) + 본문 섹션 2곳(Quick Company
    # Scan/Investment Review) = 정확히 4회. Dedup이 깨지면 반복 실행 횟수만큼 늘어난다.
    assert html.count("LX Hausys") == 4


def test_scenario_3_main_prints_result_summary_without_opening_files(tmp_path, monkeypatch, capsys):
    """Round 11 지시: "입력 -> 결과 -> Export까지 클릭 수를 최소화한다." CLI 실행 한 번으로
    파일을 열지 않고도 핵심 결과(점수/추천신호/근거/경로)를 바로 확인할 수 있어야 한다."""
    monkeypatch.setattr(scenario_3_investment_review, "project_root", lambda: tmp_path)
    monkeypatch.setattr("sys.argv", ["scenario_3_investment_review.py", "LX Hausys"])

    scenario_3_investment_review.main()

    out = capsys.readouterr().out
    assert "결과 요약" in out
    assert "회사명: LX Hausys" in out
    assert "Company Intelligence Score:" in out
    assert "추천 신호:" in out
    assert "추천 사유:" in out
    assert "보고서(Markdown, 상세):" in out
    assert "보고서(JSON):" in out
    assert "Executive Report(HTML" in out


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
