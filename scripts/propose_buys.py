"""오늘 살 만한 종목을 골라 **시트에 올리고 승인을 기다린다.**

**이 스크립트는 아무것도 사지 않는다.** 후보를 적어 두고 알릴 뿐이다.
실제 매수는 사람이 시트에서 체크한 뒤 다음 단계가 한다.

## 왜 이걸 먼저 만드나

모의투자를 꺼 둔 이유가 "완전 자동이 무섭다"였다. 그런데 안 켜면
**슬리피지(사겠다고 판단한 값과 실제로 사진 값의 차이) 실측 표본이 영영
안 생기고**, 지금 모든 백테스트 숫자가 "종가에 딱 체결됐다"는 가정 위에
있다.

승인 스텝이 그 사이를 잇는다. 그리고 이 스크립트만 며칠 돌려 보면
**아무 위험 없이** "이 전략이 하루에 몇 종목을, 어떤 이유로 고르는지"를
눈으로 볼 수 있다. 매수를 켜는 판단은 그다음이다.

## 무엇을 유니버스로 쓰나

**구글 시트의 섹터·종목 탭**이다. 지금까지 쓰던 시가총액 스냅샷이 아니라,
사람이 정한 섹터별 목록이다.

사용 예:
    python scripts/propose_buys.py --dry-run     # 화면에만
    python scripts/propose_buys.py               # 시트 + 텔레그램
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import requests

from muwon.cloud.approval import pending_rows, 승인머리, 알림글, 후보
from muwon.cloud.sector_sheet import DEFAULT_TITLE, find_or_create, read
from muwon.cloud.sheet_log import append
from muwon.config import bootstrap_settings
from muwon.data.price_cache import PriceCache
from muwon.data.yahoo_client import YahooFinanceDataSource
from muwon.db.session import ensure_schema, make_session_factory
from muwon.domain.types import SignalType
from muwon.settings.from_sheet import parse_settings
from muwon.settings.service import build_settings_service
from muwon.strategy.registry import build_strategies

KST = ZoneInfo("Asia/Seoul")
#: 지표 예열에 필요한 기간. 짧으면 이동평균이 안 나와 신호가 통째로 빈다.
WARMUP_DAYS = 400


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet-id", default=os.environ.get("MUWON_SHEET_ID", ""))
    parser.add_argument("--folder-id", default=os.environ.get("GDRIVE_FOLDER_ID", ""))
    parser.add_argument("--dry-run", action="store_true", help="시트·텔레그램에 안 보내고 화면에만")
    parser.add_argument("--max", type=int, default=0, help="후보를 몇 개까지 (0이면 설정의 동시보유 수)")
    args = parser.parse_args()

    sheet_id = args.sheet_id
    if not sheet_id:
        if not args.folder_id:
            raise SystemExit("MUWON_SHEET_ID도 GDRIVE_FOLDER_ID도 없습니다.")
        sheet_id, _ = find_or_create(args.folder_id, DEFAULT_TITLE)

    내용 = read(sheet_id)
    설정 = parse_settings(내용.설정)

    ensure_schema(bootstrap_settings.database_url)
    service = build_settings_service()
    selection = service.get_strategy_selection()
    strategy = build_strategies(selection.active_keys, selection.combine)
    print(f"■ 전략: {selection.describe()}", file=sys.stderr)

    # 지금 들고 있는 종목은 다시 사지 않는다.
    from sqlalchemy import select

    from muwon.db.models import PositionRow

    with make_session_factory(bootstrap_settings.database_url)() as session:
        보유중 = {p.symbol for p in session.scalars(select(PositionRow))}

    대상 = [
        (m.symbol, m.name, s.이름)
        for s in 내용.섹터
        if s.활성
        for m in s.활성종목
        if m.symbol not in 보유중
    ]
    print(f"■ 살펴볼 종목 {len(대상)}개 (보유 중 {len(보유중)}개 제외)", file=sys.stderr)

    source = YahooFinanceDataSource()
    cache = PriceCache()
    오늘 = datetime.now(KST).date()
    시작 = 오늘 - timedelta(days=WARMUP_DAYS)

    후보들, 못본것 = [], []
    for symbol, name, 섹터명 in 대상:
        야후 = f"{symbol}.KS" if _코스피인가(내용, symbol) else f"{symbol}.KQ"
        try:
            df = cache.fetch(source, symbol, 야후, 시작, 오늘)
        except (requests.RequestException, ValueError, KeyError) as e:
            못본것.append(f"{name}({symbol}): {type(e).__name__}")
            continue
        if df is None or len(df) < 60:
            못본것.append(f"{name}({symbol}): 시세 {0 if df is None else len(df)}일")
            continue

        # **마지막 봉의 신호만** 본다. generate_signals는 히스토리 전체의
        # 신호를 돌려주므로, 거르지 않으면 3년 전 신호로 오늘 산다.
        마지막날 = df["trade_date"].iloc[-1]
        살것 = [
            s for s in strategy.generate_signals(symbol, df)
            if s.trade_date == 마지막날 and s.signal_type == SignalType.BUY
        ]
        if not 살것:
            continue
        signal = max(살것, key=lambda s: s.score)

        가격 = float(df["close"].iloc[-1])
        후보들.append((signal.score, 후보(
            symbol=symbol, name=name, strategy=signal.strategy_name,
            quantity=0,  # 수량은 매수 단계에서 그때 현금으로 정한다
            price=가격, reason=f"[{섹터명}] {signal.reason}",
        )))

    # 점수가 높은 순으로 자른다. 동시에 들 수 있는 수보다 많이 제안하면
    # 사람이 다 체크했을 때 리스크 매니저가 뒤에서 거부한다 — 그러면
    # "승인했는데 왜 안 샀지"가 된다.
    상한 = args.max or _동시보유(설정, service)
    후보들.sort(key=lambda 것: 것[0], reverse=True)
    고른것 = [c for _, c in 후보들[:상한]]

    print(f"\n■ 매수 후보 {len(고른것)}종목 (신호 {len(후보들)}개 중 상위 {상한})")
    for c in 고른것:
        print(f"  {c.name}({c.symbol})  {c.price:>9,.0f}원   {c.reason}")
    if 못본것:
        print(f"\n  시세를 못 본 종목 {len(못본것)}개 — **이유가 있어야 다음에 무엇을 고칠지 안다**")
        for 줄 in 못본것:
            print(f"    · {줄}")

    if not 설정.승인필요:
        print("\n⚠️ 시트의 require_approval이 꺼져 있습니다 — 승인 없이 사도록 설정돼 있습니다.")

    if args.dry_run:
        print("\n(--dry-run이라 시트·텔레그램에 안 보냈습니다)")
        return 0

    올린수 = append(sheet_id, "승인대기", 승인머리, pending_rows(고른것, 오늘))
    주소 = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
    print(f"\n승인대기 탭에 {올린수}줄 올렸습니다 — {주소}")

    try:
        from muwon.notify.telegram import TelegramNotifier

        TelegramNotifier(service).send(알림글(고른것, 오늘, 주소))
        print("텔레그램으로 알렸습니다.", file=sys.stderr)
    except Exception as e:  # noqa: BLE001 — 알림 실패가 후보 목록을 지우면 안 된다
        print(f"텔레그램 전송 실패: {type(e).__name__}: {e}", file=sys.stderr)
    return 0


def _코스피인가(내용, symbol: str) -> bool:
    for s in 내용.섹터:
        for m in s.종목:
            if m.symbol == symbol:
                return m.market == "KOSPI"
    return True


def _동시보유(설정, service) -> int:
    값 = 설정.덮개.get("max_concurrent_positions")
    return int(값) if 값 else service.get_risk_policy().max_concurrent_positions


if __name__ == "__main__":
    raise SystemExit(main())
