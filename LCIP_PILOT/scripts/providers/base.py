"""AIProvider — 모델/공급자에 무관한 분석 인터페이스."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderUsage:
    input_tokens: int
    output_tokens: int
    model: str


@dataclass(frozen=True)
class ProviderResult:
    ok: bool
    parsed_json: dict | None
    raw_text: str
    usage: ProviderUsage | None
    error: str | None = None


class AIProvider(ABC):
    """모든 AI 공급자(Claude/OpenAI/Gemini 등)가 구현해야 하는 계약.

    scripts/pipeline/*의 Business Logic은 이 인터페이스에만 의존한다 — 어떤 Provider를
    주입하느냐에 따라 실제 호출 대상이 바뀔 뿐, Pipeline 코드는 전혀 수정하지 않는다.
    """

    @abstractmethod
    def classify_relevance(self, article: dict, topic: dict) -> ProviderResult:
        """schemas/claude_output.schema.json의 relevance_output 형태를 반환해야 한다."""

    @abstractmethod
    def analyze_risk(
        self, article: dict, lx_context_excerpt: str, existing_timeline_excerpt: str
    ) -> ProviderResult:
        """schemas/claude_output.schema.json의 risk_analysis_output 형태를 반환해야 한다."""
