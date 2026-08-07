"""ModelRegistryAdapter — `config/model_registry.yaml`의 `tiers:` 딕셔너리(리스트가 아님)를
공통 Registry Interface로 감싼다. 실제 모델 조회 로직은 여전히
`claude_client.get_model_name()`이 담당한다 — 이 어댑터는 조회 순서 로직을 대체하지 않고
"등록된 tier 목록"만 노출한다.
"""
from __future__ import annotations

from _common import load_yaml

from .base import Registry


class ModelRegistryAdapter(Registry):
    registry_id = "model"

    def list_entries(self) -> list[dict]:
        tiers = load_yaml("config/model_registry.yaml")["tiers"]
        return [{"tier": name, **config} for name, config in tiers.items()]

    def get(self, entry_id: str) -> dict | None:
        tiers = load_yaml("config/model_registry.yaml")["tiers"]
        if entry_id not in tiers:
            return None
        return {"tier": entry_id, **tiers[entry_id]}
