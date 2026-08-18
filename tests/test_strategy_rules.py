"""매매 기준 설명 검증.

설명이 코드와 어긋나면 아무 설명도 없는 것보다 나쁘다 — 화면을 믿고
판단하게 되기 때문이다."""

import pytest

from muwon.dashboard.strategy_rules import Rules, common_rules, describe
from muwon.settings.schema import RiskPolicy
from muwon.strategy.breakout import VolumeSurgeParams, VolumeSurgeStrategy
from muwon.strategy.registry import build_strategy, list_definitions


def _text(rules: Rules) -> str:
    return " ".join(rules.산다 + rules.판다 + rules.참고)


@pytest.mark.parametrize("definition", list_definitions(), ids=lambda d: d.key)
def test_every_registered_strategy_explains_itself(definition):
    """새 전략을 등록하고 설명을 안 붙이면 여기서 잡힌다.

    안 잡으면 화면에 파라미터 덤프만 뜨는데, 그건 아무도 못 읽는다."""
    rules = describe(build_strategy(definition.key))
    assert rules.설명있음, f"{definition.key}: strategy_rules.py에 문장을 붙여야 한다"
    assert rules.산다, f"{definition.key}: 사는 조건이 비었다"
    assert rules.판다, f"{definition.key}: 파는 조건이 비었다"


def test_the_sentences_are_built_from_live_parameters():
    """설명을 손으로 적어 두면 파라미터를 바꿔도 옛 글이 남는다.

    같은 전략 클래스에 다른 숫자를 넣었을 때 문장이 따라 바뀌어야 한다."""
    기본 = describe(VolumeSurgeStrategy(VolumeSurgeParams()))
    빡센 = describe(
        VolumeSurgeStrategy(VolumeSurgeParams(volume_surge_ratio=3.0, holding_days=3))
    )

    assert "2배" in _text(기본) and "5거래일" in _text(기본)
    assert "3배" in _text(빡센) and "3거래일" in _text(빡센)
    assert "2배" not in _text(빡센), "옛 숫자가 남으면 설명이 거짓말이 된다"


def test_an_optional_condition_only_shows_when_it_is_on():
    """켜지지도 않은 조건을 설명에 적으면 '왜 안 사지'를 엉뚱한 데서 찾게 된다."""
    켬 = describe(build_strategy("macd_cross_positive"))
    끔 = describe(build_strategy("macd_cross"))
    assert any("0보다 클 때" in line for line in 켬.산다)
    assert not any("0보다 클 때" in line for line in 끔.산다)


def test_an_unknown_strategy_shows_its_settings_instead_of_nothing():
    """설명을 안 붙인 전략이라도 빈 화면을 주면 안 된다."""

    class 낯선파라미터:
        pass

    class 낯선전략:
        params = 낯선파라미터()

    rules = describe(낯선전략())
    assert not rules.설명있음
    assert rules.참고, "최소한 '설명이 없다'는 사실은 보여야 한다"


def test_common_rules_carry_the_actual_policy_numbers():
    policy = RiskPolicy(
        max_position_weight=0.25,
        stop_loss_pct=-0.07,
        daily_loss_limit_pct=-0.03,
        max_concurrent_positions=4,
        trading_enabled=True,
    )
    text = " ".join(common_rules(policy, 60, "market_cap"))
    assert "25%" in text
    assert "7%" in text
    assert "3%" in text
    assert "4종목" in text
    assert "60개" in text


def test_the_kill_switch_wording_says_stops_do_still_run():
    """'꺼짐'을 '방치'로 읽으면 안 된다 — 보유분 손절은 계속 작동한다."""
    off = " ".join(common_rules(RiskPolicy(trading_enabled=False), 60, "market_cap"))
    assert "손절은 그대로" in off
