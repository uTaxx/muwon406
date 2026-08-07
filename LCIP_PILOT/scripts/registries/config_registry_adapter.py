"""ConfigRegistryAdapter — `config/*.yaml` 파일 자체를 목록화하는 메타 Registry.

"이 Pilot에 Config 파일이 몇 개, 무엇이 있는지"를 한 곳에서 조회하기 위한 것이며, 각
Config 파일의 내용을 재해석하거나 검증하지 않는다(검증은 `scripts/validate_config.py`가
이미 담당한다 — 중복 로직을 만들지 않는다).
"""
from __future__ import annotations

from _common import load_yaml, project_root

from .base import Registry

CONFIG_DIR = project_root() / "config"


class ConfigRegistryAdapter(Registry):
    registry_id = "config"

    def list_entries(self) -> list[dict]:
        return [self._entry_for(path.stem) for path in sorted(CONFIG_DIR.glob("*.yaml"))]

    def get(self, entry_id: str) -> dict | None:
        path = CONFIG_DIR / f"{entry_id}.yaml"
        if not path.exists():
            return None
        return self._entry_for(entry_id)

    @staticmethod
    def _entry_for(config_name: str) -> dict:
        data = load_yaml(f"config/{config_name}.yaml") or {}
        top_level_keys = list(data.keys()) if isinstance(data, dict) else []
        return {"config_id": config_name, "top_level_keys": top_level_keys}
