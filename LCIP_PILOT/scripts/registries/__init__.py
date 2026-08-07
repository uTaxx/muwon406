"""Registry Engine — Architect Review Round 7.

새 Engine이 아니라 기존 7개 Registry(Company/Source/Model/Prompt/Workflow/Config/
Storage)의 조회 방식을 통일하는 얇은 어댑터 계층이다. `RegistryManager`가 단일
진입점이다.
"""
from .base import Registry
from .config_registry_adapter import ConfigRegistryAdapter
from .manager import RegistryManager, UnknownRegistryError
from .model_registry_adapter import ModelRegistryAdapter
from .prompt_registry_adapter import PromptRegistryAdapter
from .storage_registry_adapter import StorageRegistryAdapter
from .yaml_list_registry import CompanyRegistry, SourceRegistry, WorkflowRegistry

__all__ = [
    "Registry",
    "RegistryManager",
    "UnknownRegistryError",
    "CompanyRegistry",
    "SourceRegistry",
    "WorkflowRegistry",
    "ModelRegistryAdapter",
    "PromptRegistryAdapter",
    "ConfigRegistryAdapter",
    "StorageRegistryAdapter",
]
