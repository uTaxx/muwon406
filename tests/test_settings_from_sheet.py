"""시트의 설정 값이 매매 정책이 되는 자리.

여기서 틀리면 **단위 하나 때문에 자금 전부가 한 종목에 들어간다.**
그래서 규칙 하나마다 시험을 붙였다."""

import pytest

from muwon.settings.from_sheet import (
    SettingsError,
    apply,
    describe,
    parse_settings,
    시트설정,
)
from muwon.settings.schema import RiskPolicy


def 기본설정(**덮개):
    값 = {
        "trading_enabled": "false",
        "max_position_weight": "15",
        "max_concurrent_positions": "8",
        "stop_loss_pct": "-5",
        "daily_loss_limit_pct": "-3",
        "min_turnover_eok": "50",
        "require_approval": "true",
    }
    값.update(덮개)
    return 값


def test_퍼센트를_소수로_바꾼다():
    """시트에 15라고 적으면 0.15여야 한다. 그냥 넘기면 자금의 1,500%다."""
    결과 = parse_settings(기본설정())
    assert 결과.덮개["max_position_weight"] == pytest.approx(0.15)
    assert 결과.덮개["stop_loss_pct"] == pytest.approx(-0.05)
    assert 결과.덮개["daily_loss_limit_pct"] == pytest.approx(-0.03)


def test_킬스위치는_빈칸이면_꺼진다():
    """종목 탭과 규칙이 **반대**다. 매매를 켜려면 명시해야 한다."""
    assert parse_settings(기본설정(trading_enabled="")).덮개["trading_enabled"] is False
    assert parse_settings(기본설정(trading_enabled="아무말")).덮개["trading_enabled"] is False
    assert parse_settings(기본설정(trading_enabled="Y")).덮개["trading_enabled"] is True
    assert parse_settings(기본설정(trading_enabled="true")).덮개["trading_enabled"] is True


def test_비중상한이_범위를_벗어나면_거부한다():
    with pytest.raises(SettingsError, match="분산이 아닙니다"):
        parse_settings(기본설정(max_position_weight="80"))
    with pytest.raises(SettingsError):
        parse_settings(기본설정(max_position_weight="0"))


def test_손절선을_양수로_적으면_거부한다():
    """'5% 빠지면 판다'를 5로 적는 실수를 잡는다 — 그대로 두면 손절이 안 걸린다."""
    with pytest.raises(SettingsError, match="-5처럼"):
        parse_settings(기본설정(stop_loss_pct="5"))


def test_동시보유가_정수가_아니면_거부한다():
    with pytest.raises(SettingsError, match="정수"):
        parse_settings(기본설정(max_concurrent_positions="8.5"))
    with pytest.raises(SettingsError):
        parse_settings(기본설정(max_concurrent_positions="0"))


def test_모르는_이름은_막지_않되_알린다():
    """오타 난 줄이 매매를 멈추면 안 되지만, 조용히 넘어가도 안 된다."""
    결과 = parse_settings(기본설정(stop_loss="-5", 메모="아무거나"))
    assert set(결과.모르는이름) == {"stop_loss", "메모"}
    assert "stop_loss_pct" in 결과.덮개  # 제대로 된 이름은 그대로 먹는다


def test_빈칸은_덮지_않는다():
    """빈 칸은 '0으로 하라'가 아니라 '안 적었다'다 — DB 값이 살아야 한다."""
    결과 = parse_settings(기본설정(max_position_weight=""))
    assert "max_position_weight" not in 결과.덮개


def test_승인은_빈칸이면_받는다():
    assert parse_settings(기본설정(require_approval="")).승인필요 is True
    assert parse_settings(기본설정(require_approval="N")).승인필요 is False


def test_시트가_DB를_이긴다():
    정책 = RiskPolicy(max_position_weight=0.10, trading_enabled=True)
    새정책, 출처 = apply(정책, parse_settings(기본설정(max_position_weight="20")))
    assert 새정책.max_position_weight == pytest.approx(0.20)
    assert 출처["max_position_weight"] == "시트"
    assert 출처["atr_stop_multiple"] == "DB"  # 시트에 없는 항목은 DB 그대로


def test_시트를_못_읽으면_매매를_끈다():
    """제일 나쁜 고장은 '사람은 껐다고 믿는데 코드는 켜진 채 도는' 것이다."""
    정책 = RiskPolicy(trading_enabled=True)
    새정책, 출처 = apply(정책, None)
    assert 새정책.trading_enabled is False
    assert "못 읽어" in 출처["trading_enabled"]


def test_설명에_출처와_경고가_보인다():
    시트 = parse_settings(기본설정(오타항목="x"))
    정책, 출처 = apply(RiskPolicy(), 시트)
    글 = describe(정책, 출처, 시트)
    assert "꺼짐" in 글
    assert "[시트]" in 글
    assert "오타항목" in 글
    assert "아무 효과가 없습니다" in 글


def test_설명은_시트가_없어도_돈다():
    정책, 출처 = apply(RiskPolicy(), None)
    글 = describe(정책, 출처, None)
    assert "매매를 껐습니다" in 글


def test_최소거래대금이_음수면_거부한다():
    with pytest.raises(SettingsError, match="음수"):
        parse_settings(기본설정(min_turnover_eok="-1"))


def test_아무것도_없으면_안전한_기본값():
    빈것 = 시트설정()
    assert 빈것.승인필요 is True
    정책, _ = apply(RiskPolicy(), 빈것)
    assert 정책.max_position_weight == RiskPolicy().max_position_weight


class 가짜서비스:
    def __init__(self, 정책):
        self._정책 = 정책

    def get_risk_policy(self):
        return self._정책


def test_제공자는_한번만_읽는다():
    """한 회차 도는 중간에 기준이 바뀌면 로그를 봐도 왜 그랬는지 모른다."""
    from muwon.settings.from_sheet import build_policy_provider

    센횟수 = {"n": 0}

    def 읽기():
        센횟수["n"] += 1
        return 기본설정(trading_enabled="Y", max_position_weight="12")

    제공자, 글, 시트 = build_policy_provider(가짜서비스(RiskPolicy()), "sheet", reader=읽기)
    for _ in range(5):
        assert 제공자().max_position_weight == pytest.approx(0.12)
    assert 센횟수["n"] == 1
    assert 시트 is not None
    assert "켜짐" in 글


def test_제공자는_읽기가_터져도_죽지_않고_매매를_끈다():
    from muwon.settings.from_sheet import build_policy_provider

    def 터짐():
        raise RuntimeError("구글이 안 받음")

    제공자, 글, 시트 = build_policy_provider(
        가짜서비스(RiskPolicy(trading_enabled=True)), "sheet", reader=터짐
    )
    assert 제공자().trading_enabled is False
    assert 시트 is None
    assert "구글이 안 받음" in 글


def test_제공자는_시트값이_틀리면도_매매를_끈다():
    """검증에 걸린 시트로 그냥 돌면, 틀린 기준으로 실제 주문이 나간다."""
    from muwon.settings.from_sheet import build_policy_provider

    제공자, 글, 시트 = build_policy_provider(
        가짜서비스(RiskPolicy(trading_enabled=True)),
        "sheet",
        reader=lambda: 기본설정(max_position_weight="500"),
    )
    assert 제공자().trading_enabled is False
    assert 시트 is None
    assert "SettingsError" in 글


def test_킬스위치는_둘_다_켜져야_켜진다():
    """시트가 DB의 킬스위치를 무력화하면 안 된다 — 끄는 쪽은 어디서 눌러도 먹어야 한다."""
    켠시트 = parse_settings(기본설정(trading_enabled="Y"))
    끈시트 = parse_settings(기본설정(trading_enabled="N"))

    # DB 켬 + 시트 켬 → 켜짐
    정책, 출처 = apply(RiskPolicy(trading_enabled=True), 켠시트)
    assert 정책.trading_enabled is True
    assert 출처["trading_enabled"] == "시트+DB 둘 다 켬"

    # DB 끔 + 시트 켬 → **꺼짐** (예전이라면 시트가 이겨 켜졌다)
    정책, 출처 = apply(RiskPolicy(trading_enabled=False), 켠시트)
    assert 정책.trading_enabled is False
    assert 출처["trading_enabled"] == "DB에서 끔"

    # DB 켬 + 시트 끔 → 꺼짐
    정책, 출처 = apply(RiskPolicy(trading_enabled=True), 끈시트)
    assert 정책.trading_enabled is False
    assert 출처["trading_enabled"] == "시트에서 끔"


def test_시트에_킬스위치_줄이_아예_없으면_꺼진다():
    """줄이 지워졌다고 매매가 켜지면 안 된다."""
    없음 = 기본설정()
    del 없음["trading_enabled"]
    정책, 출처 = apply(RiskPolicy(trading_enabled=True), parse_settings(없음))
    assert 정책.trading_enabled is False
    assert 출처["trading_enabled"] == "시트에 없어 꺼짐"
