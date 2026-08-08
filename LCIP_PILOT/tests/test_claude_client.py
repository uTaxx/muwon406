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


def test_split_prompt_blocks_rejects_prompt_without_blocks():
    with pytest.raises(ValueError):
        claude_client.split_prompt_blocks("# 그냥 아무 텍스트\n내용만 있음")


def test_model_registry_has_three_tiers():
    registry = claude_client.load_model_registry()
    assert set(registry.keys()) == {"classification", "deep_analysis", "future"}
    for tier in registry.values():
        assert "model_env" in tier
        assert "used_by_prompts" in tier


def test_get_model_name_raises_when_nothing_configured(monkeypatch, tmp_path):
    # Round 13 Priority 1 질문 답변 이후 model_registry.yaml의 model_id 3종은
    # 실제 값으로 채워졌다(더 이상 null이 아니다) — 이 테스트는 그 실제 상태가
    # 아니라 "환경변수도, Registry도, Prompt fallback도 전부 없는" 최후 케이스를
    # 검증해야 하므로 Registry와 Prompt 둘 다 가짜로 비운다.
    monkeypatch.delenv("LCIP_CLASSIFICATION_MODEL", raising=False)
    fake_prompt_dir = tmp_path
    (fake_prompt_dir / "relevance_filter.md").write_text(
        "---\nprompt_version: 0.1.0\n---\n# X\n", encoding="utf-8"
    )
    monkeypatch.setattr(claude_client, "PROMPTS_DIR", fake_prompt_dir)
    fake_registry = {
        "classification": {
            "model_env": "LCIP_CLASSIFICATION_MODEL",
            "model_id": None,
            "used_by_prompts": ["relevance_filter"],
        }
    }
    monkeypatch.setattr(claude_client, "load_model_registry", lambda: fake_registry)
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
