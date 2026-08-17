"""KIS 모의투자 계좌로 실제 매매 파이프라인을 돌리는 스크립트.

KIS 서버(openapivts.koreainvestment.com:29443)에 접근 가능한 환경에서만
동작한다 — 비표준 포트라 egress 정책에 따라 막혀 있을 수 있다 (이 저장소를
개발한 환경은 실제로 막혀 있었다). 여기서 막히면 scripts/run_dry_run.py로
파이프라인 로직만 먼저 검증할 것.

전제 조건:
    python scripts/configure.py kis --env paper --app-key ... --app-secret ... \
        --account-no ... --account-product-cd 01
    python scripts/configure.py telegram --bot-token ... --chat-id ...

매일 장 마감 후 1회 실행하는 걸 전제로 한다 (cron/스케줄러로 등록).

사용 예:
    python scripts/run_paper_trading.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from muwon.config import bootstrap_settings
from muwon.data.kis_client import KISClient
from muwon.data.universe import UNIVERSE
from muwon.db.session import make_session_factory
from muwon.execution.engine import TradingEngine
from muwon.execution.kis_order_executor import KISOrderExecutor
from muwon.notify.telegram import TelegramNotifier
from muwon.risk.manager import RiskManager
from muwon.settings.service import build_settings_service
from muwon.strategy.registry import build_strategy


def main() -> None:
    settings_service = build_settings_service()
    creds = settings_service.get_kis_credentials()
    if creds.is_real:
        raise SystemExit(
            "kis.env가 'real'로 설정되어 있습니다. 이 스크립트는 모의투자 전용이니 "
            "python scripts/configure.py kis --env paper ...로 먼저 되돌리세요."
        )
    if not creds.app_key or not creds.app_secret or not creds.account_no:
        raise SystemExit("KIS 인증정보가 없습니다. python scripts/configure.py kis ...로 먼저 설정하세요.")

    client = KISClient.from_settings(settings_service)
    session_factory = make_session_factory(bootstrap_settings.database_url)
    strategy_key = settings_service.get_strategy_selection().active_key
    print(f"활성 전략: {strategy_key}", file=sys.stderr)

    engine = TradingEngine(
        strategy=build_strategy(strategy_key),
        risk_manager=RiskManager(policy_provider=settings_service.get_risk_policy),
        data_source=client,
        order_executor=KISOrderExecutor(client),
        notifier=TelegramNotifier(settings_service),
        session_factory=session_factory,
        universe=UNIVERSE,
        source_symbol=lambda ticker: ticker.symbol,
    )

    summary = engine.run_once()

    print(f"\n=== KIS 모의투자 실행 결과 ({summary.run_date}) ===")
    print(f"점검 종목 수: {summary.checked_symbols}")
    if not summary.actions:
        print("체결 없음")
    for action in summary.actions:
        side = "매수" if action.side.value == "buy" else "매도"
        print(f"{side}: {action.name}({action.symbol}) {action.quantity}주 @ {action.price:,.0f}원 — {action.reason}")
    if summary.rejections:
        print("\n리스크 매니저 거부:")
        for rejection in summary.rejections:
            print(f"  - {rejection}")


if __name__ == "__main__":
    main()
