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
        self,
        article: dict,
        lx_context_excerpt: str,
        existing_timeline_excerpt: str,
        group_ai_instructions: str = "",
    ) -> ProviderResult:
        """schemas/claude_output.schema.json의 risk_analysis_output 형태를 반환해야 한다.

        Architect Review 뉴스 수집 실체화 라운드(2026-08-08): `group_ai_instructions`
        (선택, 기본값 빈 문자열 — 하위호환)는 이 기사가 속한 Keyword Group의
        `ai_instructions`를 Dynamic Block에 추가 컨텍스트로 전달한다.
        """

    @abstractmethod
    def quick_company_scan(
        self, company: dict, sources: list[dict], knowledge_excerpt: str = ""
    ) -> ProviderResult:
        """schemas/quick_company_scan.schema.json의 Core 필드(최소)를 반환해야 한다.

        Architect Review Round 5: Quick Company Scan을 Pilot의 첫 번째 실제 서비스로
        승격 — `scripts/quick_company_scan.py`의 Pipeline이 이 메서드를 호출한다.
        Architect Review Round 8: `knowledge_excerpt`(Knowledge Retrieval 단계 산출물)를
        선택 인자로 추가 — 기본값이 빈 문자열이라 기존 호출부는 수정 없이 그대로
        동작한다(하위 호환).
        """

    @abstractmethod
    def analyze_policy_impact(
        self, article: dict, lx_context_excerpt: str, existing_timeline_excerpt: str
    ) -> ProviderResult:
        """schemas/claude_output.schema.json의 policy_analysis_output 형태를 반환해야 한다.

        Architect Review Round 7 Scenario 4(정부 정책 영향 분석) — `analyze_risk()`와
        동일한 입력을 받되 `prompts/policy_analysis.md`(regulatory_stage 포함)를 쓴다.
        """
