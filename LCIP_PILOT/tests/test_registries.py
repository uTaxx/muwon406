"""Round 7 — RegistryManager 통합 검증.

Architect Review Round 7 지시: "Company/Source/Knowledge가 각자 따로 존재한다 — Registry
관리 방식을 통일한다." 이 테스트는 7개 Registry(Company/Source/Model/Prompt/Workflow/
Config/Storage)가 동일한 Interface(list_entries/get/count)를 통해 조회 가능한지, 그리고
기존 원본 파일(YAML)을 그대로 반영하는지(새 데이터 사본을 만들지 않는지) 검증한다.
"""
from __future__ import annotations

from _common import load_yaml
from registries import (
    ConfigRegistryAdapter,
    ModelRegistryAdapter,
    PromptRegistryAdapter,
    Registry,
    RegistryManager,
    StorageRegistryAdapter,
    UnknownRegistryError,
)
from registries.yaml_list_registry import (
    CompanyRegistry,
    SourceRegistry,
    TechnicalDebtRegistry,
    WorkflowRegistry,
)


def test_registry_manager_exposes_all_8_registries():
    manager = RegistryManager()
    assert set(manager.registry_ids()) == {
        "company", "source", "model", "prompt", "workflow", "config", "storage",
        "technical_debt",
    }


def test_registry_manager_get_registry_raises_for_unknown_id():
    manager = RegistryManager()
    try:
        manager.get_registry("no_such_registry")
        assert False, "should have raised"
    except UnknownRegistryError:
        pass


def test_all_registries_are_registry_instances():
    manager = RegistryManager()
    for registry_id in manager.registry_ids():
        assert isinstance(manager.get_registry(registry_id), Registry)


def test_company_registry_matches_underlying_yaml_count():
    expected = len(load_yaml("config/company_registry.yaml")["companies"])
    assert CompanyRegistry().count() == expected


def test_company_registry_get_returns_none_for_unregistered_company():
    assert CompanyRegistry().get("NOT_A_REAL_COMPANY_ID") is None


def test_company_registry_get_returns_known_entry():
    entry = CompanyRegistry().get("LX_HAUSYS")
    assert entry is not None
    assert entry["display_name"] == "LX Hausys"


def test_source_registry_matches_underlying_yaml_count():
    expected = len(load_yaml("config/sources.yaml")["sources"])
    assert SourceRegistry().count() == expected


def test_workflow_registry_matches_underlying_yaml_count():
    expected = len(load_yaml("config/workflow_registry.yaml")["workflows"])
    assert WorkflowRegistry().count() == expected


def test_model_registry_adapter_lists_three_tiers():
    entries = ModelRegistryAdapter().list_entries()
    tiers = {e["tier"] for e in entries}
    assert tiers == {"classification", "deep_analysis", "future"}


def test_model_registry_adapter_get_merges_tier_name_into_entry():
    entry = ModelRegistryAdapter().get("classification")
    assert entry["tier"] == "classification"
    assert "model_env" in entry


def test_model_registry_adapter_get_unknown_tier_returns_none():
    assert ModelRegistryAdapter().get("no_such_tier") is None


def test_prompt_registry_adapter_lists_all_prompt_files():
    from pathlib import Path

    from _common import project_root

    expected = {p.stem for p in (project_root() / "prompts").glob("*.md")}
    entries = PromptRegistryAdapter().list_entries()
    assert {e["prompt_id"] for e in entries} == expected


def test_prompt_registry_adapter_get_returns_version():
    entry = PromptRegistryAdapter().get("risk_analysis")
    assert entry is not None
    assert entry["prompt_version"] != "unknown"


def test_prompt_registry_adapter_get_unknown_prompt_returns_none():
    assert PromptRegistryAdapter().get("no_such_prompt") is None


def test_config_registry_adapter_includes_known_config_files():
    ids = {e["config_id"] for e in ConfigRegistryAdapter().list_entries()}
    assert {"company_registry", "sources", "feature_flags", "model_registry"} <= ids


def test_storage_registry_adapter_lists_three_backends_with_local_default():
    entries = StorageRegistryAdapter().list_entries()
    ids = {e["storage_id"] for e in entries}
    assert ids == {"local_jsonl", "google_sheets", "future_database"}
    local = StorageRegistryAdapter().get("local_jsonl")
    assert local["enabled_by_default"] is True


def test_technical_debt_registry_matches_underlying_yaml_count():
    expected = len(load_yaml("config/technical_debt_registry.yaml")["technical_debt"])
    assert TechnicalDebtRegistry().count() == expected


def test_technical_debt_registry_entries_have_round_8_project_management_fields():
    """Round 8 지시: "Severity/Priority/Estimated Time/Owner를 추가한다 — 실제
    프로젝트 관리가 가능해야 한다." 4개 필드 전부 채워져 있는지 검증한다."""
    for entry in TechnicalDebtRegistry().list_entries():
        for field in ("severity", "priority", "estimated_time", "owner", "status"):
            assert entry.get(field), f"{entry.get('debt_id')}의 '{field}' 필드가 비어 있음"
        assert entry["severity"] in {"critical", "high", "medium", "low"}
        assert entry["priority"] in {"P0", "P1", "P2"}
        assert entry["status"] in {"open", "in_progress", "resolved"}


def test_technical_debt_registry_get_returns_known_entry():
    entry = TechnicalDebtRegistry().get("TD-001")
    assert entry is not None
    assert entry["severity"] == "low"


def test_technical_debt_registry_get_returns_none_for_unknown_id():
    assert TechnicalDebtRegistry().get("TD-999-NOT-REAL") is None


def test_registry_manager_summary_matches_individual_counts():
    manager = RegistryManager()
    summary = manager.summary()
    for registry_id in manager.registry_ids():
        assert summary[registry_id] == manager.get_registry(registry_id).count()


# --- Round 8: Validation / Integrity Check / Dependency Check ---


def test_validate_all_passes_on_real_registries():
    """실제 config/yaml/prompt 파일들은 이미 정상 상태여야 한다 — 회귀 감시용."""
    manager = RegistryManager()
    assert manager.validate_all() == []


def test_validate_detects_missing_id_field():
    manager = RegistryManager()
    from registries import validation

    errors = validation.validate_registry("company", [{"display_name": "이름만 있고 company_id 없음"}])
    assert len(errors) == 1
    assert "company_id" in errors[0]


def test_check_integrity_detects_duplicate_ids():
    from registries import validation

    entries = [{"source_id": "SRC-DUP"}, {"source_id": "SRC-DUP"}, {"source_id": "SRC-UNIQUE"}]
    errors = validation.check_registry_integrity("source", entries)
    assert len(errors) == 1
    assert "SRC-DUP" in errors[0]


def test_check_integrity_passes_when_no_duplicates():
    from registries import validation

    entries = [{"source_id": "SRC-0001"}, {"source_id": "SRC-0002"}]
    assert validation.check_registry_integrity("source", entries) == []


def test_check_dependencies_detects_unknown_company_id_in_topics(monkeypatch):
    class _FakeCompanyRegistry:
        def list_entries(self):
            return [{"company_id": "LX_HAUSYS"}]

    class _FakeManager:
        def get_registry(self, registry_id):
            assert registry_id == "company"
            return _FakeCompanyRegistry()

    from registries import validation

    def _fake_load_yaml(path):
        assert path == "config/topics.yaml"
        return {"topics": [{"topic_id": "TOP-TEST", "related_lx_companies": ["NOT_REGISTERED"]}]}

    monkeypatch.setattr(validation, "load_yaml", _fake_load_yaml)
    errors = validation.check_cross_registry_dependencies(_FakeManager())
    assert any("NOT_REGISTERED" in e for e in errors)


def test_registry_manager_exposes_validate_check_integrity_and_check_dependencies():
    manager = RegistryManager()
    assert manager.validate() == []
    assert manager.check_integrity() == []
    assert manager.check_dependencies() == []
