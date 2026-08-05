import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WF_DIR = ROOT / "n8n" / "workflows"

EXPECTED_FILES = [
    "WF-P01-config-loader.json",
    "WF-P02-news-collector.json",
    "WF-P03-public-source-collector.json",
    "WF-P04-relevance-classifier.json",
    "WF-P05-risk-analysis.json",
    "WF-P06-dashboard-builder.json",
    "WF-P07-notification.json",
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
