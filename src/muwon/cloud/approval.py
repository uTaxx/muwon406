"""매수 전에 사람이 체크해야 산다 — 승인 대기열.

`docs/설계_스트림릿을_걷어낼까.md`의 **5단계**이고, LX MI 시스템에서
가장 값나갔던 부분(사람 승인 스텝)을 이쪽에 옮긴 것이다.

## 왜 필요한가

모의투자를 꺼 둔 이유가 "완전 자동이 무섭다"였다. 그런데 켜지 않으면
**슬리피지(사겠다고 판단한 값과 실제로 사진 값의 차이) 실측 표본이 영영
안 생긴다.** 지금 이 저장소의 모든 백테스트 숫자가 "종가에 딱 체결됐다"는
가정 위에 있고, 그 가정을 검증할 방법이 그것뿐이다.

승인 스텝이 그 사이를 잇는다. 자동으로 고르되 **사람이 체크한 것만 산다.**

## 왜 텔레그램 버튼이 아니라 시트인가

텔레그램 버튼을 받으려면 봇이 응답을 받는 자리(웹훅이나 폴링)가 있어야
하고, 그건 상시 도는 서버다. **시트 체크박스는 그게 없어도 된다** — 사람이
시트에서 체크하고, 다음 워크플로가 읽는다. 텔레그램은 "체크하러 오세요"를
알리는 데만 쓴다.

## 세 가지 규칙 — 전부 '안 사는 쪽'으로 틀린다

**① 빈 칸은 승인이 아니다.** 체크 안 한 것, 지운 것, 오타 전부 거부다.
`종목` 탭에서는 빈 칸이 '켜짐'이지만 여기서는 반대다. 사는 쪽으로 기우는
기본값을 두면 안 된다.

**② 어제 승인은 오늘 못 쓴다.** 후보를 낸 날짜와 주문 내는 날짜가 다르면
무시한다. 어제 좋아 보이던 종목이 오늘 20% 올라 있을 수 있다.

**③ 목록에 없는 줄은 무시한다.** 사람이 시트에 손으로 종목을 적어 넣어도
사지 않는다. 승인은 "제안된 것 중에 고르는" 행위지 "새로 주문하는" 행위가
아니다. 새로 사고 싶으면 증권사 앱에서 사는 것이 맞다.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date

승인머리 = ["열쇠", "날짜", "종목코드", "종목명", "섹터", "전략", "수량", "예상가",
            "승인", "이유"]

#: 명시적으로 이 중 하나여야 승인이다. 빈 칸·오타는 전부 거부다.
승인표시 = ("Y", "YES", "TRUE", "1", "O", "OK", "승인", "예", "V", "✓", "☑")


@dataclass(frozen=True)
class 후보:
    symbol: str
    name: str
    strategy: str
    quantity: int
    price: float
    reason: str = ""
    #: 어느 섹터에서 나왔나. 한 섹터에 몰리는 것을 막는 데 쓴다.
    sector: str = ""
    sector_name: str = ""


@dataclass(frozen=True)
class 승인결과:
    """읽어서 판단이 끝난 상태. **왜 안 샀는지가 왜 샀는지만큼 중요하다.**"""

    승인된것: tuple[str, ...]
    거부된것: tuple[str, ...]
    지난날것: tuple[str, ...]
    목록밖: tuple[str, ...]

    def 요약(self) -> str:
        줄 = [f"승인 {len(self.승인된것)}종목 · 미승인 {len(self.거부된것)}종목"]
        if self.지난날것:
            줄.append(f"  지난 날짜라 무시 {len(self.지난날것)}건 — 어제 승인은 오늘 못 씁니다")
        if self.목록밖:
            줄.append(
                f"  ⚠️ 제안한 적 없는 종목 {len(self.목록밖)}건을 무시했습니다: "
                f"{', '.join(self.목록밖)}"
            )
        return "\n".join(줄)


def 열쇠(날짜: date, symbol: str) -> str:
    return f"A{날짜.isoformat()}|{symbol}"


def pending_rows(후보들: Iterable[후보], 날짜: date) -> list[list[str]]:
    """오늘의 후보 → 시트에 올릴 줄. **승인 칸은 비워서 올린다.**

    미리 체크해 두면 '기본값이 산다'가 되고, 그건 승인 스텝이 없는 것과
    같다."""
    return [
        [
            열쇠(날짜, c.symbol),
            날짜.isoformat(),
            c.symbol,
            c.name,
            c.sector_name or c.sector,
            c.strategy,
            str(c.quantity),
            f"{c.price:.0f}",
            "",  # ← 사람이 여기에 체크한다
            c.reason,
        ]
        for c in 후보들
    ]


def parse_approvals(
    줄들: Sequence[Sequence[str]], 날짜: date, 제안한것: Iterable[str]
) -> 승인결과:
    """시트에서 읽은 줄 → 오늘 살 종목.

    **네트워크 없이 시험할 수 있게 따로 뺐다.** 규칙이 이 함수의 전부다."""
    제안 = set(제안한것)
    승인, 거부, 지난날, 목록밖 = [], [], [], []

    for 줄 in 줄들[1:]:  # 머리줄 건너뜀
        칸 = (list(줄) + [""] * len(승인머리))[: len(승인머리)]
        if not str(칸[0]).strip():
            continue
        적힌날 = str(칸[1]).strip()
        symbol = str(칸[2]).strip()
        체크됨 = str(칸[8]).strip().upper() in 승인표시

        if not 체크됨:
            거부.append(symbol)
            continue
        if 적힌날 != 날짜.isoformat():
            지난날.append(symbol)
            continue
        if symbol not in 제안:
            목록밖.append(symbol)
            continue
        승인.append(symbol)

    return 승인결과(
        승인된것=tuple(dict.fromkeys(승인)),
        거부된것=tuple(dict.fromkeys(거부)),
        지난날것=tuple(dict.fromkeys(지난날)),
        목록밖=tuple(dict.fromkeys(목록밖)),
    )


def 알림글(후보들: Sequence[후보], 날짜: date, 주소: str) -> str:
    """텔레그램으로 보낼 글. **버튼이 아니라 '보러 오세요'다.**"""
    if not 후보들:
        return f"📋 {날짜.isoformat()} 매수 후보 없음 — 오늘은 승인할 것이 없습니다."
    줄 = [f"📋 {날짜.isoformat()} 매수 후보 {len(후보들)}종목 — **승인 칸에 Y를 적은 것만 삽니다**", ""]
    for c in 후보들:
        섹터 = f"[{c.sector_name or c.sector}] " if (c.sector_name or c.sector) else ""
        수량 = f"{c.quantity}주 " if c.quantity else ""
        줄.append(f"  {섹터}{c.name}({c.symbol}) {수량}@ {c.price:,.0f}원")
        if c.reason:
            줄.append(f"     {c.reason}")
    줄 += [
        "",
        f"시트: {주소}",
        "",
        "빈 칸은 '안 산다'입니다. 아무것도 안 하시면 아무것도 안 삽니다.",
    ]
    return "\n".join(줄)
