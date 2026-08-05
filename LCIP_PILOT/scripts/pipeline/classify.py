"""Classify 단계 — Provider(AIProvider)를 호출해 관련성/미션/도메인 카테고리를 판정한다.

Pipeline 코드는 `AIProvider` 인터페이스에만 의존한다 — MockProvider/ClaudeProvider 어느 쪽을
주입해도 이 함수는 수정하지 않는다 (TASK-009 Provider Layer 설계 원칙).
"""
from __future__ import annotations

from providers.base import AIProvider, ProviderResult


def classify_relevance(provider: AIProvider, article: dict, topic: dict) -> ProviderResult:
    return provider.classify_relevance(article, topic)
