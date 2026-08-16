import pytest

from muwon.db.session import make_session_factory
from muwon.settings.crypto import generate_master_key
from muwon.settings.schema import KISCredentials, RiskPolicy, TelegramConfig
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


def test_telegram_config_roundtrip():
    master_key = generate_master_key()
    service = make_service(master_key=master_key)
    cfg = TelegramConfig(bot_token="123:ABC", chat_id="999")
    service.set_telegram_config(cfg)
    assert service.get_telegram_config() == cfg
