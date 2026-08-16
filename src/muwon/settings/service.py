from dataclasses import dataclass
from datetime import datetime

from muwon.settings.schema import KISCredentials, RiskPolicy, TelegramConfig
from muwon.settings.store import SettingsStore


@dataclass
class SettingHistoryEntry:
    key: str
    old_value: str | None
    new_value: str | None
    is_secret: bool
    changed_at: datetime
    decrypted: bool  # is_secret인데 마스터키가 없어 값을 못 읽었으면 False


class SettingsService:
    """리스크 정책·KIS 인증정보·텔레그램 설정에 대한 타입 안전한 접근 창구.

    CLI(scripts/configure.py)와 (Phase 2+) 대시보드는 모두 이 서비스 하나를
    통해 설정을 읽고 쓴다 — 저장 방식이 바뀌어도 호출부는 영향받지 않는다.
    """

    def __init__(self, store: SettingsStore):
        self._store = store

    def get_risk_policy(self) -> RiskPolicy:
        d = RiskPolicy()
        return RiskPolicy(
            max_position_weight=float(
                self._store.get("risk.max_position_weight", str(d.max_position_weight))
            ),
            stop_loss_pct=float(self._store.get("risk.stop_loss_pct", str(d.stop_loss_pct))),
            daily_loss_limit_pct=float(
                self._store.get("risk.daily_loss_limit_pct", str(d.daily_loss_limit_pct))
            ),
            max_concurrent_positions=int(
                self._store.get(
                    "risk.max_concurrent_positions", str(d.max_concurrent_positions)
                )
            ),
        )

    def set_risk_policy(self, policy: RiskPolicy) -> None:
        self._store.set("risk.max_position_weight", str(policy.max_position_weight))
        self._store.set("risk.stop_loss_pct", str(policy.stop_loss_pct))
        self._store.set("risk.daily_loss_limit_pct", str(policy.daily_loss_limit_pct))
        self._store.set(
            "risk.max_concurrent_positions", str(policy.max_concurrent_positions)
        )

    def get_kis_credentials(self) -> KISCredentials:
        d = KISCredentials()
        return KISCredentials(
            kis_env=self._store.get("kis.env", d.kis_env),
            app_key=self._store.get("kis.app_key", d.app_key) or "",
            app_secret=self._store.get("kis.app_secret", d.app_secret) or "",
            account_no=self._store.get("kis.account_no", d.account_no) or "",
            account_product_cd=self._store.get(
                "kis.account_product_cd", d.account_product_cd
            )
            or "",
        )

    def set_kis_credentials(self, creds: KISCredentials) -> None:
        self._store.set("kis.env", creds.kis_env)
        self._store.set("kis.app_key", creds.app_key, secret=True)
        self._store.set("kis.app_secret", creds.app_secret, secret=True)
        self._store.set("kis.account_no", creds.account_no, secret=True)
        self._store.set("kis.account_product_cd", creds.account_product_cd)

    def get_telegram_config(self) -> TelegramConfig:
        d = TelegramConfig()
        return TelegramConfig(
            bot_token=self._store.get("telegram.bot_token", d.bot_token) or "",
            chat_id=self._store.get("telegram.chat_id", d.chat_id) or "",
        )

    def set_telegram_config(self, cfg: TelegramConfig) -> None:
        self._store.set("telegram.bot_token", cfg.bot_token, secret=True)
        self._store.set("telegram.chat_id", cfg.chat_id)

    def get_settings_history(self, limit: int = 100) -> list[SettingHistoryEntry]:
        entries = []
        for row in self._store.get_history(limit=limit):
            if not row.is_secret:
                old_value, new_value, decrypted = row.old_value, row.new_value, True
            else:
                old_value = self._store.try_decrypt(row.old_value)
                new_value = self._store.try_decrypt(row.new_value)
                decrypted = self._store.has_master_key
            entries.append(
                SettingHistoryEntry(
                    key=row.key,
                    old_value=old_value,
                    new_value=new_value,
                    is_secret=row.is_secret,
                    changed_at=row.changed_at,
                    decrypted=decrypted,
                )
            )
        return entries


def build_settings_service(
    database_url: str | None = None, master_key: str | None = None
) -> SettingsService:
    from muwon.config import bootstrap_settings
    from muwon.db.session import make_session_factory

    session_factory = make_session_factory(database_url or bootstrap_settings.database_url)
    store = SettingsStore(
        session_factory, master_key=master_key if master_key is not None else bootstrap_settings.master_key
    )
    return SettingsService(store)
