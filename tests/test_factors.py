"""개별 Factor 검증 — 특히 예전 구조에서 만들 수 없던 두 개.

상대강도와 시장국면은 '다른 종목을 봐야' 계산되므로, generate_signals(symbol, df)
시절에는 구현 자체가 불가능했다. 그게 정말로 가능해졌는지 확인하는 게 이
파일의 핵심이다."""

from datetime import date, timedelta

import pandas as pd
import pytest

from muwon.factors.cross_sectional import MarketRegimeFactor, RelativeStrengthFactor
from muwon.factors.technical import (
    MomentumFactor,
    PullbackFactor,
    TrendFactor,
    VolumeFactor,
)
from muwon.strategy.portfolio import MarketContext


def frame(closes, volumes=None, start=date(2024, 1, 2)):
    n = len(closes)
    volumes = volumes or [100_000] * n
    return pd.DataFrame(
        {
            "trade_date": [start + timedelta(days=i) for i in range(n)],
            "open": closes,
            "high": [c * 1.01 for c in closes],
            "low": [c * 0.99 for c in closes],
            "close": closes,
            "volume": volumes,
        }
    )


def ctx_of(histories, index_history=None):
    as_of = max(df["trade_date"].iloc[-1] for df in histories.values())
    return MarketContext(as_of=as_of, histories=histories, index_history=index_history)


# ── 상대강도: 옛 구조에서 불가능했던 것 ──────────────────────────


def test_relative_strength_ranks_within_universe():
    """같은 날 다른 종목과 비교해야만 나오는 점수다.

    셋 다 오르지만 오름폭이 다르면, 가장 많이 오른 쪽이 상위여야 한다."""
    histories = {
        "FAST": frame([100 + i * 1.0 for i in range(120)]),
        "MID": frame([100 + i * 0.5 for i in range(120)]),
        "SLOW": frame([100 + i * 0.1 for i in range(120)]),
    }
    factor = RelativeStrengthFactor({"period": 60})
    ctx = ctx_of(histories)
    factor.prepare(ctx)

    scores = {s: factor.score(s, ctx).score for s in histories}

    assert scores["FAST"] > scores["MID"] > scores["SLOW"]
    assert scores["FAST"] == 100.0


def test_relative_strength_uses_index_when_given():
    """지수를 주면 초과수익 기준으로 바뀐다 — 지수가 없어도 죽지 않아야 한다."""
    histories = {"A": frame([100 + i for i in range(120)])}
    index = frame([100 + i * 2 for i in range(120)])

    with_index = RelativeStrengthFactor({"period": 60})
    ctx = ctx_of(histories, index_history=index)
    with_index.prepare(ctx)
    assert "지수 대비" in with_index.score("A", ctx).reason

    without = RelativeStrengthFactor({"period": 60})
    ctx2 = ctx_of(histories)
    without.prepare(ctx2)
    assert "유니버스 내" in without.score("A", ctx2).reason


def test_relative_strength_is_not_absolute_return():
    """전부 하락하는 장에서도 '덜 빠진 종목'은 상위여야 한다.
    절대 수익률로 점수를 매기면 이 구분이 사라진다."""
    histories = {
        "LESS_BAD": frame([200 - i * 0.2 for i in range(120)]),
        "WORSE": frame([200 - i * 1.0 for i in range(120)]),
    }
    factor = RelativeStrengthFactor({"period": 60})
    ctx = ctx_of(histories)
    factor.prepare(ctx)

    assert factor.score("LESS_BAD", ctx).score > factor.score("WORSE", ctx).score


# ── 시장 국면 ────────────────────────────────────────────────────


def test_regime_gives_every_symbol_the_same_score():
    """국면은 종목을 고르는 값이 아니라 시장 전체를 누르거나 띄우는 값이다."""
    histories = {f"S{i}": frame([100 + i * 0.1 + j for j in range(80)]) for i in range(4)}
    factor = MarketRegimeFactor()
    ctx = ctx_of(histories)
    factor.prepare(ctx)

    scores = {s: factor.score(s, ctx).score for s in histories}
    assert len(set(scores.values())) == 1


def test_regime_reports_unavailable_when_history_too_short():
    factor = MarketRegimeFactor()
    ctx = ctx_of({"A": frame([100.0] * 10)})
    factor.prepare(ctx)

    assert factor.regime is None
    assert factor.score("A", ctx).score is None


# ── 추세 ─────────────────────────────────────────────────────────


def test_trend_scores_full_alignment_higher_than_broken():
    rising = frame([100 + i for i in range(200)])
    falling = frame([300 - i for i in range(200)])
    factor = TrendFactor()

    up = factor.score("A", ctx_of({"A": rising})).score
    down = factor.score("A", ctx_of({"A": falling})).score

    assert up == 100.0
    assert down == 0.0


def test_trend_reports_reason_in_words():
    """점수만 남기면 나중에 왜 그랬는지 알 수 없다."""
    result = TrendFactor().score("A", ctx_of({"A": frame([100 + i for i in range(200)])}))
    assert "정배열" in result.reason and "종가>20일선" in result.reason


# ── 눌림목 ───────────────────────────────────────────────────────


def test_pullback_prefers_moderate_dip_over_deep_crash():
    """많이 떨어졌다고 좋은 게 아니다 — 눌림과 추세훼손을 구분해야 한다."""
    base = [100 + i for i in range(120)]  # 꾸준한 상승으로 60일선 위 확보
    moderate = frame(base + [base[-1] * 0.94])  # 고점 대비 -6%
    crash = frame(base + [base[-1] * 0.80])  # -20%

    factor = PullbackFactor()
    moderate_score = factor.score("A", ctx_of({"A": moderate})).score
    crash_score = factor.score("A", ctx_of({"A": crash})).score

    assert moderate_score > crash_score


def test_pullback_is_zero_below_long_term_average():
    """장기선 아래로 내려간 건 눌림이 아니라 하락이다."""
    falling = frame([300 - i * 1.5 for i in range(120)])
    result = PullbackFactor().score("A", ctx_of({"A": falling}))

    assert result.score == 0.0
    assert "하락" in result.reason


# ── 거래량 ───────────────────────────────────────────────────────


def test_volume_scales_with_surge_ratio():
    quiet = frame([100.0] * 40, [100_000] * 40)
    surge = frame([100.0] * 40, [100_000] * 39 + [300_000])
    factor = VolumeFactor()

    assert factor.score("A", ctx_of({"A": surge})).score > factor.score(
        "A", ctx_of({"A": quiet})
    ).score


def test_volume_rejects_illiquid_stock():
    """거래대금이 너무 작으면 신호가 맞아도 원하는 가격에 못 산다."""
    thin = frame([100.0] * 40, [100] * 39 + [1_000])
    result = VolumeFactor({"min_turnover_krw": 2_000_000_000}).score("A", ctx_of({"A": thin}))

    assert result.score == 0.0
    assert "유동성" in result.reason


# ── 미래를 보지 않는가 ───────────────────────────────────────────


def test_factors_ignore_data_after_as_of():
    """백테스트는 성능 때문에 전체 프레임을 그대로 넘긴다. 자르는 책임이
    Factor에 있으므로, as_of 이후 행이 결과를 바꾸면 안 된다."""
    closes = [100 + i for i in range(150)]
    full = frame(closes + [999.0] * 10)  # as_of 이후에 폭등이 있는 프레임
    as_of = full["trade_date"].iloc[len(closes) - 1]

    trimmed_ctx = MarketContext(as_of=as_of, histories={"A": frame(closes)})
    full_ctx = MarketContext(as_of=as_of, histories={"A": full})

    for factor_cls in (TrendFactor, PullbackFactor, VolumeFactor):
        factor_a, factor_b = factor_cls(), factor_cls()
        factor_a.prepare(trimmed_ctx)
        factor_b.prepare(full_ctx)
        assert factor_a.score("A", trimmed_ctx).score == pytest.approx(
            factor_b.score("A", full_ctx).score
        ), f"{factor_cls.__name__}이 as_of 이후 데이터를 보고 있다"


def test_momentum_weights_long_horizons_over_a_single_spike():
    """최근 수익률만 보면 하루 급등에 속는다.

    오래 흘러내리다 마지막 하루 튄 종목(5일 수익률은 크지만 120일은 마이너스)
    보다, 꾸준히 오른 종목이 높아야 한다. 장기 기간에 더 큰 가중치를 두는
    이유가 이것이다(인수인계서 8.2항)."""
    steady = frame([100 + i * 0.8 for i in range(150)])
    faded = frame([200 - i * 0.6 for i in range(149)] + [140.0])  # 하락 뒤 하루 급등

    factor = MomentumFactor()
    ctx = ctx_of({"STEADY": steady, "FADED": faded})
    factor.prepare(ctx)

    steady_result = factor.score("STEADY", ctx)
    faded_result = factor.score("FADED", ctx)

    assert "5일 +2" in faded_result.reason  # 단기만 보면 급등처럼 보이지만
    assert steady_result.score > faded_result.score  # 장기가 반영돼 뒤집힌다
