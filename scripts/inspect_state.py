"""운영 DB에 무엇이 들어 있는지 그대로 찍는다 — 읽기 전용.

"자동매매가 정말 돌고 있나"를 확인할 방법이 없었다. 대시보드가 비어 있어도
'아직 안 샀다'인지 '기록이 저장되지 못했다'인지 구분이 안 된다. 둘은 고치는
방법이 전혀 다르다.

아무것도 쓰지 않는다. 구글드라이브에 다시 올리지도 않는다 — 확인하려고
돌린 것이 운영 상태를 바꾸면 안 된다.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sqlalchemy import func, select

from muwon.config import bootstrap_settings
from muwon.db.models import (
    AppSettingRow,
    BacktestRunRow,
    EngineStateRow,
    OrderRow,
    PositionRow,
    SignalRow,
    TradeRow,
    UniverseSnapshotRow,
)
from muwon.db.session import make_session_factory


def main() -> None:
    path = bootstrap_settings.database_url
    print(f"■ 운영 DB 점검 — {path}")
    print(f"  조회 시각 {datetime.now(UTC).isoformat(timespec='seconds')}\n")

    session_factory = make_session_factory(path)
    with session_factory() as session:
        counts = {
            "신호(signals)": session.scalar(select(func.count()).select_from(SignalRow)),
            "주문(orders)": session.scalar(select(func.count()).select_from(OrderRow)),
            "보유(positions)": session.scalar(select(func.count()).select_from(PositionRow)),
            "완결매매(trades)": session.scalar(select(func.count()).select_from(TradeRow)),
            "백테스트(backtest_runs)": session.scalar(
                select(func.count()).select_from(BacktestRunRow)
            ),
            "유니버스 스냅샷": session.scalar(
                select(func.count()).select_from(UniverseSnapshotRow)
            ),
            "설정(app_settings)": session.scalar(
                select(func.count()).select_from(AppSettingRow)
            ),
        }
        for name, value in counts.items():
            print(f"  {name:<24} {value:>6}건")

        print("\n■ 엔진 상태 (회차 사이에 이어지는 값)")
        states = session.scalars(select(EngineStateRow)).all()
        if not states:
            print("  비어 있음 — 실거래 엔진이 한 번도 상태를 저장한 적이 없다는 뜻이다.")
        for row in states:
            print(f"  {row.key:<20} {row.value}")

        print("\n■ 최근 신호 10건")
        signals = session.scalars(
            select(SignalRow).order_by(SignalRow.created_at.desc()).limit(10)
        ).all()
        if not signals:
            print("  없음")
        for s in signals:
            print(
                f"  {s.trade_date} {s.symbol} {s.signal_type:<4} "
                f"{s.strategy_name:<22} 점수 {s.score:.1f}"
            )

        print("\n■ 최근 주문 10건")
        orders = session.scalars(
            select(OrderRow).order_by(OrderRow.created_at.desc()).limit(10)
        ).all()
        if not orders:
            print("  없음")
        for o in orders:
            ref = f"{o.reference_price:,.0f}" if o.reference_price else "—"
            confirmed = {True: "체결확인", False: "미확인", None: "(옛기록)"}[o.fill_confirmed]
            print(
                f"  {o.created_at:%Y-%m-%d %H:%M} {o.symbol} {o.side:<4} "
                f"{o.quantity}주 체결 {o.price:,.0f} / 기준 {ref} [{confirmed}]"
            )

        print("\n■ 최근 유니버스 스냅샷")
        latest = session.scalars(
            select(UniverseSnapshotRow)
            .order_by(UniverseSnapshotRow.snapshot_at.desc())
            .limit(3)
        ).all()
        if not latest:
            print("  없음 — 기본 18종목으로 매매하고 있다는 뜻이다.")
        for row in latest:
            print(f"  {row.snapshot_at:%Y-%m-%d %H:%M} kind={row.kind} {row.symbol} {row.name}")


if __name__ == "__main__":
    main()
