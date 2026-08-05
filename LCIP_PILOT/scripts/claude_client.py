#!/usr/bin/env python3
"""Claude API Client — 프롬프트 파일 로딩, Model Registry 조회, 메시지 조립 유틸.

Round 5 Technical Debt 정리: 실제 Provider 호출은 `scripts/providers/claude_provider.py`
(Provider Layer)와 `scripts/prompt_engine/`(Prompt Engine)가 담당한다. 이 모듈은 그 둘이
공유하는 하위 유틸(프롬프트 파일 파싱, Model Registry 조회)만 남긴다 — Round 4까지 있던
`call_claude_mocked()`(및 `ClaudeUsage`/`ClaudeCallResult`)는 `providers/mock_provider.py`
(MockProvider)로 완전히 대체되어 제거했다.
"""
from __future__ import annotations

import json
from pathlib import Path

from _common import env_or_none, load_yaml, project_root

PROMPTS_DIR = project_root() / "prompts"


def _frontmatter_field(text: str, field: str) -> str | None:
    """prompts/*.md의 YAML frontmatter에서 `field:` 값을 읽는다. 없거나 null이면 None."""
    for line in text.splitlines():
        if line.strip().startswith(f"{field}:"):
            value = line.split(":", 1)[1].strip()
            if value in ("", "null", "~"):
                return None
            return value
    return None


def load_prompt(name: str) -> tuple[str, str]:
    """prompts/<name>.md를 읽어 (본문, prompt_version)을 반환한다.

    각 prompt 파일은 frontmatter에 `prompt_version:`을 명시해야 한다.
    """
    path = PROMPTS_DIR / f"{name}.md"
    text = path.read_text(encoding="utf-8")
    version = _frontmatter_field(text, "prompt_version") or "unknown"
    return text, version


def load_model_registry() -> dict:
    """config/model_registry.yaml을 로드한다 (Architect Review Round 3 Q4)."""
    return load_yaml("config/model_registry.yaml")["tiers"]


def get_model_name(purpose: str) -> str:
    """purpose: 'classification' | 'deep_analysis' | 'future'.

    모델명 조회 순서 (Architect Review Round 3 Q4, 하드코딩 금지 원칙 유지):
      1. .env의 model_env 환경변수 (최우선 — 임시 override 등)
      2. config/model_registry.yaml의 tiers.<purpose>.model_id (팀 표준 기본값)
      3. tiers.<purpose>.used_by_prompts[0] 프롬프트 frontmatter의 default_model_id (최후 fallback)
      4. 셋 다 없으면 명시적으로 에러 — 임의로 모델을 추측하지 않는다.
    """
    registry = load_model_registry()
    if purpose not in registry:
        raise ValueError(f"model_registry.yaml에 없는 purpose: {purpose}")
    tier = registry[purpose]

    env_key = tier["model_env"]
    model = env_or_none(env_key)
    if model:
        return model

    if tier.get("model_id"):
        return tier["model_id"]

    for prompt_name in tier.get("used_by_prompts", []):
        prompt_text, _ = load_prompt(prompt_name)
        default_model = _frontmatter_field(prompt_text, "default_model_id")
        if default_model:
            return default_model

    raise RuntimeError(
        f"'{purpose}' tier의 모델을 확인할 수 없다 — {env_key}(.env), "
        f"config/model_registry.yaml의 tiers.{purpose}.model_id, "
        f"prompts/*.md의 default_model_id가 전부 비어 있다. Anthropic Console에서 모델 ID를 "
        "확정한 뒤 이 중 하나에 채워야 한다 (코드 하드코딩 금지)."
    )


def split_prompt_blocks(prompt_text: str) -> tuple[str, str]:
    """Architect Review Q3의 Static/Dynamic Block 구조를 파싱한다.

    prompts/*.md는 `## Static Block`과 `## Dynamic Block` 두 개의 h2 섹션을 갖는다
    (natural_language_admin.md처럼 h3 하위 섹션이 있어도 h2 경계만 기준으로 자른다).
    반환값: (static_block_text, dynamic_block_text)
    """
    static_marker = "## Static Block"
    dynamic_marker = "## Dynamic Block"
    if static_marker not in prompt_text or dynamic_marker not in prompt_text:
        raise ValueError(
            "prompt에 '## Static Block'/'## Dynamic Block' 섹션이 없다 — "
            "Architect Review Q3 구조를 따르지 않는 prompt 파일이다."
        )
    static_start = prompt_text.index(static_marker)
    dynamic_start = prompt_text.index(dynamic_marker)
    static_block = prompt_text[static_start:dynamic_start].strip()
    dynamic_block = prompt_text[dynamic_start:].strip()
    return static_block, dynamic_block


def build_cached_messages(prompt_name: str, dynamic_payload: dict) -> list[dict]:
    """Anthropic Messages API의 content 배열을 Static/Dynamic Block으로 분리 구성한다.

    Static Block에는 `cache_control: {"type": "ephemeral"}`을 붙여 Prompt Caching 대상으로
    표시한다 (config/cost_policy.yaml의 prompt_cache.cache_control_type과 동일 값). 실제
    Anthropic API 클라이언트 호출은 TASK-009에서 이 반환값을 그대로 `messages[0]["content"]`로
    사용하면 된다 — 이번 라운드는 메시지 구조만 만들고 실제 호출은 하지 않는다.
    """
    prompt_text, _version = load_prompt(prompt_name)
    static_block, _dynamic_template = split_prompt_blocks(prompt_text)

    policy = load_yaml("config/cost_policy.yaml")
    cache_control_type = policy.get("prompt_cache", {}).get("cache_control_type", "ephemeral")

    return [
        {
            "type": "text",
            "text": static_block,
            "cache_control": {"type": cache_control_type},
        },
        {
            "type": "text",
            "text": json.dumps(dynamic_payload, ensure_ascii=False, indent=2),
        },
    ]


def clip_context(text: str, max_chars: int) -> str:
    """전체 Knowledge Base를 매번 보내지 않기 위한 단순 clipping 유틸.

    실제 관련 문단 선택 로직(semantic search 등)은 TASK-009 본 구현에서 정교화한다.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[TRUNCATED]"


if __name__ == "__main__":
    print("이 모듈은 프롬프트 로딩/Model Registry 조회 유틸만 제공한다.")
    print("Mock 기반 로컬 테스트는 providers.mock_provider.MockProvider를 사용하라.")
    print("실제 Anthropic 호출은 providers.claude_provider.ClaudeProvider(enabled=True) 대상이다.")
