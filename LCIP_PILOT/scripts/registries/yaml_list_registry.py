"""YAMLListRegistry — `{top_level_key}: [ {id_field: ...}, ... ]` 형태의 YAML을 감싸는
공통 어댑터. Company/Source/Workflow Registry가 전부 이 형태라 하나의 클래스로 재사용한다
(Round 7 지시: 새 Engine이 아니라 관리 방식만 통일).
"""
from __future__ import annotations

from _common import load_yaml

from .base import Registry


class YAMLListRegistry(Registry):
    def __init__(self, registry_id: str, yaml_path: str, top_level_key: str, id_field: str):
        self.registry_id = registry_id
        self._yaml_path = yaml_path
        self._top_level_key = top_level_key
        self._id_field = id_field

    def list_entries(self) -> list[dict]:
        return load_yaml(self._yaml_path)[self._top_level_key]

    def get(self, entry_id: str) -> dict | None:
        for entry in self.list_entries():
            if entry.get(self._id_field) == entry_id:
                return entry
        return None


class CompanyRegistry(YAMLListRegistry):
    def __init__(self):
        super().__init__(
            registry_id="company",
            yaml_path="config/company_registry.yaml",
            top_level_key="companies",
            id_field="company_id",
        )


class SourceRegistry(YAMLListRegistry):
    def __init__(self):
        super().__init__(
            registry_id="source",
            yaml_path="config/sources.yaml",
            top_level_key="sources",
            id_field="source_id",
        )


class WorkflowRegistry(YAMLListRegistry):
    def __init__(self):
        super().__init__(
            registry_id="workflow",
            yaml_path="config/workflow_registry.yaml",
            top_level_key="workflows",
            id_field="workflow_id",
        )
