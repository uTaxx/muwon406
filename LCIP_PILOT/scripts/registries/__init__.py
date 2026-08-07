"""Registry Engine — Architect Review Round 7/8.

새 Engine이 아니라 기존 8개 Registry(Company/Source/Model/Prompt/Workflow/Config/
Storage/Technical Debt)의 조회 방식을 통일하는 얇은 어댑터 계층이다. `RegistryManager`가
단일 진입점이다. Technical Debt Registry(Round 8)는 새 어댑터 클래스를 만들지 않고
Company/Source/Workflow와 동일한 `YAMLListRegistry`를 재사용한다.
"""
from .base import Registry
from .config_registry_adapter import ConfigRegistryAdapter
from .manager import RegistryManager, UnknownRegistryError
from .model_registry_adapter import ModelRegistryAdapter
from .prompt_registry_adapter import PromptRegistryAdapter
from .storage_registry_adapter import StorageRegistryAdapter
from .yaml_list_registry import (
    CompanyRegistry,
    SourceRegistry,
    TechnicalDebtRegistry,
    WorkflowRegistry,
)

__all__ = [
    "Registry",
    "RegistryManager",
    "UnknownRegistryError",
    "CompanyRegistry",
    "SourceRegistry",
    "WorkflowRegistry",
    "TechnicalDebtRegistry",
    "ModelRegistryAdapter",
    "PromptRegistryAdapter",
    "ConfigRegistryAdapter",
    "StorageRegistryAdapter",
]
