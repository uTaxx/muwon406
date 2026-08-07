"""RegistryManager — Architect Review Round 7.

Company/Source/Model/Prompt/Workflow/Config/Storage 7개 Registry를 동일한 Interface
(`Registry.list_entries()`/`get()`/`count()`)로 조회할 수 있게 묶는 단일 진입점이다.
각 Registry의 원본 파일/파싱 로직은 전혀 바꾸지 않았다 — 기존 호출부
(`quick_company_scan.py`가 `config/company_registry.yaml`을 직접 읽는 것 등)는 계속
그대로 동작한다. `RegistryManager`는 "Registry가 몇 개 있고 각각 몇 건인지"를 한 번에
보고 싶을 때(Quality Gate의 Registry Quality Score 등) 쓰는 조회 계층이다.
"""
from __future__ import annotations

from .base import Registry
from .config_registry_adapter import ConfigRegistryAdapter
from .model_registry_adapter import ModelRegistryAdapter
from .prompt_registry_adapter import PromptRegistryAdapter
from .storage_registry_adapter import StorageRegistryAdapter
from .yaml_list_registry import CompanyRegistry, SourceRegistry, WorkflowRegistry


class UnknownRegistryError(KeyError):
    """RegistryManager에 등록되지 않은 registry_id를 조회하면 발생."""


class RegistryManager:
    def __init__(self):
        self._registries: dict[str, Registry] = {
            "company": CompanyRegistry(),
            "source": SourceRegistry(),
            "model": ModelRegistryAdapter(),
            "prompt": PromptRegistryAdapter(),
            "workflow": WorkflowRegistry(),
            "config": ConfigRegistryAdapter(),
            "storage": StorageRegistryAdapter(),
        }

    def registry_ids(self) -> list[str]:
        return list(self._registries.keys())

    def get_registry(self, registry_id: str) -> Registry:
        if registry_id not in self._registries:
            raise UnknownRegistryError(
                f"알 수 없는 registry_id: '{registry_id}' — 사용 가능: {self.registry_ids()}"
            )
        return self._registries[registry_id]

    def summary(self) -> dict[str, int]:
        """각 Registry의 등록 건수. Quality Gate/보고서에서 그대로 재사용한다."""
        return {name: registry.count() for name, registry in self._registries.items()}
