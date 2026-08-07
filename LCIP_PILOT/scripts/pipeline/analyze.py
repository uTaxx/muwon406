"""Analyze 단계 — Provider(AIProvider)를 호출해 심층 리스크 분석을 수행한다."""
from __future__ import annotations

from providers.base import AIProvider, ProviderResult


def analyze_risk(
    provider: AIProvider,
    article: dict,
    lx_context_excerpt: str,
    existing_timeline_excerpt: str,
) -> ProviderResult:
    return provider.analyze_risk(article, lx_context_excerpt, existing_timeline_excerpt)


def analyze_policy_impact(
    provider: AIProvider,
    article: dict,
    lx_context_excerpt: str,
    existing_timeline_excerpt: str,
) -> ProviderResult:
    """Round 7 Scenario 4(정부 정책 영향 분석) 전용 — analyze_risk와 동일한 얇은 wrapper다."""
    return provider.analyze_policy_impact(article, lx_context_excerpt, existing_timeline_excerpt)
