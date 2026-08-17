from dataclasses import dataclass


@dataclass(frozen=True)
class RiskPolicy:
    max_position_weight: float = 0.15
    stop_loss_pct: float = -0.05
    daily_loss_limit_pct: float = -0.03
    max_concurrent_positions: int = 8
    trading_enabled: bool = True  # 전체 킬스위치 — False면 신규 진입을 전부 거부


@dataclass(frozen=True)
class KISCredentials:
    kis_env: str = "paper"  # "paper" | "real"
    app_key: str = ""
    app_secret: str = ""
    account_no: str = ""
    account_product_cd: str = "01"

    @property
    def is_real(self) -> bool:
        return self.kis_env == "real"


@dataclass(frozen=True)
class TelegramConfig:
    bot_token: str = ""
    chat_id: str = ""


@dataclass(frozen=True)
class StrategySelection:
    """지금 실거래(run_paper_trading.py/run_realtime_trading.py)가 쓸
    전략을 가리키는 값. strategy/registry.py에 등록된 키여야 한다. 이걸
    바꾸는 건 곧 "가설을 실거래로 승격"하는 행위라서, 코드 배포 없이
    설정값 하나로 되고 변경 이력에도 자동으로 남는다."""

    active_key: str = "ma_rsi_v1"
