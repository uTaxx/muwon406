from muwon.indicators.technical import add_indicators
from tests.price_series import flat_then_breakout


def test_sma_short_nan_before_window_then_populated():
    df = add_indicators(flat_then_breakout())
    assert df["sma_short"].iloc[:19].isna().all()
    assert df["sma_short"].iloc[19:].notna().all()


def test_rsi_within_bounds_once_available():
    df = add_indicators(flat_then_breakout())
    rsi = df["rsi"].dropna()
    assert len(rsi) > 0
    assert (rsi >= 0).all() and (rsi <= 100).all()


def test_volume_ma_matches_rolling_mean():
    df = add_indicators(flat_then_breakout())
    expected = df["volume"].rolling(window=20).mean()
    pd_equal = (df["volume_ma"].fillna(-1) == expected.fillna(-1)).all()
    assert pd_equal


def test_custom_windows_change_column_values():
    df_default = add_indicators(flat_then_breakout())
    df_custom = add_indicators(flat_then_breakout(), sma_short=5, sma_long=20, rsi_period=7, volume_ma_window=5)
    assert df_custom["sma_short"].iloc[:4].isna().all()
    assert df_custom["sma_short"].iloc[4:].notna().all()
    assert not df_default["sma_short"].equals(df_custom["sma_short"])


def test_adx_on_a_freshly_listed_stock_returns_blanks_not_a_crash():
    """상장한 지 얼마 안 된 종목은 봉이 몇 개 없다.

    ta 라이브러리는 그럴 때 IndexError로 터진다 — 60종목 5년 비교에서
    봉 11개짜리 종목 하나 때문에 실험 전체가 죽었다. 지표를 못 구하는 건
    정상 상황이므로 빈 값이어야 한다."""
    import pandas as pd

    from muwon.indicators.technical import add_adx

    짧은시세 = pd.DataFrame(
        {
            "trade_date": pd.date_range("2024-01-01", periods=11).date,
            "open": range(100, 111),
            "high": range(101, 112),
            "low": range(99, 110),
            "close": range(100, 111),
            "volume": [1000] * 11,
        }
    )
    결과 = add_adx(짧은시세, window=14)
    assert len(결과) == 11
    assert 결과["adx"].isna().all(), "계산할 수 없으면 빈 값이어야 한다"
