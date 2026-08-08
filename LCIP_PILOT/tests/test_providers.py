import json
from pathlib import Path

import jsonschema
import pytest

from providers.base import AIProvider, ProviderResult, ProviderUsage
from providers.claude_provider import ClaudeProvider, ClaudeProviderDisabledError
from providers.factory import get_default_provider
from providers.future_providers import GeminiProvider, OpenAIProvider
from providers.mock_provider import MockProvider

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = ROOT / "schemas"

SILICA_ARTICLE = {
    "title_original": "Engineered stone silicosis lawsuit filed in California",
    "source_url": "https://example.com/a",
    "published_at": "2026-07-30T09:00:00Z",
    "language": "en",
}
UNRELATED_ARTICLE = {
    "title_original": "Local weather forecast update",
    "source_url": "https://example.com/b",
    "published_at": "2026-07-30T09:00:00Z",
    "language": "en",
}
TOPIC = {"topic_id": "TOP-0001", "related_lx_companies": ["LX_HAUSYS"]}


def _relevance_schema():
    schema = json.loads((SCHEMAS_DIR / "claude_output.schema.json").read_text(encoding="utf-8"))
    return {**schema["$defs"]["relevance_output"], "$defs": schema["$defs"]}


def _risk_schema():
    schema = json.loads((SCHEMAS_DIR / "claude_output.schema.json").read_text(encoding="utf-8"))
    return {**schema["$defs"]["risk_analysis_output"], "$defs": schema["$defs"]}


def _quick_scan_schema():
    return json.loads((SCHEMAS_DIR / "quick_company_scan.schema.json").read_text(encoding="utf-8"))


def _policy_schema():
    schema = json.loads((SCHEMAS_DIR / "claude_output.schema.json").read_text(encoding="utf-8"))
    return {**schema["$defs"]["policy_analysis_output"], "$defs": schema["$defs"]}


def test_mock_provider_is_an_ai_provider():
    assert isinstance(MockProvider(), AIProvider)


def test_mock_provider_classify_relevance_matches_schema_for_related_article():
    result = MockProvider().classify_relevance(SILICA_ARTICLE, TOPIC)
    assert result.ok is True
    jsonschema.validate(instance=result.parsed_json, schema=_relevance_schema())
    assert result.parsed_json["relevant"] is True
    assert result.parsed_json["needs_deep_analysis"] is True


def test_mock_provider_classify_relevance_matches_schema_for_unrelated_article():
    result = MockProvider().classify_relevance(UNRELATED_ARTICLE, TOPIC)
    jsonschema.validate(instance=result.parsed_json, schema=_relevance_schema())
    assert result.parsed_json["relevant"] is False


def test_mock_provider_analyze_risk_matches_schema():
    result = MockProvider().analyze_risk(SILICA_ARTICLE, "LX Hausys 발췌", "기존 타임라인")
    assert result.ok is True
    jsonschema.validate(instance=result.parsed_json, schema=_risk_schema())
    assert isinstance(result.usage, ProviderUsage)


def test_mock_provider_analyze_policy_impact_matches_schema():
    result = MockProvider().analyze_policy_impact(SILICA_ARTICLE, "LX Hausys 발췌", "기존 타임라인")
    assert result.ok is True
    jsonschema.validate(instance=result.parsed_json, schema=_policy_schema())
    assert result.parsed_json["regulatory_stage"] in (
        "proposed", "public_comment", "passed", "in_effect", "enforcement", "unknown",
    )


def test_mock_provider_call_count_increments():
    provider = MockProvider()
    provider.classify_relevance(SILICA_ARTICLE, TOPIC)
    provider.analyze_risk(SILICA_ARTICLE, "", "")
    assert provider.call_count == 2


def test_mock_provider_quick_company_scan_matches_core_schema():
    result = MockProvider().quick_company_scan(
        {"display_name": "LX Hausys"},
        [{"source_name": "Google News RSS (Korean)", "endpoint_url": "https://example.com/rss"}],
    )
    assert result.ok is True
    jsonschema.validate(instance=result.parsed_json, schema=_quick_scan_schema())
    assert result.parsed_json["target_company"] == "LX Hausys"


def test_mock_provider_quick_company_scan_uses_real_knowledge_when_company_id_registered():
    """Round 9 지시("실제 사용 가능한 Pilot"): LX_HAUSYS는 Round 6에서 실제 Knowledge를
    갖췄으므로, company_id가 주어지면 더 이상 "mock: ... 미확인" placeholder가 아니라
    LX_HAUSYS_COMPANY_DNA.md의 실제 내용을 반환해야 한다."""
    result = MockProvider().quick_company_scan(
        {"display_name": "LX Hausys", "query": "LX Hausys", "company_id": "LX_HAUSYS"}, []
    )
    assert "mock" not in result.parsed_json["company_overview"].lower()
    assert "108670" in result.parsed_json["company_overview"]  # KRX 티커, 실제 Knowledge 근거
    assert "mock: 사업부 구성 정보 미확인" not in result.parsed_json["business_structure"]
    assert "mock: 경쟁사 정보 미확인" not in result.parsed_json["competitor"]
    jsonschema.validate(instance=result.parsed_json, schema=_quick_scan_schema())


def test_mock_provider_quick_company_scan_stays_mock_for_unregistered_company():
    """company_id가 없거나(미등록 회사) Knowledge 파일이 없으면 예전처럼 정직하게
    mock placeholder를 유지한다 — 임의로 지어내지 않는다."""
    result = MockProvider().quick_company_scan(
        {"display_name": "존재하지않는가상회사", "query": "존재하지않는가상회사", "company_id": None}, []
    )
    assert result.parsed_json["company_overview"].startswith("존재하지않는가상회사")
    assert result.parsed_json["business_structure"] == ["mock: 사업부 구성 정보 미확인"]


def test_mock_provider_quick_company_scan_does_not_leak_other_files_section_numbers():
    """Round 9 버그 수정 회귀 감시: `search_by_company()`가 이어붙이는 7개 파일 중
    LX_HOLDINGS_CONTEXT.md도 §7(Competitor)을 갖고 있어, 파일 우선순위 없이 Section
    번호로만 찾으면 LX Hausys 고유의 §7 대신 지주회사(LX_HOLDINGS_CONTEXT)의 "직접
    경쟁하는 대상이 없다"는 문장이 잘못 노출될 수 있었다."""
    result = MockProvider().quick_company_scan(
        {"display_name": "LX Hausys", "query": "LX Hausys", "company_id": "LX_HAUSYS"}, []
    )
    assert "지주회사는 사업적으로 직접 경쟁하는 대상이 없다" not in result.parsed_json["competitor"][0]


def test_claude_provider_quick_company_scan_enabled_with_model_raises_not_implemented(monkeypatch):
    monkeypatch.setenv("LCIP_FUTURE_READINESS_MODEL", "test-model-id")
    provider = ClaudeProvider(enabled=True)
    with pytest.raises(NotImplementedError):
        provider.quick_company_scan({"display_name": "LX Hausys"}, [])


def test_claude_provider_is_an_ai_provider():
    assert isinstance(ClaudeProvider(), AIProvider)


def test_claude_provider_disabled_by_default():
    provider = ClaudeProvider()
    assert provider.enabled is False
    with pytest.raises(ClaudeProviderDisabledError):
        provider.classify_relevance(SILICA_ARTICLE, TOPIC)
    with pytest.raises(ClaudeProviderDisabledError):
        provider.analyze_risk(SILICA_ARTICLE, "", "")
    with pytest.raises(ClaudeProviderDisabledError):
        provider.analyze_policy_impact(SILICA_ARTICLE, "", "")


def test_claude_provider_enabled_but_no_model_configured_raises_before_network(monkeypatch):
    # enabled=True로 켜도, 실제 네트워크 호출까지 가지 않고 model_registry 미설정에서 멈춰야 한다.
    monkeypatch.delenv("LCIP_CLASSIFICATION_MODEL", raising=False)
    provider = ClaudeProvider(enabled=True)
    with pytest.raises(RuntimeError):
        provider.classify_relevance(SILICA_ARTICLE, TOPIC)


def test_claude_provider_enabled_with_model_raises_not_implemented(monkeypatch):
    # 모델은 설정됐지만 실제 API 호출부는 TASK-009 본구현 대상 — NotImplementedError로 명확히 멈춘다.
    monkeypatch.setenv("LCIP_CLASSIFICATION_MODEL", "test-model-id")
    provider = ClaudeProvider(enabled=True)
    with pytest.raises(NotImplementedError):
        provider.classify_relevance(SILICA_ARTICLE, TOPIC)


def test_claude_provider_analyze_risk_enabled_with_model_raises_not_implemented(monkeypatch):
    monkeypatch.setenv("LCIP_DEEP_ANALYSIS_MODEL", "test-model-id")
    provider = ClaudeProvider(enabled=True)
    with pytest.raises(NotImplementedError):
        provider.analyze_risk(SILICA_ARTICLE, "LX Hausys 발췌", "기존 타임라인")


def test_claude_provider_analyze_policy_impact_enabled_with_model_raises_not_implemented(monkeypatch):
    monkeypatch.setenv("LCIP_DEEP_ANALYSIS_MODEL", "test-model-id")
    provider = ClaudeProvider(enabled=True)
    with pytest.raises(NotImplementedError):
        provider.analyze_policy_impact(SILICA_ARTICLE, "LX Hausys 발췌", "기존 타임라인")


def test_claude_provider_build_source_block_includes_reliability_score():
    block = ClaudeProvider._build_source_block({"source_name": "DART 공시 (전자공시시스템)"})
    assert "DART 공시 (전자공시시스템)" in block
    assert "Source Reliability Score: 5/5" in block


def test_claude_provider_build_source_block_empty_when_no_source_name():
    assert ClaudeProvider._build_source_block({}) == ""


def test_claude_provider_validate_output_accepts_valid_relevance_output():
    example = {
        "relevant": True,
        "relevance_score": 0.9,
        "mission_category": ["risk_management"],
        "intelligence_categories": ["litigation"],
        "related_companies": [],
        "reason": "샘플",
        "needs_deep_analysis": True,
    }
    ClaudeProvider.validate_output(example, "relevance_output")


def test_claude_provider_validate_output_rejects_invalid_relevance_output():
    with pytest.raises(jsonschema.ValidationError):
        ClaudeProvider.validate_output({"relevant": "not-a-bool"}, "relevance_output")


@pytest.mark.parametrize("provider_cls", [OpenAIProvider, GeminiProvider])
def test_future_providers_are_ai_providers_but_not_implemented(provider_cls):
    provider = provider_cls()
    assert isinstance(provider, AIProvider)
    with pytest.raises(NotImplementedError):
        provider.classify_relevance(SILICA_ARTICLE, TOPIC)
    with pytest.raises(NotImplementedError):
        provider.analyze_risk(SILICA_ARTICLE, "", "")
    with pytest.raises(NotImplementedError):
        provider.quick_company_scan({"display_name": "샘플"}, [])
    with pytest.raises(NotImplementedError):
        provider.analyze_policy_impact(SILICA_ARTICLE, "", "")


def test_providers_are_interchangeable_same_call_signature():
    """Provider 교체 가능성 검증: 동일한 시그니처로 MockProvider/ClaudeProvider를 바꿔 끼울 수 있다."""
    providers: list[AIProvider] = [MockProvider()]
    for provider in providers:
        result = provider.classify_relevance(SILICA_ARTICLE, TOPIC)
        assert isinstance(result, ProviderResult)


# --- Round 6 TASK-009: 실제 _call_anthropic 호출부 (feature_flags.claude_api_enabled로 이중 게이트) ---


class _FakeTextBlock:
    type = "text"

    def __init__(self, text: str):
        self.text = text


class _FakeUsage:
    def __init__(self, input_tokens: int, output_tokens: int):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class _FakeAnthropicResponse:
    def __init__(self, text: str, input_tokens: int = 100, output_tokens: int = 50):
        self.content = [_FakeTextBlock(text)]
        self.usage = _FakeUsage(input_tokens, output_tokens)


class _FakeMessages:
    def __init__(self, response):
        self._response = response
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self._response


class _FakeAnthropicClient:
    def __init__(self, response):
        self.messages = _FakeMessages(response)


_RELEVANCE_PAYLOAD = {
    "relevant": True,
    "relevance_score": 0.9,
    "mission_category": ["risk_management"],
    "mission_subcategory": ["litigation"],
    "intelligence_categories": ["litigation"],
    "related_companies": ["LX_HAUSYS"],
    "reason": "실제 호출 경로 테스트 (fake client)",
    "needs_deep_analysis": True,
}


def test_claude_provider_real_call_still_not_implemented_when_flag_off_even_if_enabled(monkeypatch):
    """feature_flags.claude_api_enabled가 false인 한(config 기본값), self.enabled=True로
    켜도 anthropic SDK를 import조차 하지 않고 NotImplementedError로 멈춰야 한다."""
    monkeypatch.setenv("LCIP_CLASSIFICATION_MODEL", "test-model-id")
    provider = ClaudeProvider(enabled=True)
    with pytest.raises(NotImplementedError):
        provider.classify_relevance(SILICA_ARTICLE, TOPIC)


def test_claude_provider_real_call_executes_when_both_gates_true(monkeypatch):
    import anthropic
    import providers.claude_provider as claude_provider_module

    monkeypatch.setattr(claude_provider_module, "is_enabled", lambda flag_name: True)
    monkeypatch.setenv("LCIP_CLASSIFICATION_MODEL", "test-model-id")

    fake_client = _FakeAnthropicClient(
        _FakeAnthropicResponse(json.dumps(_RELEVANCE_PAYLOAD, ensure_ascii=False))
    )
    monkeypatch.setattr(anthropic, "Anthropic", lambda: fake_client)

    provider = ClaudeProvider(enabled=True)
    result = provider.classify_relevance(SILICA_ARTICLE, TOPIC)

    assert result.ok is True
    assert result.parsed_json["relevant"] is True
    assert result.usage.model == "test-model-id"
    assert result.usage.input_tokens == 100
    assert fake_client.messages.calls[0]["model"] == "test-model-id"
    assert fake_client.messages.calls[0]["messages"][0]["role"] == "user"


def test_claude_provider_real_call_strips_markdown_json_fence(monkeypatch):
    """Round 13 이어서(2026-08-08) 최초 실제 연결 검증에서 발견한 실측 버그: 프롬프트가
    "JSON만" 출력하라고 지시해도 Haiku 4.5가 실제로 ```json ... ``` 코드펜스로 감싸
    응답하는 경우가 있었다 — 감싸여 있어도 파싱에 성공해야 한다."""
    import anthropic
    import providers.claude_provider as claude_provider_module

    monkeypatch.setattr(claude_provider_module, "is_enabled", lambda flag_name: True)
    monkeypatch.setenv("LCIP_CLASSIFICATION_MODEL", "test-model-id")

    fenced_text = "```json\n" + json.dumps(_RELEVANCE_PAYLOAD, ensure_ascii=False) + "\n```"
    fake_client = _FakeAnthropicClient(_FakeAnthropicResponse(fenced_text))
    monkeypatch.setattr(anthropic, "Anthropic", lambda: fake_client)

    provider = ClaudeProvider(enabled=True)
    result = provider.classify_relevance(SILICA_ARTICLE, TOPIC)

    assert result.ok is True
    assert result.parsed_json["relevant"] is True


def test_claude_provider_real_call_returns_not_ok_on_invalid_json(monkeypatch):
    import anthropic
    import providers.claude_provider as claude_provider_module

    monkeypatch.setattr(claude_provider_module, "is_enabled", lambda flag_name: True)
    monkeypatch.setenv("LCIP_CLASSIFICATION_MODEL", "test-model-id")

    fake_client = _FakeAnthropicClient(_FakeAnthropicResponse("이건 JSON이 아니다"))
    monkeypatch.setattr(anthropic, "Anthropic", lambda: fake_client)

    provider = ClaudeProvider(enabled=True)
    result = provider.classify_relevance(SILICA_ARTICLE, TOPIC)

    assert result.ok is False
    assert result.error is not None


def test_claude_provider_real_call_returns_not_ok_on_api_error(monkeypatch):
    import anthropic
    import providers.claude_provider as claude_provider_module

    monkeypatch.setattr(claude_provider_module, "is_enabled", lambda flag_name: True)
    monkeypatch.setenv("LCIP_CLASSIFICATION_MODEL", "test-model-id")

    class _RaisingMessages:
        def create(self, **kwargs):
            request = anthropic._base_client.httpx.Request("POST", "https://api.anthropic.com/v1/messages")
            response = anthropic._base_client.httpx.Response(429, request=request)
            raise anthropic.RateLimitError("rate limited", response=response, body=None)

    class _RaisingClient:
        def __init__(self):
            self.messages = _RaisingMessages()

    monkeypatch.setattr(anthropic, "Anthropic", lambda: _RaisingClient())

    provider = ClaudeProvider(enabled=True)
    result = provider.classify_relevance(SILICA_ARTICLE, TOPIC)

    assert result.ok is False
    assert "rate limited" in result.error.lower()


# --- Round 6 TASK-009: Provider Factory ---


def test_get_default_provider_returns_mock_when_no_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert isinstance(get_default_provider(), MockProvider)


def test_get_default_provider_returns_mock_when_flag_off_even_with_api_key(monkeypatch):
    """다음 Architect 승인 전까지 config/feature_flags.yaml의 claude_api_enabled는 false —
    ANTHROPIC_API_KEY가 있어도 factory는 여전히 MockProvider를 반환해야 한다."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-fake-key")
    assert isinstance(get_default_provider(), MockProvider)


def test_get_default_provider_returns_claude_provider_when_key_and_flag_both_true(monkeypatch):
    import providers.factory as factory_module

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-fake-key")
    monkeypatch.setattr(factory_module, "is_enabled", lambda flag_name: True)

    provider = get_default_provider()
    assert isinstance(provider, ClaudeProvider)
    assert provider.enabled is True


def test_get_default_provider_returns_mock_when_flag_true_but_no_key(monkeypatch):
    import providers.factory as factory_module

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(factory_module, "is_enabled", lambda flag_name: True)

    assert isinstance(get_default_provider(), MockProvider)
