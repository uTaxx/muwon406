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
