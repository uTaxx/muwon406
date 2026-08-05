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


def test_model_registry_has_three_tiers():
    registry = claude_client.load_model_registry()
    assert set(registry.keys()) == {"classification", "deep_analysis", "future"}
    for tier in registry.values():
        assert "model_env" in tier
        assert "used_by_prompts" in tier


def test_get_model_name_raises_when_nothing_configured(monkeypatch):
    # 현재 저장소 상태: .env 없음, model_registry.yaml의 model_id는 전부 null,
    # prompts의 default_model_id도 전부 null -> 명시적으로 에러가 나야 한다.
    monkeypatch.delenv("LCIP_CLASSIFICATION_MODEL", raising=False)
    with pytest.raises(RuntimeError):
        claude_client.get_model_name("classification")


def test_get_model_name_prefers_env_var(monkeypatch):
    monkeypatch.setenv("LCIP_CLASSIFICATION_MODEL", "env-override-model")
    assert claude_client.get_model_name("classification") == "env-override-model"


def test_get_model_name_falls_back_to_registry(monkeypatch):
    monkeypatch.delenv("LCIP_DEEP_ANALYSIS_MODEL", raising=False)
    fake_registry = {
        "deep_analysis": {
            "model_env": "LCIP_DEEP_ANALYSIS_MODEL",
            "model_id": "registry-default-model",
            "used_by_prompts": ["risk_analysis"],
        }
    }
    monkeypatch.setattr(claude_client, "load_model_registry", lambda: fake_registry)
    assert claude_client.get_model_name("deep_analysis") == "registry-default-model"


def test_get_model_name_falls_back_to_prompt_default(monkeypatch, tmp_path):
    monkeypatch.delenv("LCIP_FUTURE_READINESS_MODEL", raising=False)
    fake_prompt_dir = tmp_path
    (fake_prompt_dir / "quick_scan.md").write_text(
        "---\nprompt_version: 0.2.0\ndefault_model_id: prompt-fallback-model\n---\n# X\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(claude_client, "PROMPTS_DIR", fake_prompt_dir)
    fake_registry = {
        "future": {
            "model_env": "LCIP_FUTURE_READINESS_MODEL",
            "model_id": None,
            "used_by_prompts": ["quick_scan"],
        }
    }
    monkeypatch.setattr(claude_client, "load_model_registry", lambda: fake_registry)
    assert claude_client.get_model_name("future") == "prompt-fallback-model"


def test_get_model_name_unknown_purpose_raises():
    with pytest.raises(ValueError):
        claude_client.get_model_name("nonexistent_purpose")
