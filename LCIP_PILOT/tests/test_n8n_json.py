import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WF_DIR = ROOT / "n8n" / "workflows"

# ADR-007(Round 2 Q4)로 11개 -> 5개 워크플로우로 통합. ADR-008(Round 3 Q1)로 Source
# Health/Cost Guard/NL Admin은 원래 번호(WF-P08/P09/P10)를 유지 (재배정하지 않음).
EXPECTED_FILES = [
    "WF-P01-master-pipeline.json",
    "WF-P08-source-health.json",
    "WF-P09-cost-guard.json",
    "WF-P10-natural-language-admin.json",
    "WF-P99-error-handler.json",
]


def test_all_expected_files_exist():
    for name in EXPECTED_FILES:
        assert (WF_DIR / name).exists(), f"{name} 없음"


def _load(name):
    return json.loads((WF_DIR / name).read_text(encoding="utf-8"))


def test_all_workflows_parse_as_valid_json():
    for name in EXPECTED_FILES:
        data = _load(name)
        assert "nodes" in data and "connections" in data


def test_all_workflows_are_inactive():
    for name in EXPECTED_FILES:
        data = _load(name)
        assert data["active"] is False, f"{name}는 active:false여야 한다"


def test_no_hardcoded_credential_ids():
    for name in EXPECTED_FILES:
        data = _load(name)
        for node in data["nodes"]:
            for cred_type, cred_val in node.get("credentials", {}).items():
                assert "id" not in cred_val, f"{name}/{node['name']}: credential id 하드코딩 금지"
                assert cred_val.get("name", "").startswith("PLACEHOLDER_CRED_"), (
                    f"{name}/{node['name']}: credential name이 placeholder 형식이 아님"
                )


def test_has_manual_or_error_trigger():
    trigger_types = {
        "n8n-nodes-base.manualTrigger",
        "n8n-nodes-base.errorTrigger",
        "n8n-nodes-base.executeWorkflowTrigger",
    }
    for name in EXPECTED_FILES:
        data = _load(name)
        node_types = {n["type"] for n in data["nodes"]}
        assert node_types & trigger_types, f"{name}에 Manual/Error/Sub-workflow Trigger가 없음"


def test_error_handler_referenced_except_self():
    for name in EXPECTED_FILES:
        data = _load(name)
        if name == "WF-P99-error-handler.json":
            continue
        assert data.get("settings", {}).get("errorWorkflow") == "LCIP - Error Handler", (
            f"{name}에 errorWorkflow 설정(Error 분기)이 없음"
        )


# --- 뉴스 수집 실체화 라운드(2026-08-08): WF-P01 네이티브 재구현 검증 ---


def test_wf_p01_schedule_has_three_weekday_cron_expressions():
    data = _load("WF-P01-master-pipeline.json")
    schedule_node = next(
        n for n in data["nodes"] if n["type"] == "n8n-nodes-base.scheduleTrigger"
    )
    expressions = {
        entry["expression"] for entry in schedule_node["parameters"]["rule"]["interval"]
    }
    assert expressions == {"0 8 * * 1-5", "0 12 * * 1-5", "30 16 * * 1-5"}


def test_wf_p01_ai_analyze_nodes_are_enabled():
    """뉴스 수집 실체화 라운드 전에는 disabled:true였다 — 이번에 실제 활성화했다."""
    data = _load("WF-P01-master-pipeline.json")
    ai_nodes = [n for n in data["nodes"] if n["name"].startswith("AI Analyze - Claude")]
    assert len(ai_nodes) == 2
    assert all(not n.get("disabled") for n in ai_nodes)


def test_wf_p01_notification_nodes_are_enabled():
    data = _load("WF-P01-master-pipeline.json")
    notif_nodes = [n for n in data["nodes"] if n["name"].startswith("Notification - ")]
    assert len(notif_nodes) >= 2
    assert all(not n.get("disabled") for n in notif_nodes)


def test_wf_p01_has_naver_news_node_not_disabled():
    data = _load("WF-P01-master-pipeline.json")
    naver_node = next(n for n in data["nodes"] if "Naver" in n["name"])
    assert not naver_node.get("disabled")
    assert naver_node["credentials"]["httpHeaderAuth"]["name"] == "PLACEHOLDER_CRED_NaverApi"


def test_wf_p01_dart_and_government_sources_remain_disabled():
    """DART/정부보도자료는 이번 라운드 명시적 범위 밖 — 계속 비활성 상태여야 한다."""
    data = _load("WF-P01-master-pipeline.json")
    public_source_node = next(
        n for n in data["nodes"] if "Public Source" in n["name"]
    )
    assert public_source_node.get("disabled") is True


def test_wf_p01_drive_upload_nodes_remain_disabled():
    data = _load("WF-P01-master-pipeline.json")
    drive_nodes = [n for n in data["nodes"] if n["type"] == "n8n-nodes-base.googleDrive"]
    assert len(drive_nodes) == 2
    assert all(n.get("disabled") is True for n in drive_nodes)


def test_wf_p01_all_node_names_and_ids_are_unique():
    data = _load("WF-P01-master-pipeline.json")
    names = [n["name"] for n in data["nodes"]]
    ids = [n["id"] for n in data["nodes"]]
    assert len(names) == len(set(names))
    assert len(ids) == len(set(ids))


def test_wf_p01_connections_reference_only_existing_nodes():
    data = _load("WF-P01-master-pipeline.json")
    names = {n["name"] for n in data["nodes"]}
    for src, spec in data["connections"].items():
        assert src in names, f"connections에 존재하지 않는 노드 참조: {src}"
        for output in spec["main"]:
            for conn in output:
                assert conn["node"] in names, f"connections에 존재하지 않는 노드 참조: {conn['node']}"
