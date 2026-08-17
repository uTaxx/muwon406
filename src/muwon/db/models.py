from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class AppSettingRow(Base):
    """KIS 인증정보/텔레그램/리스크 정책 등, 재시작 없이 바꿀 수 있어야 하는
    설정값 저장소. muwon.settings.store.SettingsStore가 이 테이블을 통해
    읽고 쓴다 — CLI와 (Phase 2+) 대시보드가 공유하는 단일 소스."""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AppSettingHistoryRow(Base):
    """AppSettingRow 값이 바뀔 때마다 이전/이후 값을 남기는 append-only 로그.
    대시보드의 '변경 이력' 탭이 이 테이블을 읽는다. 비밀값은 원문(is_secret=True
    이면 암호문)이 그대로 저장되므로, 조회 시 AppSettingRow와 같은 마스터키로
    복호화해야 한다."""

    __tablename__ = "app_settings_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), index=True)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str] = mapped_column(Text, default="")
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class PriceBarRow(Base):
    __tablename__ = "price_bars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(10), index=True)
    trade_date: Mapped[date] = mapped_column(Date, index=True)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[int] = mapped_column(Integer)


class SignalRow(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(10), index=True)
    trade_date: Mapped[date] = mapped_column(Date, index=True)
    strategy_name: Mapped[str] = mapped_column(String(50))
    signal_type: Mapped[str] = mapped_column(String(10))
    score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class OrderRow(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(10), index=True)
    side: Mapped[str] = mapped_column(String(4))
    quantity: Mapped[int] = mapped_column(Integer)
    price: Mapped[float] = mapped_column(Float)
    is_paper: Mapped[bool] = mapped_column(default=True)
    kis_order_id: Mapped[str] = mapped_column(String(50), default="")
    reason: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class EngineStateRow(Base):
    """TradingEngine이 회차 사이에 이어가야 하는 내부 상태(가상 현금,
    당일 시작 평가금액 등). 사용자가 만지는 app_settings와는 다른
    성격이라 별도 테이블로 둔다."""

    __tablename__ = "engine_state"

    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")


class PositionRow(Base):
    """실거래/모의투자 엔진(TradingEngine)이 회차마다 새로 뜨지 않고도 보유
    종목을 이어서 추적할 수 있도록 남기는 상태. 백테스트의 OpenPosition과
    같은 정보를 갖지만, 여긴 프로세스 재시작에도 살아남아야 해서 DB에 둔다."""

    __tablename__ = "positions"

    symbol: Mapped[str] = mapped_column(String(10), primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer)
    entry_price: Mapped[float] = mapped_column(Float)
    entry_date: Mapped[date] = mapped_column(Date)
    entered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    entry_reason: Mapped[str] = mapped_column(String(100), default="")
    strategy_key: Mapped[str] = mapped_column(String(50), default="")


class TradeRow(Base):
    """진입~청산이 하나로 묶인 '완결된 매매' 기록 — OrderRow는 체결 하나하나를
    남기지만(매수/매도가 서로 안 엮여 있음), 이건 손익까지 계산된 라운드트립
    이라 "이 전략/가설이 실전에서 어떻게 됐는지"를 바로 분석할 수 있다.
    사람이든, 나중에 붙을 AI 제언 로직이든, 전략을 고치자는 판단은 결국 이
    테이블을 근거로 한다 — 그래서 strategy_key를 반드시 채워서 가설별로
    묶어 볼 수 있게 한다."""

    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(10), index=True)
    strategy_key: Mapped[str] = mapped_column(String(50), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    entry_price: Mapped[float] = mapped_column(Float)
    exit_price: Mapped[float] = mapped_column(Float)
    entry_reason: Mapped[str] = mapped_column(String(100), default="")
    exit_reason: Mapped[str] = mapped_column(String(100), default="")
    pnl_amount: Mapped[float] = mapped_column(Float)
    pnl_pct: Mapped[float] = mapped_column(Float)
    is_paper: Mapped[bool] = mapped_column(Boolean, default=True)
    entered_at: Mapped[datetime] = mapped_column(DateTime)
    exited_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class BacktestRunRow(Base):
    """가설 스윕(scripts/run_hypothesis_sweep.py)이 남기는 백테스트 실행
    기록. 콘솔에 찍고 끝나면 다음 실행과 비교할 방법이 없어서, 같은 스키마로
    누적 저장해 시간이 지나도(파라미터를 바꿔가며 여러 번 돌려도) 가설별
    성과를 추적할 수 있게 한다."""

    __tablename__ = "backtest_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_key: Mapped[str] = mapped_column(String(50), index=True)
    params_json: Mapped[str] = mapped_column(Text, default="")  # 재현 가능하도록 실제 파라미터 스냅샷
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    total_return_pct: Mapped[float] = mapped_column(Float)
    max_drawdown_pct: Mapped[float] = mapped_column(Float)
    win_rate_pct: Mapped[float] = mapped_column(Float)
    num_trades: Mapped[int] = mapped_column(Integer)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
