"""RegistryManager — Architect Review Round 7/8.

Company/Source/Model/Prompt/Workflow/Config/Storage/Technical Debt 8개 Registry를 동일한 Interface
(`Registry.list_entries()`/`get()`/`count()`)로 조회할 수 있게 묶는 단일 진입점이다.
각 Registry의 원본 파일/파싱 로직은 전혀 바꾸지 않았다 — 기존 호출부
(`quick_company_scan.py`가 `config/company_registry.yaml`을 직접 읽는 것 등)는 계속
그대로 동작한다. `RegistryManager`는 "Registry가 몇 개 있고 각각 몇 건인지"를 한 번에
보고 싶을 때(Quality Gate의 Registry Quality Score 등) 쓰는 조회 계층이다.

Round 8 지시: "Registry는 조회만 하지 않는다." `validate()`/`check_integrity()`/
`check_dependencies()` 세 메서드를 추가한다 — 실제 검증 로직은
`scripts/registries/validation.py`에 순수 함수로 분리되어 있고, 이 클래스는 그
함수들을 자신의 상태(각 Registry의 `list_entries()`)와 연결하는 얇은 위임만 한다
(새 Engine이 아니라 기존 조회 계층의 확장).
"""
from __future__ import annotations

from . import validation
from .base import Registry
from .config_registry_adapter import ConfigRegistryAdapter
from .model_registry_adapter import ModelRegistryAdapter
from .prompt_registry_adapter import PromptRegistryAdapter
from .storage_registry_adapter import StorageRegistryAdapter
from .yaml_list_registry import (
    CompanyRegistry,
    SourceRegistry,
    TechnicalDebtRegistry,
    WorkflowRegistry,
)


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
            "technical_debt": TechnicalDebtRegistry(),
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

    def validate(self) -> list[str]:
        """전체 Registry의 각 항목이 자신의 id 필드를 채우고 있는지 검사한다."""
        errors: list[str] = []
        for registry_id in self.registry_ids():
            errors += validation.validate_registry(registry_id, self.get_registry(registry_id).list_entries())
        return errors

    def check_integrity(self) -> list[str]:
        """전체 Registry 내부 id 중복 여부를 검사한다."""
        errors: list[str] = []
        for registry_id in self.registry_ids():
            errors += validation.check_registry_integrity(
                registry_id, self.get_registry(registry_id).list_entries()
            )
        return errors

    def check_dependencies(self) -> list[str]:
        """Registry/Config 간 참조 무결성(예: topics.yaml -> Company Registry)을 검사한다."""
        return validation.check_cross_registry_dependencies(self)

    def validate_all(self) -> list[str]:
        """Validation + Integrity Check + Dependency Check를 한 번에 수행한다.
        `bootstrap_project.py`(Project Boot)가 이 메서드를 호출한다."""
        return self.validate() + self.check_integrity() + self.check_dependencies()
