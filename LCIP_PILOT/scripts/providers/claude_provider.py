"""ClaudeProvider — 실제 Anthropic API를 호출하는 Provider.

Round 6 지시(TASK-009 변경): "Claude Provider도 실제 Provider 코드를 구현한다." —
`_call_anthropic()`은 이제 `anthropic` SDK로 실제 Messages API를 호출하는 코드를 담고
있다. 다만 이 코드는 이중으로 게이트된다 — (1) `self.enabled`(생성자 인자, 기존과 동일)
(2) `feature_flags.is_enabled("claude_api_enabled")`(`config/feature_flags.yaml`, 다음
Architect 승인 전까지 `false`). 두 조건이 모두 참이어야만 실제 네트워크 호출까지 도달한다
— 지금은 (2)가 `false`이므로 `enabled=True`로 켜도 여전히 `NotImplementedError`로 멈춘다
(TASK-009 본 실행은 다음 승인 이후).

Round 5부터 메시지 조립은 `claude_client.build_cached_messages()` 대신
`prompt_engine.PromptBuilder`를 거친다 — Static/Knowledge/Source/Dynamic/Context 5개
블록으로 분리하고, `lx_context_excerpt`는 Dynamic Block이 아니라 Knowledge Block으로,
기사 출처의 Source Reliability Score(`scripts/source_priority.py`)는 Source Block으로
들어간다.
"""
from __future__ import annotations

import json

import claude_client
from _common import load_yaml, project_root
from feature_flags import is_enabled
from jsonschema import ValidationError
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
        if not is_enabled("claude_api_enabled"):
            # feature_flags.claude_api_enabled=False인 동안은 self.enabled=True로 켜도
            # 여기서 멈춘다 — anthropic SDK import조차 하지 않는다(설치 여부와 무관하게
            # 항상 이 경로가 재현 가능해야 tests/test_providers.py의 기존 검증이 그대로
            # 성립한다). 다음 Architect 승인 후 config/feature_flags.yaml만 바꾸면
            # 아래 실제 호출 코드가 즉시 활성화된다.
            raise NotImplementedError(
                "ClaudeProvider._call_anthropic 실제 호출은 feature_flags.claude_api_enabled="
                "True(다음 Architect 승인 후)에서만 실행된다. 지금은 config/feature_flags.yaml"
                "에서 false로 고정되어 있다."
            )

        import anthropic

        cost_policy = load_yaml("config/cost_policy.yaml")["cost"]
        max_tokens = cost_policy["max_output_tokens_per_call"]

        client = anthropic.Anthropic()
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": messages}],
            )
        except (
            anthropic.AuthenticationError,
            anthropic.PermissionDeniedError,
            anthropic.NotFoundError,
            anthropic.BadRequestError,
            anthropic.RateLimitError,
            anthropic.APIStatusError,
            anthropic.APIConnectionError,
        ) as exc:
            return ProviderResult(
                ok=False, parsed_json=None, raw_text="", usage=None, error=str(exc)
            )

        raw_text = "".join(block.text for block in response.content if block.type == "text")
        usage = ProviderUsage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            model=model,
        )
        try:
            parsed_json = json.loads(raw_text)
            self.validate_output(parsed_json, schema_def)
        except (json.JSONDecodeError, ValidationError) as exc:
            return ProviderResult(
                ok=False, parsed_json=None, raw_text=raw_text, usage=usage, error=str(exc)
            )

        return ProviderResult(ok=True, parsed_json=parsed_json, raw_text=raw_text, usage=usage)

    @staticmethod
    def validate_output(parsed_json: dict, schema_def: str) -> None:
        """claude_output.schema.json의 $defs/<schema_def>로 검증한다 (재사용 유틸)."""
        schema = json.loads((SCHEMAS_DIR / "claude_output.schema.json").read_text(encoding="utf-8"))
        sub_schema = {**schema["$defs"][schema_def], "$defs": schema["$defs"]}
        jsonschema_validate(instance=parsed_json, schema=sub_schema)
