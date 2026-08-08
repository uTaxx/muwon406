"""공용 Google OAuth/Service Account 자격증명 로더.

Architect Review Round 13("RC2 실체화" — 새 기능 대신 이미 설계된 연결을 실제로
동작하게 만든다) 지시에 따라 신설했다. Drive(`create_drive_structure.py`)/
Sheets(`create_google_sheets.py`, `storage/google_sheets_storage.py`)/
Gmail(`notifiers.py`)이 전부 같은 Google 계정 인증 흐름(OAuth Desktop 또는 Service
Account)을 필요로 한다 — 각자 따로 구현하면 OAuth 코드가 여러 곳에 흩어지고 스코프
관리가 어긋나기 쉽다. 이 모듈은 새 Framework가 아니라, 각 파일이 `docs/
GOOGLE_DRIVE_SETUP.md`/`.env.example`에서 이미 정의해 둔 두 인증 방식
(`GOOGLE_OAUTH_CLIENT_ID`/`GOOGLE_OAUTH_CLIENT_SECRET`/`GOOGLE_OAUTH_TOKEN_PATH`,
`GOOGLE_SERVICE_ACCOUNT_JSON_PATH`)을 실제로 로드하는 얇은 공용 헬퍼일 뿐이다.

Credential 값 자체는 이 코드 어디에도 하드코딩하지 않는다 — `.env`에서 파일 경로/
Client ID만 읽고, 실제 Secret은 해당 파일(서비스 계정 JSON, OAuth 토큰 캐시)에서만
읽는다(CLAUDE.md 절대 원칙 #7).
"""
from __future__ import annotations

from pathlib import Path

from _common import env_or_none

DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

AUTH_MODES = ("oauth_desktop", "service_account")


class GoogleAuthError(RuntimeError):
    """Credential이 준비되지 않았거나 인증 흐름이 실패했을 때 발생한다."""


def load_credentials(auth_mode: str, scopes: list[str]):
    """`auth_mode`에 맞는 `google.auth.credentials.Credentials` 객체를 반환한다.

    이 함수를 호출하는 시점에는 이미 상위 코드(예: `GoogleSheetsStorage._require_ready()`,
    `create_drive_structure.py`의 `LCIP_CONFIRM_APPLY=yes` 검사)가 "실제로 호출해도
    되는 상태"임을 확인했다고 가정한다 — 이 함수 자체는 그 안전장치를 다시 검사하지
    않는다(책임 분리).
    """
    if auth_mode == "service_account":
        return _load_service_account_credentials(scopes)
    if auth_mode == "oauth_desktop":
        return _load_oauth_desktop_credentials(scopes)
    raise GoogleAuthError(
        f"알 수 없는 auth_mode: {auth_mode!r} (지원: {', '.join(AUTH_MODES)})"
    )


def _load_service_account_credentials(scopes: list[str]):
    from google.oauth2.service_account import Credentials as ServiceAccountCredentials

    sa_path = env_or_none("GOOGLE_SERVICE_ACCOUNT_JSON_PATH")
    if not sa_path:
        raise GoogleAuthError(
            "GOOGLE_SERVICE_ACCOUNT_JSON_PATH가 .env에 설정되어 있지 않다 — 서비스 계정 "
            "키 JSON 파일 경로가 필요하다 (docs/GOOGLE_DRIVE_SETUP.md §1 참고)."
        )
    path = Path(sa_path)
    if not path.exists():
        raise GoogleAuthError(f"서비스 계정 키 파일을 찾을 수 없다: {sa_path}")
    return ServiceAccountCredentials.from_service_account_file(str(path), scopes=scopes)


def _load_oauth_desktop_credentials(scopes: list[str]):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    token_path = Path(env_or_none("GOOGLE_OAUTH_TOKEN_PATH") or "./credentials/token.json")
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), scopes)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        client_id = env_or_none("GOOGLE_OAUTH_CLIENT_ID")
        client_secret = env_or_none("GOOGLE_OAUTH_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise GoogleAuthError(
                "GOOGLE_OAUTH_CLIENT_ID/GOOGLE_OAUTH_CLIENT_SECRET이 .env에 설정되어 "
                "있지 않다 — Desktop App 유형 OAuth Client를 발급받아야 한다 "
                "(docs/GOOGLE_DRIVE_SETUP.md §1)."
            )
        client_config = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }
        }
        flow = InstalledAppFlow.from_client_config(client_config, scopes)
        # 최초 1회는 사용자 브라우저 승인이 필요하다 — 이후 실행부터는 token_path에
        # 캐시된 토큰을 재사용/갱신하므로 브라우저가 다시 뜨지 않는다.
        creds = flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    return creds
