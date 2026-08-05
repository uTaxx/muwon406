"""ClaudeProvider — 실제 Anthropic API를 호출하는 Provider (구조만, 이번 라운드는 미연동).

Round 4 지시: "외부 API 실제 호출은 아직 시작하지 않는다." 이 클래스는 모델 조회
(config/model_registry.yaml)와 Prompt 조립(Round 5부터 scripts/prompt_engine/)까지는
실제로 동작하지만, 실제 네트워크 호출 직전 단계에서 명시적으로 막아둔다 — 사용자가
Anthropic API Key를 준비하고 `enabled=True`로 명시적으로 켤 때만(TASK-009 본구현)
`_call_anthropic()`을 완성한다.

Round 5부터 메시지 조립은 `claude_client.build_cached_messages()` 대신
`prompt_engine.PromptBuilder`를 거친다 — Static/Knowledge/Source/Dynamic/Context 5개
블록으로 분리하고, `lx_context_excerpt`는 Dynamic Block이 아니라 Knowledge Block으로,
기사 출처의 Source Reliability Score(`scripts/source_priority.py`)는 Source Block으로
들어간다.
"""
from __future__ import annotations

import json

import claude_client
from _common import project_root
from jsonschema import validate as jsonschema_validate
from prompt_engine import PromptBuilder, PromptCache, PromptTemplate
from source_priority import score_for_source_type

from .base import AIProvider, ProviderResult, ProviderUsage

SCHEMAS_DIR = project_root() / "schemas"


class ClaudeProviderDisabledError(RuntimeError):
    """ClaudeProvider가 enabled=False(기본값)인 상태에서 호출되면 발생."""


class ClaudeProvider(AIProvider):
    """실제 Anthropic API 연동 지점. 기본은 항상 비활성(enabled=False)."""

    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        # 같은 프로세스 안에서 여러 번 호출될 때 Static Block을 반복 조립하지 않도록
        # PromptCache를 Provider 인스턴스 단위로 공유한다.
        self._prompt_cache = PromptCache()

    def classify_relevance(self, article: dict, topic: dict) -> ProviderResult:
        self._require_enabled()
        model = claude_client.get_model_name("classification")  # 미설정 시 여기서 명시적 에러
        builder = PromptBuilder(PromptTemplate("relevance_filter"), cache=self._prompt_cache)
        messages = builder.build({"article": article, "topic": topic})
        return self._call_anthropic(model, messages, "relevance_output")

    def analyze_risk(
        self, article: dict, lx_context_excerpt: str, existing_timeline_excerpt: str
    ) -> ProviderResult:
        self._require_enabled()
        model = claude_client.get_model_name("deep_analysis")
        builder = PromptBuilder(PromptTemplate("risk_analysis"), cache=self._prompt_cache)
        source_block = self._build_source_block(article)
        messages = builder.build(
            {"article": article},
            knowledge_block=lx_context_excerpt,
            source_block=source_block,
            context_block=existing_timeline_excerpt,
        )
        return self._call_anthropic(model, messages, "risk_analysis_output")

    def quick_company_scan(self, company: dict, sources: list[dict]) -> ProviderResult:
        self._require_enabled()
        model = claude_client.get_model_name("future")
        builder = PromptBuilder(PromptTemplate("quick_scan"), cache=self._prompt_cache)
        source_names = ", ".join(s.get("source_name", "") for s in sources) or "(등록된 Source 없음)"
        messages = builder.build(
            {"target_company": company.get("display_name") or company.get("query")},
            source_block=f"자동 선택된 Source: {source_names}",
        )
        return self._call_anthropic(model, messages, "quick_company_scan_output")

    @staticmethod
    def _build_source_block(article: dict) -> str:
        source_name = article.get("source_name") or article.get("source_type") or ""
        if not source_name:
            return ""
        score = score_for_source_type(source_name)
        return f"원문 출처: {source_name} (Source Reliability Score: {score}/5)"

    def _require_enabled(self) -> None:
        if not self.enabled:
            raise ClaudeProviderDisabledError(
                "ClaudeProvider.enabled=False — 실제 Anthropic API 호출은 TASK-009 본구현 "
                "승인 및 ANTHROPIC_API_KEY 준비 후에만 활성화한다. 지금은 MockProvider를 "
                "사용하라."
            )

    def _call_anthropic(self, model: str, messages: list[dict], schema_def: str) -> ProviderResult:
        # anthropic SDK import는 실제 네트워크 호출 로직을 채울 때(TASK-009 본구현, 사용자
        # 승인 후)만 수행한다 — 지금 단계에서 SDK 설치 여부에 이 메서드의 동작이 좌우되지
        # 않도록, import 자체를 실제 호출 구현과 함께 미룬다.
        raise NotImplementedError(
            "ClaudeProvider._call_anthropic 실제 호출부는 TASK-009 본구현 대상이다. "
            "(anthropic SDK 연동은 사용자 승인 및 ANTHROPIC_API_KEY 준비 후 완성)"
        )

    @staticmethod
    def validate_output(parsed_json: dict, schema_def: str) -> None:
        """claude_output.schema.json의 $defs/<schema_def>로 검증한다 (재사용 유틸)."""
        schema = json.loads((SCHEMAS_DIR / "claude_output.schema.json").read_text(encoding="utf-8"))
        sub_schema = {**schema["$defs"][schema_def], "$defs": schema["$defs"]}
        jsonschema_validate(instance=parsed_json, schema=sub_schema)
