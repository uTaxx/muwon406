"""임시 설정 CLI — 대시보드(Phase 2+)가 만들어지기 전까지 KIS/텔레그램/
리스크 설정을 DB(app_settings 테이블)에 채워 넣는 도구.

대시보드가 생기면 이 CLI가 호출하는 것과 동일한 SettingsService를 그대로
사용하므로, 저장되는 위치나 형식은 바뀌지 않는다.

사용 예:
    python scripts/configure.py kis --env paper --app-key XXX --app-secret YYY \
        --account-no 12345678 --account-product-cd 01
    python scripts/configure.py telegram --bot-token XXX --chat-id YYY
    python scripts/configure.py risk --max-position-weight 0.15 \
        --stop-loss-pct -0.05 --daily-loss-limit-pct -0.03 \
        --max-concurrent-positions 8
    python scripts/configure.py show
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from muwon.settings.schema import KISCredentials, RiskPolicy, TelegramConfig  # noqa: E402
from muwon.settings.service import build_settings_service  # noqa: E402


def _mask(value: str) -> str:
    if not value:
        return "(미설정)"
    return value[:2] + "*" * max(len(value) - 2, 0)


def main() -> None:
    parser = argparse.ArgumentParser(description="muwon406 설정 관리 CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    kis = sub.add_parser("kis", help="KIS 인증정보 설정")
    kis.add_argument("--env", choices=["paper", "real"], required=True)
    kis.add_argument("--app-key", required=True)
    kis.add_argument("--app-secret", required=True)
    kis.add_argument("--account-no", required=True)
    kis.add_argument("--account-product-cd", default="01")

    telegram = sub.add_parser("telegram", help="텔레그램 알림 설정")
    telegram.add_argument("--bot-token", required=True)
    telegram.add_argument("--chat-id", required=True)

    risk = sub.add_parser("risk", help="리스크 정책 설정")
    risk.add_argument("--max-position-weight", type=float, required=True)
    risk.add_argument("--stop-loss-pct", type=float, required=True)
    risk.add_argument("--daily-loss-limit-pct", type=float, required=True)
    risk.add_argument("--max-concurrent-positions", type=int, required=True)

    sub.add_parser("show", help="현재 설정 조회 (비밀값은 마스킹)")

    args = parser.parse_args()
    service = build_settings_service()

    if args.command == "kis":
        service.set_kis_credentials(
            KISCredentials(
                kis_env=args.env,
                app_key=args.app_key,
                app_secret=args.app_secret,
                account_no=args.account_no,
                account_product_cd=args.account_product_cd,
            )
        )
        print("KIS 인증정보 저장 완료")
    elif args.command == "telegram":
        service.set_telegram_config(
            TelegramConfig(bot_token=args.bot_token, chat_id=args.chat_id)
        )
        print("텔레그램 설정 저장 완료")
    elif args.command == "risk":
        service.set_risk_policy(
            RiskPolicy(
                max_position_weight=args.max_position_weight,
                stop_loss_pct=args.stop_loss_pct,
                daily_loss_limit_pct=args.daily_loss_limit_pct,
                max_concurrent_positions=args.max_concurrent_positions,
            )
        )
        print("리스크 정책 저장 완료")
    elif args.command == "show":
        creds = service.get_kis_credentials()
        telegram_cfg = service.get_telegram_config()
        risk_policy = service.get_risk_policy()
        print(
            f"KIS: env={creds.kis_env} app_key={_mask(creds.app_key)} "
            f"app_secret={_mask(creds.app_secret)} account_no={_mask(creds.account_no)}"
        )
        print(
            f"Telegram: chat_id={telegram_cfg.chat_id or '(미설정)'} "
            f"bot_token={_mask(telegram_cfg.bot_token)}"
        )
        print(f"Risk: {risk_policy}")


if __name__ == "__main__":
    main()
