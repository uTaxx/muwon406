import pytest

from muwon.db.session import make_session_factory
from muwon.settings.crypto import generate_master_key
from muwon.settings.schema import (
    KISCredentials,
    RiskPolicy,
    StrategySelection,
    TelegramConfig,
)
from muwon.settings.service import SettingsService
from muwon.settings.store import SettingsStore


def make_service(master_key: str | None = None) -> SettingsService:
    session_factory = make_session_factory("sqlite:///:memory:")
    store = SettingsStore(session_factory, master_key=master_key, cache_ttl_seconds=0)
    return SettingsService(store)


def test_risk_policy_roundtrip():
    service = make_service()
    policy = RiskPolicy(
        max_position_weight=0.2,
        stop_loss_pct=-0.07,
        daily_loss_limit_pct=-0.04,
        max_concurrent_positions=5,
    )
    service.set_risk_policy(policy)
    assert service.get_risk_policy() == policy


def test_risk_policy_defaults_when_unset():
    service = make_service()
    assert service.get_risk_policy() == RiskPolicy()


def test_trading_enabled_roundtrip():
    service = make_service()
    service.set_risk_policy(RiskPolicy(trading_enabled=False))
    assert service.get_risk_policy().trading_enabled is False
    service.set_risk_policy(RiskPolicy(trading_enabled=True))
    assert service.get_risk_policy().trading_enabled is True


def test_kis_credentials_are_encrypted_and_roundtrip():
    master_key = generate_master_key()
    service = make_service(master_key=master_key)
    creds = KISCredentials(
        kis_env="paper",
        app_key="app-key-123",
        app_secret="app-secret-456",
        account_no="12345678",
        account_product_cd="01",
    )
    service.set_kis_credentials(creds)
    assert service.get_kis_credentials() == creds


def test_secret_write_without_master_key_raises():
    service = make_service(master_key=None)
    with pytest.raises(RuntimeError, match="MUWON_MASTER_KEY"):
        service.set_kis_credentials(KISCredentials(app_key="x", app_secret="y"))


def test_strategy_selection_defaults_to_live_key():
    service = make_service()
    assert service.get_strategy_selection() == StrategySelection()


def test_strategy_selection_roundtrip_and_is_logged_in_history():
    service = make_service()
    service.set_strategy_selection(StrategySelection(active_key="ma_rsi_v1"))
    service.set_strategy_selection(StrategySelection(active_key="ma_rsi_fast5_20"))
    assert service.get_strategy_selection().active_key == "ma_rsi_fast5_20"

    entry = next(h for h in service.get_settings_history() if h.key == "strategy.active_key")
    assert entry.old_value == "ma_rsi_v1"
    assert entry.new_value == "ma_rsi_fast5_20"


def test_telegram_config_roundtrip():
    master_key = generate_master_key()
    service = make_service(master_key=master_key)
    cfg = TelegramConfig(bot_token="123:ABC", chat_id="999")
    service.set_telegram_config(cfg)
    assert service.get_telegram_config() == cfg


def test_history_records_non_secret_change():
    service = make_service()
    service.set_risk_policy(RiskPolicy(max_concurrent_positions=5))
    service.set_risk_policy(RiskPolicy(max_concurrent_positions=6))

    history = service.get_settings_history()
    entry = next(h for h in history if h.key == "risk.max_concurrent_positions")
    assert entry.old_value == "5"
    assert entry.new_value == "6"
    assert entry.decrypted is True


def test_history_skips_entry_when_value_unchanged():
    service = make_service()
    policy = RiskPolicy(max_concurrent_positions=5)
    service.set_risk_policy(policy)
    service.set_risk_policy(policy)  # 같은 값 재저장 — 이력 안 남아야 함

    history = [h for h in service.get_settings_history() if h.key == "risk.max_concurrent_positions"]
    assert len(history) == 1


def test_history_decrypts_secret_when_master_key_present():
    master_key = generate_master_key()
    service = make_service(master_key=master_key)
    service.set_kis_credentials(KISCredentials(app_key="key-a", app_secret="secret-a"))
    service.set_kis_credentials(KISCredentials(app_key="key-b", app_secret="secret-a"))

    history = service.get_settings_history()
    entry = next(h for h in history if h.key == "kis.app_key")
    assert entry.old_value == "key-a"
    assert entry.new_value == "key-b"
    assert entry.decrypted is True


def test_history_hides_secret_without_master_key():
    master_key = generate_master_key()
    session_factory = make_session_factory("sqlite:///:memory:")
    store_with_key = SettingsStore(session_factory, master_key=master_key, cache_ttl_seconds=0)
    SettingsService(store_with_key).set_kis_credentials(KISCredentials(app_key="key-a"))

    store_without_key = SettingsStore(session_factory, master_key=None, cache_ttl_seconds=0)
    service_without_key = SettingsService(store_without_key)

    entry = next(
        h for h in service_without_key.get_settings_history() if h.key == "kis.app_key"
    )
    assert entry.decrypted is False
    assert entry.new_value is None
