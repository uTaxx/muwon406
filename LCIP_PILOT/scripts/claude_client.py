#!/usr/bin/env python3
"""TASK-009 stub — Claude API Client.

이번 라운드(TASK-001~007)에서는 실제 API 호출을 구현하지 않는다. 모델명을 Config에서 읽고,
프롬프트를 로드하고, (모킹된) 응답을 JSON Schema로 검증하는 뼈대만 제공한다. 실제 Anthropic
API 연동은 TASK-009 승인 후 별도 라운드에서 완성한다.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from _common import env_or_none, load_yaml, project_root

PROMPTS_DIR = project_root() / "prompts"


@dataclass(frozen=True)
class ClaudeUsage:
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class ClaudeCallResult:
    ok: bool
    parsed_json: dict | None
    raw_text: str
    usage: ClaudeUsage | None
    prompt_version: str
    error: str | None = None


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


def call_claude_mocked(prompt_name: str, input_payload: dict) -> ClaudeCallResult:
    """실제 API를 호출하지 않는 로컬 테스트용 mock.

    TASK-011/017의 "Mock Claude 출력 검증" 단계에서 사용한다. 실제 anthropic 클라이언트 연동은
    TASK-009 승인 후 이 함수를 대체한다.
    """
    _, version = load_prompt(prompt_name)
    mock_response = {
        "relevant": True,
        "relevance_score": 0.5,
        "mission_category": ["risk_management"],
        "mission_subcategory": [],
        "intelligence_categories": ["litigation"],
        "related_companies": [],
        "reason": "mock response — 실제 API 미연동 상태",
        "needs_deep_analysis": False,
    }
    return ClaudeCallResult(
        ok=True,
        parsed_json=mock_response,
        raw_text=json.dumps(mock_response, ensure_ascii=False),
        usage=ClaudeUsage(input_tokens=0, output_tokens=0),
        prompt_version=version,
    )


if __name__ == "__main__":
    print("이 모듈은 TASK-009 전까지 실제 Anthropic API를 호출하지 않는다.")
    print("call_claude_mocked()로 로컬 파이프라인 테스트만 가능하다.")
