import json
from pathlib import Path

import jsonschema
import pytest

from providers.base import AIProvider, ProviderResult, ProviderUsage
from providers.claude_provider import ClaudeProvider, ClaudeProviderDisabledError
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


def test_mock_provider_call_count_increments():
    provider = MockProvider()
    provider.classify_relevance(SILICA_ARTICLE, TOPIC)
    provider.analyze_risk(SILICA_ARTICLE, "", "")
    assert provider.call_count == 2


def test_claude_provider_is_an_ai_provider():
    assert isinstance(ClaudeProvider(), AIProvider)


def test_claude_provider_disabled_by_default():
    provider = ClaudeProvider()
    assert provider.enabled is False
    with pytest.raises(ClaudeProviderDisabledError):
        provider.classify_relevance(SILICA_ARTICLE, TOPIC)
    with pytest.raises(ClaudeProviderDisabledError):
        provider.analyze_risk(SILICA_ARTICLE, "", "")


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


def test_providers_are_interchangeable_same_call_signature():
    """Provider 교체 가능성 검증: 동일한 시그니처로 MockProvider/ClaudeProvider를 바꿔 끼울 수 있다."""
    providers: list[AIProvider] = [MockProvider()]
    for provider in providers:
        result = provider.classify_relevance(SILICA_ARTICLE, TOPIC)
        assert isinstance(result, ProviderResult)
