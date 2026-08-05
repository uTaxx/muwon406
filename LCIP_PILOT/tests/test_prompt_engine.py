import pytest

from prompt_engine import PromptBuilder, PromptCache, PromptTemplate, PromptValidator
from prompt_engine.validator import PromptValidationError


def test_prompt_template_loads_relevance_filter():
    template = PromptTemplate("relevance_filter")
    assert template.name == "relevance_filter"
    assert "관련성 분류기" in template.static_block
    assert template.meta.prompt_version != "unknown"


def test_prompt_builder_produces_static_block_with_cache_control():
    builder = PromptBuilder(PromptTemplate("relevance_filter"))
    messages = builder.build({"article": {"title_original": "샘플"}, "topic": {}})
    assert messages[0]["cache_control"] == {"type": "ephemeral"}
    assert "관련성 분류기" in messages[0]["text"]


def test_prompt_builder_last_message_is_dynamic_payload():
    builder = PromptBuilder(PromptTemplate("relevance_filter"))
    messages = builder.build({"article": {"title_original": "샘플 제목"}, "topic": {}})
    assert "샘플 제목" in messages[-1]["text"]
    assert "cache_control" not in messages[-1]


def test_prompt_builder_includes_knowledge_block_when_provided():
    builder = PromptBuilder(PromptTemplate("risk_analysis"))
    messages = builder.build({"article": {}}, knowledge_block="LX Hausys 발췌 내용")
    knowledge_messages = [m for m in messages if "## Knowledge Block" in m["text"]]
    assert len(knowledge_messages) == 1
    assert "LX Hausys 발췌 내용" in knowledge_messages[0]["text"]
    assert knowledge_messages[0]["cache_control"] == {"type": "ephemeral"}


def test_prompt_builder_omits_knowledge_block_when_empty():
    builder = PromptBuilder(PromptTemplate("risk_analysis"))
    messages = builder.build({"article": {}})
    assert not any("## Knowledge Block" in m["text"] for m in messages)


def test_prompt_builder_includes_source_and_context_blocks():
    builder = PromptBuilder(PromptTemplate("risk_analysis"))
    messages = builder.build(
        {"article": {}},
        source_block="원문 출처: DART (Source Reliability Score: 5/5)",
        context_block="기존 타임라인 요약",
    )
    source_messages = [m for m in messages if "## Source Block" in m["text"]]
    context_messages = [m for m in messages if "## Context Block" in m["text"]]
    assert len(source_messages) == 1 and source_messages[0]["cache_control"] == {"type": "ephemeral"}
    assert len(context_messages) == 1 and "cache_control" not in context_messages[0]


def test_prompt_cache_deduplicates_static_block_across_builds():
    cache = PromptCache()
    template = PromptTemplate("relevance_filter")
    builder = PromptBuilder(template, cache=cache)
    builder.build({"article": {}, "topic": {}})
    builder.build({"article": {}, "topic": {}})
    assert cache.misses == 1
    assert cache.hits == 1


def test_prompt_cache_control_type_from_cost_policy():
    cache = PromptCache()
    assert cache.cache_control_type() == "ephemeral"


def test_prompt_validator_rejects_template_missing_static_block():
    class FakeTemplate:
        name = "fake"
        static_block = "   "
        from prompt_engine.template import PromptTemplateMeta

        meta = PromptTemplateMeta(prompt_version="0.1.0", default_model_id=None)

    with pytest.raises(PromptValidationError):
        PromptValidator().validate_template(FakeTemplate())


def test_prompt_validator_rejects_empty_messages():
    with pytest.raises(PromptValidationError):
        PromptValidator().validate_messages([])
