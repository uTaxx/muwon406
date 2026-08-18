"""지금 돌고 있는 전략이 **무엇을 보고 사고파는지**를 사람 말로 옮긴다.

왜 필요한가 — 화면에는 전략 이름만 떠 있었다. `volume_surge_5d`라는 이름은
그 전략이 무엇을 사는지 아무것도 말해 주지 않는다. 무엇을 기준으로 샀는지
모르면, 결과를 봐도 무엇을 고쳐야 할지 판단할 수 없다.

**설명을 손으로 적어 두지 않는다.** registry의 description은 사람이 쓴
글이라 코드가 바뀌어도 그대로 남는다(실제로 그렇게 어긋난 문서를 여럿 봤다).
여기서는 전략 객체의 **실제 파라미터**를 읽어서 문장을 만든다. 파라미터를
바꾸면 설명도 같이 바뀐다.

모르는 전략이 새로 등록되면 파라미터를 그대로 나열한다 — 문장이 없더라도
빈 화면보다는 낫고, '설명을 안 붙였다'는 사실 자체가 보인다.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass


@dataclass(frozen=True)
class Rules:
    """한 전략의 매매 기준.

    산다·판다·덧붙는 조건을 나눠 둔다. 한 덩어리 글로 두면 '언제 파는가'를
    찾으려고 매번 다시 읽어야 한다."""

    산다: list[str]
    #: **전략 자신의** 매도 신호만. 보유 기간 경과와 손절은 엔진이 따로
    #: 검사하므로 여기 넣지 않는다 — 넣었더니 화면에 같은 줄이 두 번 나왔다.
    #: 파는 조건 전부를 한자리에서 보려면 exit_rules()를 쓴다.
    판다: list[str]
    참고: list[str]
    설명있음: bool = True


def _pct(value: float) -> str:
    return f"{value:g}%"


def _volume_surge(ratio: float, window: int) -> str:
    return f"거래량이 최근 {window}일 평균의 **{ratio:g}배** 이상으로 늘고"


def describe(strategy) -> Rules:
    """전략 객체 하나를 받아 매매 기준을 문장으로 만든다."""
    params = getattr(strategy, "params", None)
    if params is None:
        return _describe_score(strategy)

    name = type(params).__name__
    builder = _BUILDERS.get(name)
    if builder is None:
        return _fallback(params)
    return builder(params, strategy)


def _fallback(params) -> Rules:
    """문장을 안 붙인 전략 — 파라미터라도 그대로 보여 준다."""
    lines = [f"{f.name} = {getattr(params, f.name)}" for f in fields(params)] if is_dataclass(params) else []
    return Rules(
        산다=[],
        판다=[],
        참고=["이 전략은 아직 사람 말 설명이 없습니다. 실제 설정값은 아래와 같습니다.", *lines],
        설명있음=False,
    )


# ── 전략별 문장 ────────────────────────────────────────────────────────
# 각 함수는 그 전략의 generate_signals를 그대로 읽고 옮긴 것이다.
# 코드와 어긋나면 그건 버그다 — 테스트가 파라미터 값이 문장에 들어갔는지까지 본다.


def _volume_surge_rules(p, strategy) -> Rules:
    return Rules(
        산다=[
            (f"{_volume_surge(p.volume_surge_ratio, p.volume_ma_window)} "
            f"그날 종가가 전날보다 **{_pct(p.min_price_change_pct)} 이상** 오른 종목"),
        ],
        # 이 전략은 지표로 파는 조건이 없다 — 보유 기간(max_holding_days)은
        # 엔진이 검사하므로 exit_rules가 낸다.
        판다=[],
        참고=[
            ("파는 조건이 지표가 아니라 **시간**입니다. "
            "'재료가 터진 날 들어가서 며칠 안에 나온다'는 단타 방식입니다."),
            "그래서 자주 사고팝니다 — 수수료와 슬리피지가 여러 번 붙습니다.",
        ],
    )


def _bollinger_breakout_rules(p, strategy) -> Rules:
    return Rules(
        산다=[
            (f"종가가 볼린저밴드 **상단선을 위로 뚫고**({p.window}일 평균 ± 표준편차 {p.num_std:g}배), "
            f"{_volume_surge(p.volume_surge_ratio, p.volume_ma_window)} 있을 때"),
        ],
        판다=["종가가 볼린저 **중심선 아래**로 내려가면"],
        참고=[
            ("같은 지표를 '과열이니 곧 떨어진다'로 읽는 전략도 있습니다(볼린저 평균회귀). "
            "여기서는 반대로 '뚫을 만큼 힘이 세니 더 간다'로 읽습니다."),
        ],
    )


def _price_channel_rules(p, strategy) -> Rules:
    문턱 = f" + {_pct(p.breakout_pct)}" if p.breakout_pct else ""
    return Rules(
        산다=[f"종가가 **직전 {p.lookback}일 중 가장 높은 종가**{문턱}를 넘어설 때"],
        판다=[f"종가가 **{p.exit_sma}일 이동평균선을 아래로 뚫으면**"],
        참고=["신고가를 따라 사는 방식이라, 이미 많이 오른 뒤에 들어갑니다."],
    )


def _golden_cross_rules(p, strategy) -> Rules:
    return Rules(
        산다=[f"**{p.sma_short}일 이동평균선이 {p.sma_long}일선을 위로 뚫을 때**(골든크로스)"],
        판다=[f"**{p.sma_short}일선이 {p.sma_long}일선을 아래로 뚫으면**(데드크로스)"],
        참고=["평균선끼리의 교차라 신호가 늦게 뜹니다. 이미 오른 뒤에 사는 경우가 많습니다."],
    )


def _ema_cross_rules(p, strategy) -> Rules:
    return Rules(
        산다=[f"**{p.ema_short}일 지수이동평균이 {p.ema_long}일선을 위로 뚫을 때**"],
        판다=[f"**{p.ema_short}일선이 {p.ema_long}일선을 아래로 뚫으면**"],
        참고=["지수이동평균은 최근 가격에 더 무게를 둬서, 보통 이동평균선보다 빨리 반응합니다."],
    )


def _macd_rules(p, strategy) -> Rules:
    조건 = ["**MACD가 신호선을 위로 뚫을 때**"]
    if p.require_positive_macd:
        조건.append("단, MACD가 0보다 클 때(이미 상승 국면일 때)만")
    return Rules(
        산다=조건,
        판다=["**MACD가 신호선을 아래로 뚫으면**"],
        참고=[
            (f"MACD는 {p.fast}일선과 {p.slow}일선의 차이, 신호선은 그 값의 {p.signal}일 평균입니다. "
            "'상승 힘이 붙는 순간'을 잡으려는 지표입니다."),
        ],
    )


def _donchian_rules(p, strategy) -> Rules:
    조건 = [f"종가가 **최근 {p.entry_window}일 최고가를 넘어설 때**"]
    if p.adx_filter > 0:
        조건.append(f"단, 추세 강도(ADX)가 **{p.adx_filter:g} 이상**일 때만 — 횡보장 회피")
    return Rules(
        산다=조건,
        판다=[f"종가가 **최근 {p.exit_window}일 최저가 아래**로 내려가면"],
        참고=["신고가에 사서 신저가에 파는 고전적인 추세추종 방식입니다."],
    )


def _rsi_reversion_rules(p, strategy) -> Rules:
    조건 = [f"RSI가 **{p.oversold:g} 아래로 빠졌다가 다시 위로 올라올 때**"]
    if p.require_above_long_ma:
        조건.append(f"단, 종가가 **{p.sma_long}일 이동평균선 위**일 때만 — 하락장 회피")
    return Rules(
        산다=조건,
        판다=[f"RSI가 **{p.overbought:g}를 넘으면**(과매수)"],
        참고=[
            f"RSI는 최근 {p.rsi_period}일의 오른 폭·내린 폭을 견줘 0~100으로 나타낸 값입니다.",
            "많이 빠진 걸 사는 방식이라, 계속 빠지면 계속 물립니다 — 손절이 특히 중요합니다.",
        ],
    )


def _bollinger_reversion_rules(p, strategy) -> Rules:
    청산선 = "중심선" if p.exit_at_middle else "상단선"
    return Rules(
        산다=[
            (f"종가가 볼린저 **하단선 아래로 빠졌다가 다시 위로 복귀**할 때"
            f"({p.window}일 평균 ± 표준편차 {p.num_std:g}배)"),
        ],
        판다=[f"종가가 볼린저 **{청산선}에 도달하면**"],
        참고=["'너무 많이 빠졌으니 평균으로 돌아온다'는 가정입니다. 추세가 강하면 계속 틀립니다."],
    )


def _stochastic_rules(p, strategy) -> Rules:
    return Rules(
        산다=[f"스토캐스틱이 **{p.oversold:g} 이하**인 상태에서 **%K가 %D를 위로 뚫을 때**"],
        판다=[f"**{p.overbought:g} 이상**에서 **%K가 %D를 아래로 뚫으면**"],
        참고=[
            (f"최근 {p.window}일 고가~저가 범위에서 지금 종가가 어디쯤인지를 0~100으로 나타낸 값입니다 "
            f"({p.smooth_window}일 평활)."),
        ],
    )


def _ma_rsi_rules(p, strategy) -> Rules:
    return Rules(
        산다=[
            (f"**① 종가가 {p.sma_short}일선을 위로 뚫고** + "
            f"{_volume_surge(p.volume_surge_ratio, p.volume_ma_window)} + "
            f"RSI가 **{p.rsi_buy_ceiling:g} 미만**일 때(너무 오른 건 제외)"),
            f"**② RSI가 {p.rsi_oversold:g} 아래에서 반등**하고 종가가 **{p.sma_long}일선 위**일 때",
        ],
        판다=[
            f"종가가 **{p.sma_short}일선을 아래로 뚫으면**",
            f"RSI가 **{p.rsi_overbought:g}를 넘으면**",
        ],
        참고=["사는 이유가 둘(돌파·반등)이라, 둘 중 하나만 맞아도 삽니다."],
    )


def _describe_score(strategy) -> Rules:
    """점수 합산 전략 — 조건이 아니라 점수와 문턱으로 판단한다."""
    config = getattr(strategy, "config", None)
    if config is None:
        return Rules(산다=[], 판다=[], 참고=["설명을 만들 수 없는 전략입니다."], 설명있음=False)

    weights = config.enabled_weights()
    가중치 = ", ".join(f"{k} {v:.0f}%" for k, v in sorted(weights.items(), key=lambda x: -x[1]))
    문턱 = ", ".join(
        f"{regime} {value:g}점" for regime, value in sorted(config.regime_buy_threshold.items())
    )
    return Rules(
        산다=[
            f"여러 기준에 점수를 매겨 합산하고, 총점이 **{config.buy_threshold:g}점 이상**이면 매수",
            f"쓰이는 기준과 비중: {가중치}",
        ],
        판다=["점수가 문턱 아래로 떨어지거나, 리스크 정책의 손절 조건에 걸리면"],
        참고=[
            (f"시장 국면에 따라 매수 문턱이 달라집니다 — {문턱}. "
            "내리는 판에서는 문턱을 크게 올려 사실상 안 삽니다."),
            "조건 한두 개가 아니라 여러 기준의 **합계**로 고르는 방식입니다.",
        ],
    )


_BUILDERS = {
    "VolumeSurgeParams": _volume_surge_rules,
    "BollingerBreakoutParams": _bollinger_breakout_rules,
    "PriceChannelParams": _price_channel_rules,
    "GoldenCrossParams": _golden_cross_rules,
    "EmaCrossParams": _ema_cross_rules,
    "MacdCrossParams": _macd_rules,
    "DonchianBreakoutParams": _donchian_rules,
    "RsiReversionParams": _rsi_reversion_rules,
    "BollingerReversionParams": _bollinger_reversion_rules,
    "StochasticParams": _stochastic_rules,
    "MovingAverageRsiParams": _ma_rsi_rules,
}


def common_rules(policy, universe_size: int, universe_kind: str) -> list[str]:
    """전략이 무엇이든 **항상** 적용되는 규칙.

    전략만 보면 "왜 신호가 났는데 안 샀지"를 설명할 수 없다. 실제로는 이
    규칙들이 먼저 걸러 낸다."""
    return [
        (f"**대상 종목**: {universe_size}개 "
        f"({'시가총액' if universe_kind == 'market_cap' else '거래대금'} 상위). 이 목록 밖은 안 삽니다."),
        "**판단 기준**: 어제까지의 **완성된 일봉**. 오늘 봉은 아직 안 끝나서 쓰지 않습니다.",
        (f"**한 종목당 최대 비중**: {policy.max_position_weight * 100:.0f}% "
        f"(동시에 최대 {policy.max_concurrent_positions}종목)"),
        f"**손절**: 산 값보다 {abs(policy.stop_loss_pct) * 100:.0f}% 빠지면 자동 매도",
        f"**일일 손실 한도**: 하루에 {abs(policy.daily_loss_limit_pct) * 100:.0f}% 잃으면 그날은 신규 매수 중단",
        (
            "**자동매매**: 켜짐 — 조건이 맞으면 실제로 주문이 나갑니다."
            if policy.trading_enabled
            else "**자동매매**: 꺼짐(킬스위치) — 새로 사지 않습니다. 보유분 손절은 그대로 작동합니다."
        ),
    ]


def exit_rules(strategy, policy) -> tuple[list[str], list[str]]:
    """**엔진이 실제로 검사하는 순서대로** 청산 조건 전부.

    왜 따로 두는가 — 전략의 매도 신호만 보여 줬더니 "매도 전략은 기간밖에
    없냐"는 질문을 받았다. 실제로는 손절이 항상 먼저 걸리는데, 그게 리스크
    정책 쪽에 있다는 이유로 다른 칸에 적혀 있었다. **파는 조건은 어디에
    설정돼 있든 한자리에 모여 있어야 한다.**

    (청산 조건들, 덧붙일 주의사항)을 돌려준다."""
    조건: list[str] = []
    주의: list[str] = []

    # 1순위 — 손절. 엔진은 이걸 가장 먼저 본다(risk/exits.py evaluate_exit).
    if getattr(policy, "atr_stop_enabled", False):
        조건.append(
            f"**손절(변동성 기준)** — 산 값에서 그 종목 하루 평균 변동폭"
            f"(ATR {policy.atr_window}일)의 **{policy.atr_stop_multiple:g}배**만큼 빠지면"
        )
    else:
        조건.append(
            f"**손절** — 산 값보다 **{abs(policy.stop_loss_pct) * 100:.0f}%** 빠지면"
        )
    if getattr(policy, "trailing_stop_enabled", False):
        조건.append(
            f"**트레일링 스톱** — 산 뒤 최고가에서 ATR의 "
            f"**{policy.trailing_stop_multiple:g}배**만큼 밀리면"
        )

    # 2순위 — 보유 기간
    holding = getattr(strategy, "max_holding_days", None)
    if holding:
        조건.append(f"**보유 기간** — 산 지 **{holding}거래일**이 지나면 오르든 내리든 무조건")

    # 3순위 — 전략 자신의 매도 신호
    전략 = describe(strategy).판다
    if 전략:
        조건 += [f"**전략 매도 신호** — {line}" for line in 전략]
    elif not holding:
        주의.append(
            "이 전략에는 자체 매도 신호가 없습니다 — 위 손절 외에는 파는 조건이 없다는 뜻입니다."
        )
    else:
        주의.append(
            "이 전략은 **자체 매도 신호가 없습니다**. 지표가 아니라 시간과 손절로만 나옵니다."
        )

    # 익절은 이 시스템에 아예 없다. 없는 걸 안 적으면 '있는데 안 보이는 것'과
    # 구분이 안 된다 — 실제로 그 질문을 받았다.
    주의.append(
        "**익절(목표 수익률에 닿으면 파는 것)은 없습니다.** 오르는 중이라면 "
        "위 조건 중 하나에 걸릴 때까지 그대로 들고 갑니다."
    )
    if not getattr(policy, "atr_stop_enabled", False):
        주의.append(
            "변동성 기준 손절(ATR)과 트레일링 스톱은 코드에는 있지만 **꺼져 있습니다** — "
            "2022년 구간에서 켜 봤더니 손실이 오히려 커져서 기본값을 끔으로 뒀습니다."
        )
    return 조건, 주의
