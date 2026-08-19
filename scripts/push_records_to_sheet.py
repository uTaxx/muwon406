"""매매 기록과 하루 요약을 구글 시트에 덧붙인다.

`docs/설계_스트림릿을_걷어낼까.md`의 **3단계**. 대시보드를 켜지 않고도
폰에서 "어제 뭘 샀고 어떻게 됐나"를 보게 하는 것이 목적이다.

## 덧붙이기만 한다

지난 줄을 고치지 않는다. 줄마다 열쇠가 있어서 **여러 번 돌려도 줄이
늘지 않는다** — 워크플로 재실행은 실패를 고치는 정상적인 수단이고,
그때마다 줄이 늘면 시트를 세어 만든 숫자가 전부 틀린다.

## 아무것도 사지 않는다

읽어서 올리기만 한다.

사용 예:
    python scripts/push_records_to_sheet.py
    python scripts/push_records_to_sheet.py --days 30
    python scripts/push_records_to_sheet.py --dry-run   # 올릴 것만 보여 준다
"""

import argparse
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sqlalchemy import select

from muwon.cloud.sector_sheet import DEFAULT_TITLE, find_or_create
from muwon.cloud.sheet_log import (
    append,
    daily_rows,
    trade_rows,
    매매머리,
    요약머리,
)
from muwon.config import bootstrap_settings
from muwon.db.models import OrderRow, TradeRow
from muwon.db.session import ensure_schema, make_session_factory


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=90, help="최근 며칠치를 올릴 것인가")
    parser.add_argument("--sheet-id", default=os.environ.get("MUWON_SHEET_ID", ""))
    parser.add_argument("--folder-id", default=os.environ.get("GDRIVE_FOLDER_ID", ""))
    parser.add_argument("--dry-run", action="store_true", help="구글에 붙지 않고 올릴 것만 보여 준다")
    args = parser.parse_args()

    ensure_schema(bootstrap_settings.database_url)
    session_factory = make_session_factory(bootstrap_settings.database_url)
    오늘 = datetime.now(ZoneInfo("Asia/Seoul")).date()
    자른날 = 오늘 - timedelta(days=args.days)

    with session_factory() as session:
        매매들 = list(
            session.scalars(
                select(TradeRow).where(TradeRow.exited_at >= 자른날).order_by(TradeRow.id)
            )
        )
        주문들 = list(
            session.scalars(
                select(OrderRow).where(OrderRow.created_at >= 자른날).order_by(OrderRow.id)
            )
        )

    매매줄 = trade_rows(매매들)

    # 하루 요약은 주문에서 센다. 매매(TradeRow)는 청산돼야 생기므로,
    # 산 날에는 아무것도 안 남아 "그날 아무 일도 없었다"로 보인다.
    날짜별: dict[date, list[OrderRow]] = {}
    for o in 주문들:
        날짜별.setdefault(o.created_at.date(), []).append(o)
    요약줄 = []
    for 날, 것들 in sorted(날짜별.items()):
        요약줄 += daily_rows(
            날,
            매수=sum(1 for o in 것들 if o.side == "buy"),
            매도=sum(1 for o in 것들 if o.side == "sell"),
            거부=0,  # 거부는 주문으로 안 남는다 — 로그에만 있다
            메모="주문 기록에서 셈",
        )

    print(f"■ 최근 {args.days}일 — 완결된 매매 {len(매매줄)}건 · 주문이 있던 날 {len(요약줄)}일")
    if not 매매줄 and not 요약줄:
        print("\n올릴 것이 없습니다. **실거래 주문이 0건이라 그렇습니다** — "
              "모의투자를 켜야 여기에 줄이 쌓입니다.")

    if args.dry_run:
        for 줄 in (매매줄 + 요약줄)[:20]:
            print("  " + " | ".join(줄))
        return 0

    sheet_id = args.sheet_id
    if not sheet_id:
        if not args.folder_id:
            raise SystemExit("MUWON_SHEET_ID도 GDRIVE_FOLDER_ID도 없습니다.")
        sheet_id, _ = find_or_create(args.folder_id, DEFAULT_TITLE)
    print(f"시트: https://docs.google.com/spreadsheets/d/{sheet_id}")

    올린매매 = append(sheet_id, "매매기록", 매매머리, 매매줄)
    올린요약 = append(sheet_id, "일일요약", 요약머리, 요약줄)
    print(f"\n올림 — 매매기록 {올린매매}줄 · 일일요약 {올린요약}줄")
    if 매매줄 and not 올린매매:
        print("  (이미 있는 줄이라 안 올렸습니다 — 여러 번 돌려도 줄이 늘지 않습니다)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
