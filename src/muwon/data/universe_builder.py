"""시가총액 상위 종목으로 매매 대상 목록(유니버스)을 다시 뽑는다.

data/universe.py의 UNIVERSE는 사람이 골라 고정해 둔 18종목이라 시간이
지나면 낡는다 — 상장폐지되거나, 순위가 뒤집히거나, 새로 커진 종목이
빠져 있게 된다. 여기서는 KIS 시가총액 순위 API로 현재 상위 종목을 받아
매매에 부적절한 것들을 걸러낸 유니버스를 만든다.

덮어쓰지 않고 스냅샷으로 쌓는 이유: 어느 날 성과가 나빠졌을 때 그게 전략
탓인지 종목이 바뀐 탓인지 구분하려면, 그날 무엇을 대상으로 삼았는지가
남아 있어야 한다.
"""

from __future__ import annotations

import re
from datetime import datetime

from loguru import logger
from sqlalchemy import select

from muwon.data.universe import Ticker
from muwon.db.models import UniverseSnapshotRow

# ETF·ETN은 주식이 아니라 바스켓 상품이라 개별 종목 전략(이동평균·RSI 등)의
# 전제가 맞지 않고, 스팩은 합병 전까지 가격이 거의 고정이라 추세가 없다.
# 시총 순위 API가 이들을 섞어 줄 수 있어 이름으로 한 번 더 걸러낸다.
_ETF_BRAND_PATTERN = re.compile(
    r"(KODEX|TIGER|KBSTAR|ARIRANG|HANARO|KOSEF|SOL |ACE |PLUS |RISE |TIMEFOLIO|"
    r"마이다스|파워|마이티|WOORI|히어로즈|BNK|VITA|UNICORN|에셋플러스)"
)
_ETN_PATTERN = re.compile(r"(ETN|선물|레버리지|인버스|\dX)")
_SPAC_PATTERN = re.compile(r"스팩")
# 우선주는 보통 이름이 "…우", "…우B", "…3우B"로 끝난다. API에서 보통주만
# 요청하지만(fid_div_cls_code=1), 응답이 섞여 오는 경우를 대비한 이중 방어다.
_PREFERRED_PATTERN = re.compile(r"(\d?우[B]?)$")


def is_tradable_stock(name: str) -> bool:
    """개별 종목 전략의 대상으로 적절한 보통주인지."""
    if not name:
        return False
    return not (
        _ETF_BRAND_PATTERN.search(name)
        or _ETN_PATTERN.search(name)
        or _SPAC_PATTERN.search(name)
        or _PREFERRED_PATTERN.search(name)
    )


def to_ticker(symbol: str, name: str, market: str) -> Ticker:
    """백테스트용 야후 티커까지 붙인 Ticker를 만든다 (코스피 .KS / 코스닥 .KQ)."""
    suffix = ".KQ" if market == "KOSDAQ" else ".KS"
    return Ticker(symbol=symbol, name=name, market=market, yahoo_symbol=f"{symbol}{suffix}")


# 코스닥에 할당할 비율. 시가총액만으로 줄을 세우면 코스닥은 한 종목도 못
# 남는다 — 실제로 상위 30을 뽑았더니 전부 코스피였고, 기존 유니버스에 있던
# 에코프로비엠·에코프로가 빠졌다. 단타는 변동성이 큰 코스닥에서 기회가
# 나오는 경우가 많아 통째로 빠지면 전략 자체가 좁아지므로, 시장별로 자리를
# 따로 할당한다.
DEFAULT_KOSDAQ_RATIO = 0.3


def build_universe(
    client, size: int = 30, kosdaq_ratio: float = DEFAULT_KOSDAQ_RATIO
) -> list[Ticker]:
    """코스피·코스닥 시총 상위에서 매매 대상 종목을 골라 온다.

    두 시장을 하나로 합쳐 시가총액순으로 자르지 않고 **시장별로 자리를
    나눠 각각 상위를 뽑는다**. 합쳐서 자르면 코스피 대형주가 자리를 전부
    차지해 코스닥이 0종목이 되기 때문이다(실측으로 확인).

    kosdaq_ratio=0.3, size=30이면 코스피 21 + 코스닥 9종목이 된다.
    한쪽 시장에서 조건에 맞는 종목이 모자라면 다른 쪽에서 채운다."""
    if not 0.0 <= kosdaq_ratio <= 1.0:
        raise ValueError(f"kosdaq_ratio는 0~1 사이여야 합니다: {kosdaq_ratio}")

    quotas = {
        "KOSDAQ": round(size * kosdaq_ratio),
        "KOSPI": size - round(size * kosdaq_ratio),
    }

    picked: dict[str, list[Ticker]] = {}
    leftovers: list[tuple[str, str, str, int]] = []  # 할당량을 넘어 남은 후보

    for market_key, market_name in (("kospi", "KOSPI"), ("kosdaq", "KOSDAQ")):
        # 걸러낼 종목(ETF·우선주 등)을 감안해 넉넉히 받아 온다
        rows = client.get_top_market_cap(market=market_key, limit=size * 2)
        logger.info(f"{market_name} 시총 상위 {len(rows)}종목 수신")

        tradable = [(s, n, market_name, c) for s, n, c in rows if is_tradable_stock(n)]
        quota = quotas[market_name]
        picked[market_name] = [to_ticker(s, n, m) for s, n, m, _c in tradable[:quota]]
        leftovers.extend(tradable[quota:])

    universe: list[Ticker] = []
    seen: set[str] = set()
    for market_name in ("KOSPI", "KOSDAQ"):
        for ticker in picked.get(market_name, []):
            if ticker.symbol not in seen:
                seen.add(ticker.symbol)
                universe.append(ticker)

    # 한쪽 시장이 할당량을 못 채웠으면 남은 후보 중 시총 큰 순으로 채운다
    if len(universe) < size:
        leftovers.sort(key=lambda row: row[3], reverse=True)
        for symbol, name, market, _cap in leftovers:
            if len(universe) >= size:
                break
            if symbol not in seen:
                seen.add(symbol)
                universe.append(to_ticker(symbol, name, market))

    return universe[:size]


def save_snapshot(session_factory, tickers: list[Ticker], market_caps: dict[str, int]) -> datetime:
    """유니버스 스냅샷을 저장하고 그 시각을 돌려준다."""
    snapshot_at = datetime.utcnow()  # noqa: DTZ003 — 기록용, tz 무관
    with session_factory() as session:
        for rank, ticker in enumerate(tickers, start=1):
            session.add(
                UniverseSnapshotRow(
                    snapshot_at=snapshot_at,
                    symbol=ticker.symbol,
                    name=ticker.name,
                    market=ticker.market,
                    market_cap=market_caps.get(ticker.symbol, 0),
                    rank=rank,
                )
            )
        session.commit()
    return snapshot_at


def load_latest_universe(session_factory) -> list[Ticker]:
    """가장 최근 스냅샷의 유니버스를 돌려준다. 스냅샷이 없으면 빈 목록."""
    with session_factory() as session:
        latest_at = session.scalar(select(UniverseSnapshotRow.snapshot_at).order_by(
            UniverseSnapshotRow.snapshot_at.desc()
        ))
        if latest_at is None:
            return []
        rows = session.scalars(
            select(UniverseSnapshotRow)
            .where(UniverseSnapshotRow.snapshot_at == latest_at)
            .order_by(UniverseSnapshotRow.rank)
        ).all()
        return [to_ticker(r.symbol, r.name, r.market) for r in rows]


def active_universe(session_factory, fallback: list[Ticker]) -> list[Ticker]:
    """실제 매매에 쓸 유니버스 — 스냅샷이 있으면 그걸, 없으면 fallback을 쓴다.

    갱신이 한 번도 안 됐거나 실패한 상태에서 매매가 멈추면 안 되므로,
    손으로 고른 기존 목록을 안전망으로 남겨 둔다."""
    latest = load_latest_universe(session_factory)
    if latest:
        return latest
    logger.info("저장된 유니버스 스냅샷이 없어 기본 목록을 사용합니다.")
    return fallback


def diff_universe(previous: list[Ticker], current: list[Ticker]) -> tuple[list[str], list[str]]:
    """이전/현재 유니버스의 차이를 (편입, 제외) 종목명 목록으로 돌려준다."""
    prev_symbols = {t.symbol: t.name for t in previous}
    cur_symbols = {t.symbol: t.name for t in current}
    added = [f"{name}({sym})" for sym, name in cur_symbols.items() if sym not in prev_symbols]
    removed = [f"{name}({sym})" for sym, name in prev_symbols.items() if sym not in cur_symbols]
    return added, removed
