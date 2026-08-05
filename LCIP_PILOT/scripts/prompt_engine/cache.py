"""PromptCache — 동일 프롬프트를 반복 호출할 때 Static Block 조립을 다시 하지 않는다.

Anthropic API 자체의 Prompt Caching(`cache_control: {"type": "ephemeral"}`)과는 다른
개념이다 — 그건 네트워크 호출 단(Anthropic 서버)에서 일어나는 실제 캐싱이고, 이 클래스는
"이 프로세스 안에서 같은 Template을 여러 번 build()할 때 문자열 조립을 반복하지 않는다"는
로컬 메모이제이션이다. `cache_control_type` 조회(= 어떤 문자열을 Anthropic에 보낼지)는
`config/cost_policy.yaml`을 그대로 따른다.
"""
from __future__ import annotations

from _common import load_yaml

from .template import PromptTemplate


class PromptCache:
    def __init__(self, cache_control_type: str | None = None):
        self._static_cache: dict[str, str] = {}
        self._cache_control_type = cache_control_type
        self.hits = 0
        self.misses = 0

    def cache_control_type(self) -> str:
        if self._cache_control_type:
            return self._cache_control_type
        policy = load_yaml("config/cost_policy.yaml")
        return policy.get("prompt_cache", {}).get("cache_control_type", "ephemeral")

    def get_static_block(self, template: PromptTemplate) -> str:
        key = f"{template.name}:{template.meta.prompt_version}"
        if key in self._static_cache:
            self.hits += 1
            return self._static_cache[key]
        self.misses += 1
        self._static_cache[key] = template.static_block
        return self._static_cache[key]
