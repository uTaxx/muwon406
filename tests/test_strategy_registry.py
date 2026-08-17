import pytest

from muwon.domain.interfaces import Strategy
from muwon.strategy.registry import (
    REGISTRY,
    build_strategy,
    get_definition,
    list_definitions,
)


def test_registry_has_a_live_entry():
    live_entries = [d for d in REGISTRY if d.status == "live"]
    assert len(live_entries) == 1
    assert live_entries[0].key == "ma_rsi_v1"


def test_registry_keys_are_unique():
    keys = [d.key for d in REGISTRY]
    assert len(keys) == len(set(keys))


def test_build_strategy_returns_working_strategy_named_after_key():
    strategy = build_strategy("ma_rsi_v1")
    assert isinstance(strategy, Strategy)
    assert strategy.name == "ma_rsi_v1"


def test_build_strategy_variant_has_different_params():
    default = build_strategy("ma_rsi_v1")
    fast = build_strategy("ma_rsi_fast5_20")
    assert default.params.sma_short != fast.params.sma_short


def test_get_definition_unknown_key_raises_with_known_keys_listed():
    with pytest.raises(KeyError, match="ma_rsi_v1"):
        get_definition("does-not-exist")


def test_list_definitions_returns_a_copy_not_the_live_registry():
    definitions = list_definitions()
    definitions.append("mutation-should-not-leak")
    assert "mutation-should-not-leak" not in REGISTRY
