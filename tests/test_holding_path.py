"""보유 구간 되짚기 검증."""

from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd
import pytest

from muwon.analysis.holding_path import format_paths, trace


@dataclass
class FakeTrade:
    symbol: str
    entry_date: date
    exit_date: date
    entry_price: float
    pnl_pct: float


def frame(symbol: str, start: date, closes: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "trade_date": [start + timedelta(days=i) for i in range(len(closes))],
            "close": closes,
        }
    )


def test_it_finds_the_peak_and_the_giveback():
    """+20%까지 갔다가 +5%에 판 매매는 15%를 도로 뱉은 것이다."""
    df = frame("A", date(2024, 1, 1), [100, 110, 120, 108, 105])
    paths = trace(
        [FakeTrade("A", date(2024, 1, 1), date(2024, 1, 5), 100.0, 5.0)], {"A": df}
    )

    assert len(paths) == 1
    path = paths[0]
    # 부동소수 나눗셈이라 정확히 20.0이 아니다 — approx 없이 쓰면
    # 내용은 맞는데 테스트만 깨진다.
    assert path.고점_pct == pytest.approx(20.0)
    assert path.청산_pct == pytest.approx(5.0)
    assert path.되돌림_pct == pytest.approx(15.0)
    assert path.고점까지_일 == 2


def test_giveback_never_goes_negative():
    """고점보다 높은 값에 팔 수는 없다. 데이터가 어긋나도 음수 되돌림을
    내보내면 표가 조용히 거짓말을 한다."""
    df = frame("A", date(2024, 1, 1), [100, 101])
    paths = trace(
        [FakeTrade("A", date(2024, 1, 1), date(2024, 1, 2), 100.0, 50.0)], {"A": df}
    )
    assert paths[0].되돌림_pct == 0.0


def test_a_trade_with_no_price_history_is_skipped_not_guessed():
    paths = trace([FakeTrade("없음", date(2024, 1, 1), date(2024, 1, 5), 100.0, 3.0)], {})
    assert paths == []


def test_the_peak_on_the_entry_day_counts_as_day_zero():
    """사자마자 고점인 경우가 실제로 가장 많다 — 그걸 1일째로 세면
    '재료가 하루 갔다'는 그림이 잘못 나온다."""
    df = frame("A", date(2024, 1, 1), [100, 95, 90])
    paths = trace(
        [FakeTrade("A", date(2024, 1, 1), date(2024, 1, 3), 100.0, -10.0)], {"A": df}
    )
    assert paths[0].고점까지_일 == 0


def test_empty_input_says_so_instead_of_printing_zeros():
    """표본이 없는데 0%로 채우면 '되돌림이 없다'로 읽힌다."""
    assert "완결된 매매가 없습니다" in format_paths([])


def test_the_report_separates_winners_from_losers():
    """이긴 매매와 진 매매를 섞으면 되돌림 평균이 뜻을 잃는다 —
    진 매매는 애초에 오른 적이 없어 되돌림이 곧 손실폭이다."""
    df = frame("A", date(2024, 1, 1), [100, 120, 110])
    paths = trace(
        [
            FakeTrade("A", date(2024, 1, 1), date(2024, 1, 3), 100.0, 10.0),
            FakeTrade("A", date(2024, 1, 1), date(2024, 1, 3), 100.0, -5.0),
        ],
        {"A": df},
    )
    report = format_paths(paths)
    assert "이익 매매" in report
    assert "손실 매매" in report
