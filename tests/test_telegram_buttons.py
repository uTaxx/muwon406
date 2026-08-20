"""승인 / 거절 버튼.

버튼은 코드를 손으로 치는 것보다 안전하다 — 오타로 엉뚱한 종목을 승인할
수가 없다. 대신 **손가락이 스치는 일**이 실제로 일어나므로, 눌러서 될 수
있는 일의 범위를 좁게 잡았는지가 시험의 초점이다."""

from datetime import date

import pytest

from muwon.notify.telegram_buttons import (
    MAX_CALLBACK_BYTES,
    callback_data,
    keyboard,
    parse_callback,
    누른뒤말,
)

오늘 = date(2026, 8, 20)


class 가짜후보:
    def __init__(self, symbol, name):
        self.symbol, self.name = symbol, name


후보들 = [가짜후보("005930", "삼성전자"), 가짜후보("000660", "SK하이닉스")]


def test_승인_버튼을_알아본다():
    c = parse_callback("a|2026-08-20|005930")
    assert c.종류 == "승인" and c.symbol == "005930" and c.날짜 == 오늘


def test_거절_버튼을_알아본다():
    assert parse_callback("r|2026-08-20|005930").종류 == "거절"


def test_전부_버튼에는_종목이_없다():
    c = parse_callback("A|2026-08-20")
    assert c.종류 == "전부승인" and c.symbol == ""
    assert parse_callback("R|2026-08-20").종류 == "전부거절"


def test_모르는_버튼은_추측하지_않는다():
    for 값 in ("", "x|2026-08-20|005930", "a", "a|어제|005930", "a|2026-08-20|12", None):
        assert parse_callback(값).종류 == "모름", f"{값!r}가 명령으로 읽혔습니다"


def test_버튼_자료가_64바이트를_넘지_않는다():
    """텔레그램 제한이다 — 넘으면 버튼이 통째로 안 만들어진다."""
    for 값 in (callback_data("a", 오늘, "005930"), callback_data("A", 오늘)):
        assert len(값.encode()) <= MAX_CALLBACK_BYTES


def test_종목명이_길어도_버튼_자료는_안_길어진다():
    """버튼 자료에는 이름이 안 들어간다 — 한글 몇 자면 64바이트를 넘는다."""
    판 = keyboard([가짜후보("005930", "아주아주긴이름의회사입니다주식회사")], 오늘)
    for 줄 in 판["inline_keyboard"]:
        for 칸 in 줄:
            assert len(칸["callback_data"].encode()) <= MAX_CALLBACK_BYTES


def test_긴_이름은_버튼_글자만_줄인다():
    판 = keyboard([가짜후보("005930", "아주아주긴이름의회사입니다")], 오늘)
    글 = 판["inline_keyboard"][0][0]["text"]
    assert "…" in 글


def test_후보마다_승인과_거절이_한_줄로():
    판 = keyboard(후보들, 오늘)
    assert len(판["inline_keyboard"][0]) == 2
    assert "삼성전자" in 판["inline_keyboard"][0][0]["text"]


def test_후보가_둘_이상이면_전부_버튼이_붙는다():
    판 = keyboard(후보들, 오늘)
    끝줄 = 판["inline_keyboard"][-1]
    assert [칸["text"] for 끝줄칸 in [끝줄] for 칸 in 끝줄칸] == ["✅ 전부 승인", "❌ 전부 거절"]


def test_후보가_하나면_전부_버튼을_안_붙인다():
    """하나뿐인데 '전부'가 나오면 무슨 뜻인지 헷갈린다."""
    판 = keyboard([후보들[0]], 오늘)
    assert len(판["inline_keyboard"]) == 1


def test_이미_누른_것이_버튼에_보인다():
    """방금 누른 게 먹었는지 화면에서 보이지 않으면 또 누르게 된다."""
    판 = keyboard(후보들, 오늘, {"005930": "Y", "000660": "N"})
    assert "승인함" in 판["inline_keyboard"][0][0]["text"]
    assert "거절함" in 판["inline_keyboard"][1][1]["text"]


def test_누른뒤말은_짧다():
    """화면 위에 잠깐 뜨는 한 줄이라 길면 안 읽힌다."""
    말 = 누른뒤말(parse_callback("a|2026-08-20|005930"), "삼성전자")
    assert 말 == "삼성전자 승인"
    assert len(누른뒤말(parse_callback("A|2026-08-20"))) < 20


def test_이름을_모르면_코드로_말한다():
    assert 누른뒤말(parse_callback("r|2026-08-20|005930")) == "005930 거절"


def test_너무_긴_자료는_만들_때_터진다():
    """조용히 잘려 나가면 엉뚱한 종목이 승인된다."""
    with pytest.raises(ValueError, match="64바이트"):
        callback_data("a", 오늘, "0" * 100)


def test_버튼_판을_다시_그리면_결정이_반영된다():
    """누를 때마다 판을 갈아 끼운다 — 화면이 지금 상태를 보여 줘야 한다."""
    from muwon.notify.telegram_buttons import 버튼항목

    후보 = [버튼항목("005930", "삼성전자"), 버튼항목("000660", "SK하이닉스")]
    처음 = keyboard(후보, 오늘)
    나중 = keyboard(후보, 오늘, {"005930": "Y"})
    assert 처음["inline_keyboard"][0][0]["text"] != 나중["inline_keyboard"][0][0]["text"]
    # 누르는 자료는 그대로다 — 다시 눌러 되돌릴 수 있어야 한다
    assert 처음["inline_keyboard"][0][0]["callback_data"] == 나중["inline_keyboard"][0][0]["callback_data"]


def test_되돌릴_수_있다():
    """잘못 눌렀을 때 반대 버튼으로 고칠 수 있어야 한다 — 승인은 되돌릴 수
    없는 일이 아니다(아직 사기 전이므로)."""
    from muwon.notify.telegram_buttons import 버튼항목

    판 = keyboard([버튼항목("005930", "삼성전자")], 오늘, {"005930": "Y"})
    거절칸 = 판["inline_keyboard"][0][1]
    assert parse_callback(거절칸["callback_data"]).종류 == "거절"
