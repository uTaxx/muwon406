"""증권사에만 있는 보유 종목을 우리 기록으로 들일 때의 판단.

`scripts/adopt_holdings.py`가 쓴다. 여기 규칙이 틀리면 **엔진이 실제와 다른
보유 상태 위에서 손절을 건다** — 없는 종목을 팔려 하거나, 있는 종목을
안 지킨다. 그래서 스크립트에 묻어 두지 않고 꺼내서 테스트로 고정한다.

규칙은 셋이다.

1. **증권사에 있고 우리에겐 없는 것** → 들인다. 수량·평균매입가는 증권사
   값을 그대로 쓴다. 우리 쪽에 주문 기록이 없으니 증권사가 유일한 사실이다.
2. **양쪽에 다 있는데 수량이 다른 것** → 건드리지 않고 알리기만 한다.
   부분 체결일 수도, 우리 버그일 수도 있어서 자동으로 덮으면 그것대로 사고다.
3. **우리에겐 있는데 증권사엔 없는 것** → 여기서 다루지 않는다. 그건 이미
   팔린 것을 우리가 못 지운 경우라 지우는 판단이고, 들이는 것과 반대다.
   계좌 대조가 잡아서 알린다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from muwon.db.models import PositionRow
from muwon.domain.types import Holding

#: 들인 종목의 전략 이름. 우리가 산 게 아니니 어느 가설의 성적으로도 잡히면
#: 안 된다 — `trades`를 전략별로 볼 때 이게 섞이면 판단이 오염된다.
ADOPTED = "adopted"

ENTRY_REASON = "증권사 잔고에서 들임 — 우리 주문 기록 없음"


@dataclass(frozen=True)
class 수량다름:
    symbol: str
    name: str
    db_quantity: int
    account_quantity: int


@dataclass(frozen=True)
class 들이기계획:
    들일것: list[PositionRow]
    수량다른것: list[수량다름]
    #: 들일 종목의 표시용 이름 — PositionRow에는 이름 자리가 없다.
    이름표: dict[str, str]

    @property
    def 할일있나(self) -> bool:
        return bool(self.들일것)


def plan(
    holdings: list[Holding], db_positions: dict[str, PositionRow], 진입일: date
) -> 들이기계획:
    """증권사 보유 목록과 우리 기록을 견줘 무엇을 들일지 정한다.

    진입일은 우리가 줘야 한다 — 잔고조회는 언제 샀는지를 안 알려주는데
    보유일수 청산이 그 날짜를 센다."""
    들일것, 수량다른것, 이름표 = [], [], {}

    for h in holdings:
        db = db_positions.get(h.symbol)
        if db is None:
            이름표[h.symbol] = h.name
            들일것.append(
                PositionRow(
                    symbol=h.symbol,
                    quantity=h.quantity,
                    entry_price=h.avg_buy_price,
                    entry_date=진입일,
                    entry_reason=ENTRY_REASON,
                    strategy_key=ADOPTED,
                )
            )
        elif db.quantity != h.quantity:
            수량다른것.append(
                수량다름(
                    symbol=h.symbol,
                    name=h.name,
                    db_quantity=db.quantity,
                    account_quantity=h.quantity,
                )
            )

    return 들이기계획(들일것=들일것, 수량다른것=수량다른것, 이름표=이름표)


def 맞출평가금(현금: float, holdings: list[Holding]) -> float:
    """들인 뒤의 기준평가금 — 현금 + 증권사 보유 전부의 평가금액.

    일일 손실한도가 "오늘 얼마나 잃었나"를 이 기준점에서 잰다. 안 맞추면
    종목을 들이는 순간 그만큼 손실이 난 것처럼 보여서, 아무 일도 안 했는데
    한도에 걸려 매매가 멈출 수 있다."""
    return 현금 + sum(h.quantity * h.current_price for h in holdings)
