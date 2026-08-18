"""시세 캐시 검증.

캐시는 조용히 틀리면 최악이다 — 백테스트가 다른 데이터를 보고 다른 숫자를
내는데 아무도 모른다. 그래서 '같은 값이 나오는가'와 '언제 안 맞다고
판단하는가'를 둘 다 못 박는다."""

from datetime import date, timedelta

import pandas as pd
import pytest

from muwon.data.price_cache import PriceCache


def frame(start: date, days: int) -> pd.DataFrame:
    """주말을 건너뛴 봉 — 실제 시세처럼 요청 구간 경계에 봉이 없을 수 있다."""
    rows = []
    day = start
    while len(rows) < days:
        if day.weekday() < 5:
            rows.append(
                {
                    "trade_date": day,
                    "open": 100.0 + len(rows),
                    "high": 101.0 + len(rows),
                    "low": 99.0 + len(rows),
                    "close": 100.5 + len(rows),
                    "volume": 1000 + len(rows),
                }
            )
        day += timedelta(days=1)
    return pd.DataFrame(rows)


class CountingSource:
    def __init__(self, df):
        self._df = df
        self.calls = 0

    def get_daily_ohlcv(self, symbol, start, end):
        self.calls += 1
        return self._df


@pytest.fixture
def cache(tmp_path):
    return PriceCache(tmp_path / "prices.sqlite")


def test_second_request_does_not_hit_the_network(cache):
    source = CountingSource(frame(date(2024, 1, 2), 20))
    args = ("005930", "005930.KS", date(2024, 1, 1), date(2024, 2, 1))

    first = cache.fetch(source, *args)
    second = cache.fetch(source, *args)

    assert source.calls == 1
    pd.testing.assert_frame_equal(
        first.reset_index(drop=True), second.reset_index(drop=True)
    )
    assert (cache.hits, cache.misses) == (1, 1)


def test_boundary_on_a_weekend_still_counts_as_covered(cache):
    """이걸로 실제 버그를 잡았다.

    처음엔 저장된 봉의 최초/최종 날짜로 '다 받았는가'를 판단했다. 요청 구간의
    시작·끝이 주말이면 그 날짜의 봉이 있을 수 없으므로 항상 '덜 받았다'가 되어
    캐시가 한 번도 안 맞았다 — 18종목 중 0종목 재사용이었다."""
    saturday, sunday = date(2024, 1, 6), date(2024, 3, 3)
    assert saturday.weekday() == 5
    assert sunday.weekday() == 6

    source = CountingSource(frame(date(2024, 1, 8), 30))
    cache.fetch(source, "005930", "005930.KS", saturday, sunday)
    cache.fetch(source, "005930", "005930.KS", saturday, sunday)

    assert source.calls == 1, "경계가 휴일이어도 재사용해야 한다"


def test_a_wider_range_is_refetched(cache):
    """받아 본 적 없는 구간을 조용히 잘린 데이터로 채우면 안 된다."""
    source = CountingSource(frame(date(2024, 1, 2), 20))
    cache.fetch(source, "005930", "005930.KS", date(2024, 1, 1), date(2024, 2, 1))

    cache.fetch(source, "005930", "005930.KS", date(2023, 1, 1), date(2024, 2, 1))

    assert source.calls == 2


def test_empty_result_is_remembered_so_we_stop_asking(cache):
    """상장 전 구간은 봉이 없다. 기록을 안 남기면 매번 다시 물어보고
    매번 빈손으로 돌아온다 — 오늘 실제로 2종목이 그랬다."""
    source = CountingSource(pd.DataFrame(columns=["trade_date", "open", "high", "low", "close", "volume"]))

    cache.fetch(source, "440110", "440110.KQ", date(2022, 1, 1), date(2022, 12, 31))
    cache.fetch(source, "440110", "440110.KQ", date(2022, 1, 1), date(2022, 12, 31))

    assert source.calls == 1


def test_refetch_replaces_rather_than_mixes_old_and_new(cache):
    """야후가 과거 값을 고쳤을 때 옛 값과 새 값이 섞이면 어느 쪽이 쓰인 건지
    알 수 없게 된다."""
    start, end = date(2024, 1, 1), date(2024, 2, 1)
    original = frame(date(2024, 1, 2), 10)
    revised = original.copy()
    revised["close"] = revised["close"] + 50

    cache.put("005930", original, start, end)
    cache.put("005930", revised, start, end)

    stored = cache.get("005930", start, end)
    assert len(stored) == len(original), "행이 두 배로 늘면 안 된다"
    assert stored["close"].tolist() == revised["close"].tolist()


def test_summary_says_when_the_cache_was_not_used(cache):
    assert "사용 안 함" in cache.summary()
