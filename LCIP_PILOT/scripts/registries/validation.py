"""RegistryManager Validation/Integrity/Dependency Check — Architect Review Round 8.

Round 8 지시: "Registry는 조회만 하지 않는다. Validation, Integrity Check, Dependency
Check를 추가한다. RegistryManager는 Project Boot 시 전체 Registry를 검증한다." 새 Engine을
만들지 않는다는 원칙(Round 7/8)에 따라, 이미 있는 `RegistryManager.list_entries()` 위에
3개의 순수 함수만 추가한다 — 각 Registry의 원본 파일이나 `RegistryManager`의 조회 방식은
바꾸지 않는다.

세 검증은 서로 다른 것을 본다:
- **Validation**: Registry 자기 자신 안에서, 각 항목에 id 필드가 실제로 채워져 있는가.
- **Integrity Check**: Registry 자기 자신 안에서, id가 중복되지 않는가.
  (`scripts/validate_config.py`는 topic/source/workflow_id만 검사하고 Company/Model/
  Prompt Registry는 다루지 않는다 — 이 모듈이 그 공백을 메운다. 로직을 복사하지 않고
  RegistryManager가 이미 아는 `id_field`만 재사용한다.)
- **Dependency Check**: 서로 다른 Registry/Config 사이의 참조가 실제로 존재하는가
  (예: `topics.yaml`의 `related_lx_companies`가 가리키는 company_id가 Company Registry에
  실재하는가, `pipeline/knowledge_retrieve.COMPANY_KNOWLEDGE_FILES`의 키가 실재하는
  company_id인가). 오탈자·삭제된 항목 참조를 조기에 잡기 위한 것이다.
"""
from __future__ import annotations

from _common import load_yaml

# Registry별 id 필드 이름. YAMLListRegistry 계열은 이미 `_id_field` 속성을 갖고 있지만,
# ModelRegistryAdapter/PromptRegistryAdapter/ConfigRegistryAdapter/StorageRegistryAdapter는
# 각자 다른 키(`tier`/`prompt_id`/`config_id`/`storage_id`)를 쓰므로 여기서 명시한다.
_ID_FIELD_BY_REGISTRY: dict[str, str] = {
    "company": "company_id",
    "source": "source_id",
    "model": "tier",
    "prompt": "prompt_id",
    "workflow": "workflow_id",
    "config": "config_id",
    "storage": "storage_id",
    "technical_debt": "debt_id",
}


def validate_registry(registry_id: str, entries: list[dict]) -> list[str]:
    """각 항목이 자신의 id 필드를 실제로 채우고 있는지 검사한다(비어 있거나 없으면 오류)."""
    id_field = _ID_FIELD_BY_REGISTRY[registry_id]
    errors = []
    for index, entry in enumerate(entries):
        value = entry.get(id_field)
        if not value:
            errors.append(f"{registry_id} 항목 #{index}: '{id_field}' 필드가 비어 있음")
    return errors


def check_registry_integrity(registry_id: str, entries: list[dict]) -> list[str]:
    """같은 Registry 안에서 id가 중복되지 않는지 검사한다."""
    id_field = _ID_FIELD_BY_REGISTRY[registry_id]
    ids = [entry.get(id_field) for entry in entries if entry.get(id_field)]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if not dupes:
        return []
    return [f"{registry_id} Registry: 중복 {id_field} {dupes}"]


def check_cross_registry_dependencies(manager) -> list[str]:
    """Registry/Config 간 참조 무결성을 검사한다. `manager`는 RegistryManager 인스턴스다."""
    errors: list[str] = []
    company_ids = {c["company_id"] for c in manager.get_registry("company").list_entries()}

    topics = load_yaml("config/topics.yaml").get("topics", [])
    for topic in topics:
        for company_id in topic.get("related_lx_companies", []):
            if company_id not in company_ids:
                errors.append(
                    f"topics.yaml({topic.get('topic_id')}): related_lx_companies가 "
                    f"Company Registry에 없는 '{company_id}'를 참조함"
                )

    from pipeline.knowledge_retrieve import COMPANY_KNOWLEDGE_FILES

    for company_id in COMPANY_KNOWLEDGE_FILES:
        if company_id not in company_ids:
            errors.append(
                f"pipeline/knowledge_retrieve.py: COMPANY_KNOWLEDGE_FILES가 Company "
                f"Registry에 없는 '{company_id}'를 참조함"
            )

    return errors
