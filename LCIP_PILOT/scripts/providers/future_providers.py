"""Future Providers — 아직 구현하지 않는다. Provider 확장 지점을 증명하기 위한 placeholder.

Architect Review Round 4 지시: "모델 변경 시 Business Logic 수정 없이 Provider만 교체
가능해야 한다." 아래 두 클래스는 AIProvider를 구현하지만 실제 로직은 없다 — 나중에 실제
OpenAI/Gemini SDK 연동이 필요해지면 scripts/pipeline/*을 전혀 건드리지 않고 이 파일만
채우면 된다는 것을 보여준다.
"""
from __future__ import annotations

from .base import AIProvider, ProviderResult


class OpenAIProvider(AIProvider):
    """미래 확장용. 아직 구현하지 않는다 (Architect Review Round 4)."""

    def classify_relevance(self, article: dict, topic: dict) -> ProviderResult:
        raise NotImplementedError("OpenAIProvider는 아직 구현되지 않았다 (Future).")

    def analyze_risk(
        self, article: dict, lx_context_excerpt: str, existing_timeline_excerpt: str
    ) -> ProviderResult:
        raise NotImplementedError("OpenAIProvider는 아직 구현되지 않았다 (Future).")

    def quick_company_scan(self, company: dict, sources: list[dict]) -> ProviderResult:
        raise NotImplementedError("OpenAIProvider는 아직 구현되지 않았다 (Future).")


class GeminiProvider(AIProvider):
    """미래 확장용. 아직 구현하지 않는다 (Architect Review Round 4)."""

    def classify_relevance(self, article: dict, topic: dict) -> ProviderResult:
        raise NotImplementedError("GeminiProvider는 아직 구현되지 않았다 (Future).")

    def analyze_risk(
        self, article: dict, lx_context_excerpt: str, existing_timeline_excerpt: str
    ) -> ProviderResult:
        raise NotImplementedError("GeminiProvider는 아직 구현되지 않았다 (Future).")

    def quick_company_scan(self, company: dict, sources: list[dict]) -> ProviderResult:
        raise NotImplementedError("GeminiProvider는 아직 구현되지 않았다 (Future).")
