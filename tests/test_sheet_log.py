"""기록을 시트에 쌓는 자리.

제일 중요한 시험은 **두 번 돌려도 두 줄이 되지 않는다**는 것이다. 워크플로
재실행은 정상적인 수단이고, 그때마다 줄이 늘면 시트를 세어 만든 숫자가
전부 틀린다."""

from dataclasses import dataclass
from datetime import UTC, date, datetime

from muwon.cloud.sheet_log import (
    MAX_CELL,
    append,
    daily_rows,
    forecast_rows,
    only_new,
    trade_rows,
    매매머리,
)


@dataclass
class 가짜매매:
    id: int = 1
    symbol: str = "005930"
    strategy_key: str = "volume_surge_5d"
    quantity: int = 10
    entry_price: float = 70000.0
    exit_price: float = 72000.0
    entry_reason: str = "거래량 급증"
    exit_reason: str = "보유기간 만료"
    pnl_amount: float = 20000.0
    pnl_pct: float = 2.86
    is_paper: bool = True
    entered_at: datetime = datetime(2026, 8, 10, 9, 5, tzinfo=UTC)
    exited_at: datetime = datetime(2026, 8, 14, 9, 5, tzinfo=UTC)


@dataclass
class 가짜전망:
    기준일: date = date(2026, 8, 19)
    대상: str = "반도체"
    지평: int = 20
    중앙값: float | None = 2.1
    상승확률: float | None = 62.0
    하위10: float | None = -11.4
    구간수: int = 34
    우연을_넘었나: bool = False

    @property
    def 낼수있나(self):
        return self.중앙값 is not None


def test_매매줄의_열쇠는_id에서_나온다():
    줄 = trade_rows([가짜매매(id=31)])[0]
    assert 줄[0] == "T31"
    assert 줄[2] == "005930"
    assert 줄[-1] == "모의"


def test_실거래와_모의를_구분해_적는다():
    """섞이면 나중에 슬리피지를 잴 때 모의 숫자를 실측으로 착각한다."""
    assert trade_rows([가짜매매(is_paper=False)])[0][-1] == "실거래"


def test_전망줄의_열쇠는_낸날_대상_지평():
    줄 = forecast_rows([가짜전망()])[0]
    assert 줄[0] == "F2026-08-19|반도체|20"
    assert 줄[-1] == ""  # 실제 결과는 지평이 지난 뒤에 채운다


def test_못낸_전망은_숫자칸을_비운다():
    """0으로 채우면 '0%로 전망했다'로 읽힌다 — 안 낸 것과 다르다."""
    줄 = forecast_rows([가짜전망(중앙값=None)])[0]
    assert 줄[4:9] == ["", "", "", "", ""]


def test_하루요약은_날짜가_열쇠라_두번_돌아도_한줄():
    줄들 = daily_rows(date(2026, 8, 19), 매수=2, 매도=1, 거부=3)
    assert 줄들[0][0] == "D2026-08-19"
    assert only_new({"D2026-08-19"}, 줄들) == []


def test_이미_있는_열쇠는_안_올린다():
    후보 = trade_rows([가짜매매(id=1), 가짜매매(id=2)])
    남은것 = only_new(["T1"], 후보)
    assert [줄[0] for 줄 in 남은것] == ["T2"]


def test_한번에_올리는_묶음_안의_중복도_거른다():
    후보 = trade_rows([가짜매매(id=7), 가짜매매(id=7)])
    assert len(only_new([], 후보)) == 1


def test_긴_이유는_잘라_넣는다():
    긴것 = "가" * 500
    줄 = trade_rows([가짜매매(exit_reason=긴것)])[0]
    assert len(줄[10]) == MAX_CELL
    assert 줄[10].endswith("…")


class 가짜시트:
    """구글 대신. 호출된 것을 기록만 한다."""

    def __init__(self, 탭들=(), 열쇠들=()):
        self.탭들 = list(탭들)
        self.열쇠들 = list(열쇠들)
        self.올린것 = []
        self.만든탭 = []

    def get(self, spreadsheetId):
        return _즉시({"sheets": [{"properties": {"title": t}} for t in self.탭들]})

    def batchUpdate(self, spreadsheetId, body):
        for 요청 in body["requests"]:
            제목 = 요청["addSheet"]["properties"]["title"]
            self.탭들.append(제목)
            self.만든탭.append(제목)
        return _즉시({})

    def values(self):
        return _값들(self)


class _값들:
    def __init__(self, 시트):
        self.시트 = 시트

    def get(self, spreadsheetId, range):
        return _즉시({"values": [[k] for k in self.시트.열쇠들]})

    def update(self, **kw):
        return _즉시({})

    def append(self, spreadsheetId, range, valueInputOption, insertDataOption, body):
        self.시트.올린것.extend(body["values"])
        return _즉시({})


class _즉시:
    def __init__(self, 값):
        self.값 = 값

    def execute(self):
        return self.값


def test_탭이_없으면_만들고_머리줄을_넣는다():
    시트 = 가짜시트(탭들=["섹터"])
    올린수 = append("id", "매매기록", 매매머리, trade_rows([가짜매매(id=1)]), svc=시트)
    assert 시트.만든탭 == ["매매기록"]
    assert 올린수 == 1


def test_재실행해도_같은_줄을_또_올리지_않는다():
    시트 = 가짜시트(탭들=["매매기록"], 열쇠들=["열쇠", "T1"])
    올린수 = append("id", "매매기록", 매매머리, trade_rows([가짜매매(id=1)]), svc=시트)
    assert 올린수 == 0
    assert 시트.올린것 == []


def test_새_줄만_올린다():
    시트 = 가짜시트(탭들=["매매기록"], 열쇠들=["열쇠", "T1"])
    올린수 = append(
        "id", "매매기록", 매매머리, trade_rows([가짜매매(id=1), 가짜매매(id=2)]), svc=시트
    )
    assert 올린수 == 1
    assert [줄[0] for 줄 in 시트.올린것] == ["T2"]


def test_올릴것이_없으면_구글에_붙지도_않는다():
    assert append("id", "매매기록", 매매머리, [], svc=None) == 0
