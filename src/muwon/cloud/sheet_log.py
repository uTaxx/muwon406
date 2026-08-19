"""매매·전망·하루 요약을 구글 시트에 쌓는다 — **덧붙이기만 한다.**

`docs/설계_스트림릿을_걷어낼까.md`의 **3단계**다. 2단계에서 시트가 설정의
원본이 됐고, 여기서 **기록도 시트에서 볼 수 있게** 한다. 그러면 대시보드를
켜지 않고도 "어제 뭘 샀고 지금 뭘 들고 있나"를 폰에서 본다.

## 방향이 반대다 — 설정과 헷갈리지 말 것

| | 원본 | 코드는 |
|---|---|---|
| `섹터`·`종목`·`설정` 탭 | **사람** | 읽기만 |
| `매매기록`·`전망기록`·`일일요약` 탭 | **코드** | 쓰기만 |

한 탭을 양쪽이 고치면 충돌 처리를 만들어야 한다. 그래서 탭마다 주인을
하나로 못 박았다.

## 덧붙이기만 하고 지우지 않는다

지난 줄을 고치지 않는다. **기록을 고칠 수 있으면 기록이 아니다** — 나중에
"그때 왜 샀지"를 볼 때 믿을 수 있어야 한다. 잘못 들어간 줄이 있으면 지우지
말고 다음 줄에 정정을 남긴다.

## 두 번 돌아도 두 줄이 되지 않는다

워크플로는 재실행되고, 재실행은 실패를 고치는 정상적인 수단이다. 그런데
그때마다 같은 매매가 한 줄씩 늘면 **시트를 세어 만든 숫자가 전부 틀린다.**

그래서 줄마다 맨 앞에 **열쇠**를 붙이고, 올리기 전에 시트에 이미 있는
열쇠를 읽어 **없는 것만** 올린다. 열쇠는 DB의 표와 id를 붙인 값이라
(`T31`, `F2026-08-19|반도체|20`) 같은 것이 두 번 만들어지지 않는다.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import date, datetime

매매머리 = ["열쇠", "청산일", "종목", "전략", "수량", "산값", "판값",
            "손익금액", "손익%", "산이유", "판이유", "모의"]
전망머리 = ["열쇠", "낸날", "대상", "지평", "중앙값%", "상승확률%",
            "아주나빴을때%", "구간수", "우연넘음", "실제%"]
요약머리 = ["열쇠", "날짜", "매수", "매도", "거부", "평가액", "현금", "메모"]

#: 시트 한 셀은 5만 자까지지만, 그만큼 긴 이유는 읽지도 못한다.
MAX_CELL = 200


def _자르기(글: object) -> str:
    """긴 글은 잘라 넣는다. 시트에서 한 줄이 화면을 다 먹으면 표가 아니다."""
    s = "" if 글 is None else str(글)
    return s if len(s) <= MAX_CELL else s[: MAX_CELL - 1] + "…"


def _날짜(값: object) -> str:
    if isinstance(값, datetime):
        return 값.strftime("%Y-%m-%d %H:%M")
    if isinstance(값, date):
        return 값.isoformat()
    return _자르기(값)


def trade_rows(trades: Iterable) -> list[list[str]]:
    """완결된 매매(TradeRow) → 시트 줄. **네트워크 없이 시험한다.**"""
    줄들 = []
    for t in trades:
        줄들.append([
            f"T{t.id}",
            _날짜(t.exited_at),
            _자르기(t.symbol),
            _자르기(t.strategy_key),
            str(t.quantity),
            f"{t.entry_price:.0f}",
            f"{t.exit_price:.0f}",
            f"{t.pnl_amount:.0f}",
            f"{t.pnl_pct:.2f}",
            _자르기(t.entry_reason),
            _자르기(t.exit_reason),
            "모의" if t.is_paper else "실거래",
        ])
    return 줄들


def forecast_rows(전망들: Iterable) -> list[list[str]]:
    """낸 전망 → 시트 줄.

    열쇠에 id를 못 쓴다 — 전망 기록은 나중에 실제 결과가 채워지면서 같은
    줄이 바뀌기 때문이다. 그래서 (낸날·대상·지평)을 열쇠로 쓴다. 하루에
    같은 대상·지평 전망을 두 번 내지 않으므로 이걸로 충분하다."""
    줄들 = []
    for f in 전망들:
        낼수있나 = getattr(f, "낼수있나", True)
        줄들.append([
            f"F{_날짜(f.기준일)}|{f.대상}|{f.지평}",
            _날짜(f.기준일),
            _자르기(f.대상),
            str(f.지평),
            f"{f.중앙값:.1f}" if 낼수있나 else "",
            f"{f.상승확률:.0f}" if 낼수있나 else "",
            f"{f.하위10:.1f}" if 낼수있나 else "",
            str(getattr(f, "구간수", "")) if 낼수있나 else "",
            ("Y" if getattr(f, "우연을_넘었나", False) else "N") if 낼수있나 else "",
            "",  # 실제 결과는 지평이 지난 뒤에 채운다
        ])
    return 줄들


def daily_rows(
    날짜: date, 매수: int, 매도: int, 거부: int,
    평가액: float | None = None, 현금: float | None = None, 메모: str = "",
) -> list[list[str]]:
    """하루 한 줄. 열쇠가 날짜라서 **같은 날 두 번 돌려도 한 줄이다.**"""
    return [[
        f"D{날짜.isoformat()}",
        날짜.isoformat(),
        str(매수), str(매도), str(거부),
        f"{평가액:.0f}" if 평가액 is not None else "",
        f"{현금:.0f}" if 현금 is not None else "",
        _자르기(메모),
    ]]


def only_new(있는열쇠: Iterable[str], 후보: Sequence[Sequence[str]]) -> list[list[str]]:
    """시트에 없는 줄만. **재실행이 줄을 늘리지 않게 하는 자리.**

    후보 안에서도 열쇠가 겹치면 첫 줄만 남긴다 — 한 번에 올리는 묶음
    안에서도 중복이 생길 수 있다."""
    본것 = set(있는열쇠)
    결과 = []
    for 줄 in 후보:
        열쇠 = str(줄[0])
        if 열쇠 in 본것:
            continue
        본것.add(열쇠)
        결과.append(list(줄))
    return 결과


# ── 여기부터는 구글에 붙는다 ────────────────────────────────────────


def _service():  # pragma: no cover — 실제 호출은 시험하지 않는다
    from googleapiclient.discovery import build

    from muwon.cloud.sector_sheet import _credentials

    return build("sheets", "v4", credentials=_credentials())


def append(sheet_id: str, 탭: str, 머리: Sequence[str], 줄들: Sequence[Sequence[str]],
           svc=None) -> int:
    """탭이 없으면 만들고, 이미 있는 열쇠는 빼고 덧붙인다. 올린 줄 수를 돌려준다."""
    if not 줄들:
        return 0
    svc = svc or _service().spreadsheets()

    있는탭 = {s["properties"]["title"] for s in svc.get(spreadsheetId=sheet_id).execute()["sheets"]}
    if 탭 not in 있는탭:
        svc.batchUpdate(
            spreadsheetId=sheet_id,
            body={"requests": [{"addSheet": {"properties": {"title": 탭}}}]},
        ).execute()
        svc.values().update(
            spreadsheetId=sheet_id, range=f"{탭}!A1",
            valueInputOption="RAW", body={"values": [list(머리)]},
        ).execute()
        있는열쇠: list[str] = []
    else:
        칸 = svc.values().get(spreadsheetId=sheet_id, range=f"{탭}!A1:A100000").execute()
        있는열쇠 = [줄[0] for 줄 in 칸.get("values", []) if 줄]

    올릴것 = only_new(있는열쇠, 줄들)
    if not 올릴것:
        return 0
    svc.values().append(
        spreadsheetId=sheet_id, range=f"{탭}!A1",
        valueInputOption="RAW", insertDataOption="INSERT_ROWS",
        body={"values": 올릴것},
    ).execute()
    return len(올릴것)
