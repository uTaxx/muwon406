"""승인 대기열 — **틀리면 안 사야 할 것을 산다.**

여기 시험은 전부 "안 사는 쪽으로 틀리는가"를 확인한다."""

from datetime import date

from muwon.cloud.approval import (
    parse_approvals,
    pending_rows,
    승인머리,
    알림글,
    후보,
)

오늘 = date(2026, 8, 19)
어제 = date(2026, 8, 18)

후보들 = [
    후보("005930", "삼성전자", "volume_surge_5d", 10, 70000, "거래량 급증",
         sector="SEMI", sector_name="반도체"),
    후보("000660", "SK하이닉스", "volume_surge_5d", 3, 200000, "거래량 급증",
         sector="SEMI", sector_name="반도체"),
]


def 시트(*줄들):
    return [승인머리, *줄들]


def test_후보는_승인칸을_비운채_올라간다():
    """미리 체크해 두면 '기본값이 산다'가 되고, 그건 승인이 없는 것과 같다."""
    줄들 = pending_rows(후보들, 오늘)
    assert all(줄[8] == "" for 줄 in 줄들)
    assert 줄들[0][0] == "A2026-08-19|005930"


def test_체크한것만_산다():
    결과 = parse_approvals(
        시트(
            ["A2026-08-19|005930", "2026-08-19", "005930", "삼성전자", "반도체", "s", "10", "70000", "Y", ""],
            ["A2026-08-19|000660", "2026-08-19", "000660", "하이닉스", "반도체", "s", "3", "200000", "", ""],
        ),
        오늘,
        ["005930", "000660"],
    )
    assert 결과.승인된것 == ("005930",)
    assert 결과.거부된것 == ("000660",)


def test_빈칸과_오타는_전부_거부다():
    for 값 in ("", " ", "N", "아마도", "?", "0"):
        결과 = parse_approvals(
            시트(["A2026-08-19|005930", "2026-08-19", "005930", "삼성", "반도체", "s", "1", "1", 값, ""]),
            오늘,
            ["005930"],
        )
        assert 결과.승인된것 == (), f"{값!r}이 승인으로 읽혔습니다"


def test_어제_승인은_오늘_못쓴다():
    """어제 좋아 보이던 종목이 오늘 20% 올라 있을 수 있다."""
    결과 = parse_approvals(
        시트(["A2026-08-18|005930", "2026-08-18", "005930", "삼성", "반도체", "s", "1", "1", "Y", ""]),
        오늘,
        ["005930"],
    )
    assert 결과.승인된것 == ()
    assert 결과.지난날것 == ("005930",)


def test_제안한적_없는_종목은_안_산다():
    """사람이 손으로 적어 넣어도 사지 않는다 — 승인은 고르는 행위지 주문이 아니다."""
    결과 = parse_approvals(
        시트(["A2026-08-19|123456", "2026-08-19", "123456", "손으로적음", "", "", "99", "1", "Y", ""]),
        오늘,
        ["005930"],
    )
    assert 결과.승인된것 == ()
    assert 결과.목록밖 == ("123456",)
    assert "제안한 적 없는" in 결과.요약()


def test_체크표시_여러_모양을_받는다():
    for 값 in ("Y", "y", "O", "승인", "TRUE", "1", "✓"):
        결과 = parse_approvals(
            시트(["A2026-08-19|005930", "2026-08-19", "005930", "삼성", "반도체", "s", "1", "1", 값, ""]),
            오늘,
            ["005930"],
        )
        assert 결과.승인된것 == ("005930",), f"{값!r}이 승인으로 안 읽혔습니다"


def test_빈_시트는_아무것도_안_산다():
    결과 = parse_approvals(시트(), 오늘, ["005930"])
    assert 결과.승인된것 == ()


def test_알림글은_아무것도_안하면_안산다고_말한다():
    글 = 알림글(후보들, 오늘, "https://example.com")
    assert "삼성전자(005930)" in 글
    assert "아무것도 안 삽니다" in 글


def test_후보가_없으면_그렇게_말한다():
    assert "후보 없음" in 알림글([], 오늘, "https://example.com")


def test_섹터가_시트에_적힌다():
    """왜 샀는지를 나중에 볼 때 '어느 섹터에서 나왔나'가 첫 물음이다."""
    줄 = pending_rows(후보들, 오늘)[0]
    assert 줄[4] == "반도체"


class 가짜값들:
    def __init__(self, 줄들):
        self.줄들 = 줄들
        self.고친것 = []

    def get(self, spreadsheetId, range):
        return _즉시({"values": self.줄들})

    def update(self, spreadsheetId, range, valueInputOption, body):
        self.고친것.append((range, body["values"][0][0]))
        return _즉시({})


class 가짜svc:
    def __init__(self, 값들):
        self._값들 = 값들

    def values(self):
        return self._값들


class _즉시:
    def __init__(self, 값):
        self.값 = 값

    def execute(self):
        return self.값


def test_텔레그램_승인은_오늘_줄에만_Y를_적는다():
    from muwon.cloud.approval import approve_in_sheet, 승인머리

    값들 = 가짜값들([
        승인머리,
        ["A2026-08-18|005930", "2026-08-18", "005930", "삼성", "반도체", "s", "1", "1", "", ""],
        ["A2026-08-19|005930", "2026-08-19", "005930", "삼성", "반도체", "s", "1", "1", "", ""],
    ])
    찾음, 못찾음 = approve_in_sheet("id", 오늘, ["005930"], svc=가짜svc(값들))
    assert 찾음 == ["005930"] and 못찾음 == []
    assert 값들.고친것 == [("승인대기!I3", "Y")]   # 어제 줄(2행)은 안 건드린다


def test_후보에_없는_종목을_승인하면_그렇다고_말한다():
    """승인했다고 믿는 종목이 실제로는 후보에 없었으면 말해 줘야 한다."""
    from muwon.cloud.approval import approve_in_sheet, 승인머리

    값들 = 가짜값들([승인머리])
    찾음, 못찾음 = approve_in_sheet("id", 오늘, ["005930"], svc=가짜svc(값들))
    assert 찾음 == [] and 못찾음 == ["005930"]
