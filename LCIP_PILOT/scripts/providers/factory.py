"""Provider Factory — Round 6 TASK-009.

"API Key가 없으면 MockProvider 자동 사용. Provider 선택은 Config로 제어한다"는 지시를
코드 한 곳에 모은다. `ANTHROPIC_API_KEY` 존재 여부와 `feature_flags.claude_api_enabled`
둘 다 참일 때만 `ClaudeProvider(enabled=True)`를 반환하고, 그 외에는 항상
`MockProvider()`로 안전하게 떨어진다 — 호출부는 이 함수 하나만 알면 된다.
"""
from __future__ import annotations

from _common import env_or_none
from feature_flags import is_enabled

from .base import AIProvider
from .claude_provider import ClaudeProvider
from .mock_provider import MockProvider


def get_default_provider() -> AIProvider:
    has_api_key = bool(env_or_none("ANTHROPIC_API_KEY"))
    if has_api_key and is_enabled("claude_api_enabled"):
        return ClaudeProvider(enabled=True)
    return MockProvider()
