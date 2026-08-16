from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    kis_env: str = "paper"  # "paper" | "real"
    kis_app_key: str = ""
    kis_app_secret: str = ""
    kis_account_no: str = ""
    kis_account_product_cd: str = "01"

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    database_url: str = "sqlite:///./muwon.db"

    # 리스크 관리 기본값 (docs/risk_policy.md 참고, 함께 조정 가능)
    max_position_weight: float = 0.15
    stop_loss_pct: float = -0.05
    daily_loss_limit_pct: float = -0.03
    max_concurrent_positions: int = 8

    @property
    def is_real_trading(self) -> bool:
        return self.kis_env == "real"


settings = Settings()
