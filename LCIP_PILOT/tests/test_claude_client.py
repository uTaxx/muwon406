import pytest

import claude_client

PROMPTS_WITH_CACHE_BLOCKS = [
    "relevance_filter",
    "risk_analysis",
    "daily_change",
    "policy_analysis",
    "quick_scan",
    "natural_language_admin",
]


@pytest.mark.parametrize("prompt_name", PROMPTS_WITH_CACHE_BLOCKS)
def test_all_prompts_have_static_and_dynamic_blocks(prompt_name):
    text, _version = claude_client.load_prompt(prompt_name)
    static_block, dynamic_block = claude_client.split_prompt_blocks(text)
    assert static_block.startswith("## Static Block")
    assert dynamic_block.startswith("## Dynamic Block")
    assert len(static_block) > 0
    assert len(dynamic_block) > 0


def test_build_cached_messages_marks_static_block_as_ephemeral():
    messages = claude_client.build_cached_messages(
        "relevance_filter", {"article": {"title_original": "샘플"}}
    )
    assert len(messages) == 2
    assert messages[0]["cache_control"] == {"type": "ephemeral"}
    assert "cache_control" not in messages[1]
    assert "샘플" in messages[1]["text"]


def test_split_prompt_blocks_rejects_prompt_without_blocks():
    with pytest.raises(ValueError):
        claude_client.split_prompt_blocks("# 그냥 아무 텍스트\n내용만 있음")
