"""승인 매매가 무엇을 살펴볼지.

**여기서 보유 종목이 빠지면 손절이 조용히 멈춘다.** 화면에는 '체결 없음'
으로만 보이고, 그 사실은 값이 더 빠진 뒤에야 드러난다. 그래서 시험이
대부분 그 한 가지를 본다."""

from dataclasses import dataclass

from muwon.execution.approved_universe import build_universe, to_ticker


@dataclass
class 가짜종목:
    symbol: str
    name: str
    market: str


@dataclass
class 가짜섹터:
    종목: list


섹터들 = [
    가짜섹터([가짜종목("005930", "삼성전자", "KOSPI"), 가짜종목("403870", "HPSP", "KOSDAQ")]),
]


def test_승인된것과_보유중인것을_모두_본다():
    티커, 가정 = build_universe(["005930"], {"403870"}, 섹터들)
    assert [t.symbol for t in 티커] == ["005930", "403870"]
    assert 가정 == []


def test_승인이_하나도_없어도_보유는_본다():
    """이게 빠지면 아무것도 승인 안 한 날 손절이 통째로 멈춘다."""
    티커, _ = build_universe([], {"403870"}, 섹터들)
    assert [t.symbol for t in 티커] == ["403870"]


def test_보유가_없으면_승인된것만():
    티커, _ = build_universe(["005930"], set(), 섹터들)
    assert [t.symbol for t in 티커] == ["005930"]


def test_승인과_보유가_겹쳐도_한_번만():
    티커, _ = build_universe(["005930"], {"005930"}, 섹터들)
    assert [t.symbol for t in 티커] == ["005930"]


def test_코스닥에는_KQ를_붙인다():
    """코스닥에 .KS를 붙이면 시세가 통째로 비고, 그 종목은 조용히 빠진다."""
    t, 어디 = to_ticker("403870", 섹터들)
    assert t.yahoo_symbol == "403870.KQ"
    assert 어디 == "시트"


def test_코스피에는_KS를_붙인다():
    assert to_ticker("005930", 섹터들)[0].yahoo_symbol == "005930.KS"


def test_시트에_없으면_기본목록에서_찾는다():
    t, 어디 = to_ticker("000660", [])
    assert t.name == "SK하이닉스" and 어디 == "기본목록"


def test_아무데도_없으면_가정하고_알린다():
    """조용히 코스피로 가정하면 코스닥 종목의 시세가 빈 채로 넘어간다."""
    티커, 가정 = build_universe(["999999"], set(), [])
    assert 가정 == ["999999"]
    assert 티커[0].market == "KOSPI"


def test_이름을_알면_붙여_준다():
    티커, _ = build_universe(["999999"], set(), [], {"999999": "어떤회사"})
    assert 티커[0].name == "어떤회사"


def test_승인된것이_보유보다_앞에_온다():
    티커, _ = build_universe(["005930"], {"000660", "403870"}, 섹터들)
    assert 티커[0].symbol == "005930"
