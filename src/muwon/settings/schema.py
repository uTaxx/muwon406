from dataclasses import dataclass


@dataclass(frozen=True)
class RiskPolicy:
    max_position_weight: float = 0.15
    stop_loss_pct: float = -0.05
    daily_loss_limit_pct: float = -0.03
    max_concurrent_positions: int = 8
    trading_enabled: bool = True  # 전체 킬스위치 — False면 신규 진입을 전부 거부

    # 변동성 기반 청산. 고정 %는 모든 종목에 같은 자를 들이대는데, 하루 1%
    # 움직이는 종목과 4% 움직이는 종목에 같은 -5%를 적용하면 후자는 이틀치
    # 잡음에 손절당한다. ATR(그 종목이 하루에 보통 움직이는 폭)의 배수로
    # 잡으면 종목 성격에 맞춰진다. 끄면 위의 고정 stop_loss_pct로 돌아간다.
    atr_stop_enabled: bool = False
    atr_stop_multiple: float = 2.0
    trailing_stop_enabled: bool = False
    trailing_stop_multiple: float = 3.0
    atr_window: int = 14


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
