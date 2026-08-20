"""매수 후보 밑에 붙는 **승인 / 거절 버튼.**

## 왜 버튼인가

지금은 `/승인 005930`을 손으로 쳐야 한다. 종목코드 여섯 자리를 폰에서
정확히 치는 일은 생각보다 귀찮고, **귀찮으면 안 하게 되고, 안 하면 승인
스텝이 없는 것과 같다.**

버튼은 한 번 누르면 끝이고, **무엇을 누르는지 이름으로 보인다** — 코드를
잘못 치면 엉뚱한 종목을 승인하지만 버튼은 그럴 수가 없다.

## 누른 뒤에 무엇이 남나

**거절을 빈 칸이 아니라 `N`으로 적는다.** 지금 규칙상 빈 칸도 안 사는
것이라 매매 결과는 같지만, 나중에 기록을 볼 때 **"안 봤다"와 "보고
거절했다"는 전혀 다른 이야기**다. 앞의 것은 알림이 안 갔거나 놓친 것이고,
뒤의 것은 판단이다. 구별해 두지 않으면 승인 스텝이 실제로 쓰이고 있는지
알 수가 없다.

## 눌러도 안 되는 것

버튼으로는 **오늘 제안된 종목의 승인/거절만** 된다. 매매를 켜거나 기준을
바꾸는 버튼은 만들지 않는다 — 폰 화면에서 손가락이 스치는 일이 실제로
일어나고, 그 결과가 '매매 켜짐'이면 안 된다.

## 64바이트

텔레그램은 버튼에 붙일 수 있는 자료를 **64바이트**로 제한한다. 그래서
`a|2026-08-20|005930`(19바이트)처럼 짧게 적는다. 종목명 같은 것을 넣으면
한글 몇 자에 넘어간다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

#: 버튼 하나에 붙는 자료의 최대 길이(텔레그램 제한).
MAX_CALLBACK_BYTES = 64
#: 버튼에 적을 종목명 길이. 길면 버튼이 두 줄로 접혀 목록이 안 읽힌다.
NAME_LEN = 9

승인, 거절, 전부승인, 전부거절 = "a", "r", "A", "R"


@dataclass(frozen=True)
class 버튼항목:
    """버튼 하나를 그리는 데 필요한 전부. 후보 전체를 끌고 다닐 필요가 없다."""

    symbol: str
    name: str


@dataclass(frozen=True)
class 누름:
    종류: str            # 승인 / 거절 / 전부승인 / 전부거절 / 모름
    날짜: date | None = None
    symbol: str = ""
    말: str = ""         # 못 알아들었을 때 돌려줄 말


def callback_data(종류: str, 날짜: date, symbol: str = "") -> str:
    값 = f"{종류}|{날짜.isoformat()}" + (f"|{symbol}" if symbol else "")
    if len(값.encode()) > MAX_CALLBACK_BYTES:
        raise ValueError(f"버튼 자료가 {MAX_CALLBACK_BYTES}바이트를 넘습니다: {값!r}")
    return 값


def parse_callback(값: str) -> 누름:
    """버튼에서 온 자료 → 무엇을 눌렀나. **네트워크도 상태도 없다.**"""
    조각 = (값 or "").split("|")
    종류 = 조각[0] if 조각 else ""
    if 종류 not in (승인, 거절, 전부승인, 전부거절):
        return 누름("모름", 말="모르는 버튼입니다. 새로 온 후보 목록에서 눌러 주세요.")
    if len(조각) < 2:
        return 누름("모름", 말="날짜가 없는 버튼입니다.")
    try:
        날 = date.fromisoformat(조각[1])
    except ValueError:
        return 누름("모름", 말="날짜를 못 읽었습니다.")

    if 종류 in (전부승인, 전부거절):
        return 누름("전부승인" if 종류 == 전부승인 else "전부거절", 날짜=날)

    if len(조각) < 3 or not (조각[2].isdigit() and len(조각[2]) == 6):
        return 누름("모름", 말="종목코드가 이상한 버튼입니다.")
    return 누름("승인" if 종류 == 승인 else "거절", 날짜=날, symbol=조각[2])


def keyboard(후보들, 날짜: date, 결정: dict[str, str] | None = None) -> dict:
    """후보 목록 → 버튼 판. `결정`을 주면 이미 누른 것이 표시된다.

    누를 때마다 이 판을 다시 만들어 갈아 끼운다 — **화면이 지금 상태를
    보여 주지 않으면 방금 누른 게 먹었는지 알 수가 없다.**"""
    결정 = 결정 or {}
    줄들 = []
    for c in 후보들:
        d = 결정.get(c.symbol, "")
        이름 = c.name if len(c.name) <= NAME_LEN else c.name[: NAME_LEN - 1] + "…"
        승인칸 = f"☑️ {이름} 승인함" if d == "Y" else f"✅ {이름}"
        거절칸 = "🚫 거절함" if d == "N" else "❌"
        줄들.append([
            {"text": 승인칸, "callback_data": callback_data(승인, 날짜, c.symbol)},
            {"text": 거절칸, "callback_data": callback_data(거절, 날짜, c.symbol)},
        ])
    if len(후보들) > 1:
        줄들.append([
            {"text": "✅ 전부 승인", "callback_data": callback_data(전부승인, 날짜)},
            {"text": "❌ 전부 거절", "callback_data": callback_data(전부거절, 날짜)},
        ])
    return {"inline_keyboard": 줄들}


#: 상태 블록의 시작 표시. 다시 그릴 때 여기서부터 잘라 낸다.
상태표시 = "──────────"


def 상태블록(후보들, 결정: dict[str, str] | None = None) -> str:
    """지금 무엇이 승인이고 무엇이 거절인지 **글로도 적는다.**

    버튼 글자만 바꾸면 나중에 대화를 훑을 때 무슨 일이 있었는지 안 보인다.
    버튼은 지금 누르는 것이고, 이 블록은 **남는 기록**이다.

    아직 안 정한 것을 따로 세는 이유는, 0이 되어야 다 본 것이기 때문이다 —
    승인 1건이라는 말만으로는 나머지를 봤는지 알 수 없다."""
    결정 = 결정 or {}
    승인된것 = [c.name for c in 후보들 if 결정.get(c.symbol) == "Y"]
    거절된것 = [c.name for c in 후보들 if 결정.get(c.symbol) == "N"]
    아직 = [c.name for c in 후보들 if c.symbol not in 결정]

    줄 = [상태표시, "지금 상태"]
    줄.append(f"  ✅ 승인 {len(승인된것)}종목" + (f" — {', '.join(승인된것)}" if 승인된것 else ""))
    줄.append(f"  ❌ 거절 {len(거절된것)}종목" + (f" — {', '.join(거절된것)}" if 거절된것 else ""))
    if 아직:
        줄.append(f"  ⬜ 아직 안 정함 {len(아직)}종목 — {', '.join(아직)}")
    else:
        줄.append("  ⬜ 아직 안 정함 없음 — 다 보셨습니다")
    if 승인된것:
        줄.append("")
        줄.append("승인한 것은 다음 매수 때 삽니다. 그 전까지는 다시 눌러 되돌릴 수 있습니다.")
    return "\n".join(줄)


def 글에_상태붙이기(원래글: str, 후보들, 결정: dict[str, str] | None = None) -> str:
    """이미 보낸 글에 상태 블록을 갈아 끼운다.

    앞선 상태 블록을 잘라 내고 새로 붙인다 — 안 자르면 누를 때마다 글이
    길어져서 정작 후보 목록이 화면 밖으로 밀려난다."""
    몸통 = (원래글 or "").split(상태표시)[0].rstrip()
    return 몸통 + "\n\n" + 상태블록(후보들, 결정)


def 누른뒤말(누름값: 누름, 이름: str = "") -> str:
    """버튼을 누르면 화면 위에 잠깐 뜨는 한 줄. **짧아야 읽힌다.**"""
    if 누름값.종류 == "승인":
        return f"{이름 or 누름값.symbol} 승인"
    if 누름값.종류 == "거절":
        return f"{이름 or 누름값.symbol} 거절"
    if 누름값.종류 == "전부승인":
        return "전부 승인"
    if 누름값.종류 == "전부거절":
        return "전부 거절"
    return 누름값.말
