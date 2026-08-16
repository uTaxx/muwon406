import time

from sqlalchemy.orm import sessionmaker

from muwon.db.models import AppSettingRow
from muwon.settings.crypto import decrypt, encrypt


class SettingsStore:
    """DB에 저장된 키-값 설정을 읽고 쓰는 저수준 저장소.

    운영 봇 프로세스와 (미래의) 대시보드 프로세스가 같은 DB를 공유할 수
    있으므로, 로컬 캐시는 TTL이 지나면 자동 갱신하고, 이 프로세스에서 직접
    set()한 경우에는 즉시 캐시를 갱신한다.
    """

    def __init__(
        self,
        session_factory: sessionmaker,
        master_key: str | None = None,
        cache_ttl_seconds: float = 5.0,
    ):
        self._session_factory = session_factory
        self._master_key = master_key or None
        self._cache_ttl = cache_ttl_seconds
        self._cache: dict[str, tuple[str, bool]] = {}
        self._cache_loaded_at: float = 0.0

    def _refresh_cache_if_stale(self) -> None:
        if time.time() - self._cache_loaded_at < self._cache_ttl:
            return
        with self._session_factory() as session:
            rows = session.query(AppSettingRow).all()
            self._cache = {row.key: (row.value, row.is_secret) for row in rows}
        self._cache_loaded_at = time.time()

    def get(self, key: str, default: str | None = None) -> str | None:
        self._refresh_cache_if_stale()
        if key not in self._cache:
            return default
        stored_value, is_secret = self._cache[key]
        if not is_secret:
            return stored_value
        if not self._master_key:
            raise RuntimeError(
                f"'{key}' 값은 암호화되어 있는데 MUWON_MASTER_KEY가 설정되지 "
                "않아 복호화할 수 없습니다."
            )
        return decrypt(stored_value, self._master_key)

    def set(self, key: str, value: str, secret: bool = False) -> None:
        if secret and not self._master_key:
            raise RuntimeError(
                "비밀값을 저장하려면 MUWON_MASTER_KEY 환경변수가 필요합니다."
            )
        stored_value = encrypt(value, self._master_key) if secret else value
        with self._session_factory() as session:
            row = session.get(AppSettingRow, key)
            if row is None:
                session.add(AppSettingRow(key=key, value=stored_value, is_secret=secret))
            else:
                row.value = stored_value
                row.is_secret = secret
            session.commit()
        self._cache[key] = (stored_value, secret)
        self._cache_loaded_at = time.time()
