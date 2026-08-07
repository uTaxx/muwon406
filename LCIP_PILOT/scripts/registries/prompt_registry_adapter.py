"""PromptRegistryAdapter — `prompts/*.md` 파일들을 공통 Registry Interface로 감싼다.
별도 YAML 없이 파일 자체가 원본이므로, `claude_client`가 이미 하는 frontmatter 파싱을
재사용한다(새 파서를 만들지 않는다).
"""
from __future__ import annotations

import claude_client
from _common import project_root

from .base import Registry

PROMPTS_DIR = project_root() / "prompts"


class PromptRegistryAdapter(Registry):
    registry_id = "prompt"

    def list_entries(self) -> list[dict]:
        entries = []
        for path in sorted(PROMPTS_DIR.glob("*.md")):
            entries.append(self._entry_for(path.stem))
        return entries

    def get(self, entry_id: str) -> dict | None:
        path = PROMPTS_DIR / f"{entry_id}.md"
        if not path.exists():
            return None
        return self._entry_for(entry_id)

    @staticmethod
    def _entry_for(prompt_name: str) -> dict:
        text, version = claude_client.load_prompt(prompt_name)
        default_model_id = claude_client._frontmatter_field(text, "default_model_id")
        return {
            "prompt_id": prompt_name,
            "prompt_version": version,
            "default_model_id": default_model_id,
        }
