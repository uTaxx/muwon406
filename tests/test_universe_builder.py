"""유니버스 자동 갱신 로직 검증.

핵심은 두 가지다: (1) 개별 종목 전략에 안 맞는 것(ETF·우선주·스팩)을
확실히 걸러내는가, (2) 갱신이 실패해도 매매가 멈추지 않는가."""

from unittest.mock import MagicMock

from muwon.data.universe import Ticker
from muwon.data.universe_builder import (
    active_universe,
    build_universe,
    diff_universe,
    is_tradable_stock,
    load_latest_universe,
    save_snapshot,
    to_ticker,
)
from muwon.db.session import make_session_factory


def test_accepts_ordinary_stocks():
    for name in ["삼성전자", "SK하이닉스", "NAVER", "에코프로비엠", "LG에너지솔루션"]:
        assert is_tradable_stock(name) is True, name


def test_rejects_etf_etn_spac_and_preferred_stocks():
    """개별 종목 전략(이동평균·RSI)의 전제가 안 맞거나, 추세 자체가 없는
    상품들 — 유니버스에 섞이면 신호가 오염된다."""
    rejected = [
        "KODEX 200",  # ETF
        "TIGER 미국나스닥100",
        "KBSTAR 200",
        "삼성 레버리지 WTI원유 ETN",
        "교보10호스팩",  # 스팩: 합병 전까지 가격이 거의 고정
        "삼성전자우",  # 우선주: 같은 회사 중복 + 거래량 적음
        "현대차2우B",
        "LG화학우",
    ]
    for name in rejected:
        assert is_tradable_stock(name) is False, name


def test_rejects_empty_name():
    assert is_tradable_stock("") is False


def test_to_ticker_assigns_market_specific_yahoo_suffix():
    """백테스트는 야후 티커를 쓰는데 코스피/코스닥 접미사가 다르다 —
    틀리면 그 종목만 조용히 시세가 안 잡힌다."""
    assert to_ticker("005930", "삼성전자", "KOSPI").yahoo_symbol == "005930.KS"
    assert to_ticker("247540", "에코프로비엠", "KOSDAQ").yahoo_symbol == "247540.KQ"


def make_client(kospi_rows, kosdaq_rows) -> MagicMock:
    client = MagicMock()

    def fake_ranking(market: str, limit: int):
        return {"kospi": kospi_rows, "kosdaq": kosdaq_rows}[market][:limit]

    client.get_top_market_cap.side_effect = lambda market, limit: fake_ranking(market, limit)
    return client


def test_build_universe_merges_both_markets_by_market_cap():
    """코스피만 조회하면 코스닥이 통째로 빠진다 — 두 시장을 각각 받아
    시가총액으로 합쳐야 한다."""
    client = make_client(
        kospi_rows=[("005930", "삼성전자", 5_000_000), ("000660", "SK하이닉스", 1_000_000)],
        kosdaq_rows=[("247540", "에코프로비엠", 2_000_000)],
    )

    universe = build_universe(client, size=3)

    assert [t.symbol for t in universe] == ["005930", "247540", "000660"]  # 시총 내림차순
    assert universe[1].market == "KOSDAQ"


def test_build_universe_filters_then_respects_size():
    """걸러낼 종목이 섞여 있어도 요청한 개수를 채워야 한다 — 그래서 넉넉히
    받아 온 뒤 거르는 순서가 중요하다."""
    client = make_client(
        kospi_rows=[
            ("069500", "KODEX 200", 9_000_000),  # 제외 대상
            ("005935", "삼성전자우", 8_000_000),  # 제외 대상
            ("005930", "삼성전자", 5_000_000),
            ("000660", "SK하이닉스", 1_000_000),
        ],
        kosdaq_rows=[],
    )

    universe = build_universe(client, size=2)

    assert [t.name for t in universe] == ["삼성전자", "SK하이닉스"]


def test_build_universe_deduplicates_symbols_across_markets():
    client = make_client(
        kospi_rows=[("005930", "삼성전자", 5_000_000)],
        kosdaq_rows=[("005930", "삼성전자", 5_000_000)],
    )
    universe = build_universe(client, size=5)
    assert len(universe) == 1


def test_snapshot_roundtrip_preserves_rank_order():
    session_factory = make_session_factory("sqlite:///:memory:")
    tickers = [
        to_ticker("005930", "삼성전자", "KOSPI"),
        to_ticker("247540", "에코프로비엠", "KOSDAQ"),
    ]

    save_snapshot(session_factory, tickers, {"005930": 5_000_000, "247540": 2_000_000})
    loaded = load_latest_universe(session_factory)

    assert [t.symbol for t in loaded] == ["005930", "247540"]
    assert loaded[1].yahoo_symbol == "247540.KQ"


def test_load_latest_returns_only_most_recent_snapshot():
    """스냅샷은 덮어쓰지 않고 쌓으므로, 매매에는 가장 최근 것만 써야 한다."""
    session_factory = make_session_factory("sqlite:///:memory:")
    save_snapshot(session_factory, [to_ticker("005930", "삼성전자", "KOSPI")], {})
    save_snapshot(
        session_factory,
        [to_ticker("000660", "SK하이닉스", "KOSPI"), to_ticker("035720", "카카오", "KOSPI")],
        {},
    )

    loaded = load_latest_universe(session_factory)
    assert [t.symbol for t in loaded] == ["000660", "035720"]


def test_active_universe_falls_back_when_no_snapshot():
    """갱신이 한 번도 안 됐거나 실패해도 매매가 멈추면 안 된다."""
    session_factory = make_session_factory("sqlite:///:memory:")
    fallback = [Ticker("005930", "삼성전자", "KOSPI", "005930.KS")]

    assert active_universe(session_factory, fallback) == fallback


def test_active_universe_prefers_snapshot_over_fallback():
    session_factory = make_session_factory("sqlite:///:memory:")
    save_snapshot(session_factory, [to_ticker("000660", "SK하이닉스", "KOSPI")], {})
    fallback = [Ticker("005930", "삼성전자", "KOSPI", "005930.KS")]

    assert [t.symbol for t in active_universe(session_factory, fallback)] == ["000660"]


def test_diff_reports_added_and_removed():
    """성과가 나빠졌을 때 전략 탓인지 종목이 바뀐 탓인지 구분하려면
    무엇이 들고 났는지 보여야 한다."""
    previous = [to_ticker("005930", "삼성전자", "KOSPI"), to_ticker("035720", "카카오", "KOSPI")]
    current = [to_ticker("005930", "삼성전자", "KOSPI"), to_ticker("000660", "SK하이닉스", "KOSPI")]

    added, removed = diff_universe(previous, current)

    assert added == ["SK하이닉스(000660)"]
    assert removed == ["카카오(035720)"]
