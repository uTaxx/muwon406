"""TASK-013 — Gmail/Telegram Notifier.

CLAUDE.md 절대 원칙 #8("실제 외부 쓰기는 사용자의 명시적 승인 전까지 금지, 기본은 항상
dry-run")에 따라, `config/notification.yaml`의 `test_mode: true`(기본값)인 동안은 실제
발송 API를 전혀 호출하지 않는다 — 발송했다면 어떤 내용이 누구에게 갔을지를 나타내는
`NotifierResult`만 반환한다.

Architect Review Round 13(RC2 실체화) — `test_mode=False`일 때의 실제 발송 경로를
완성했다. Provider/Adapter와 동일한 2중 안전장치는 그대로 유지된다: `enabled`(채널
자체가 꺼져 있으면 즉시 멈춤) + `test_mode`(꺼야만 실제 API까지 도달). Gmail은
`scripts/google_auth.py`(Drive/Sheets와 공용 OAuth) 경유 Gmail API, Telegram은
Bot API를 `requests`로 직접 호출한다(이미 있는 의존성, 새 라이브러리 없음).
`client_factory`/`http_post`를 주입하면(테스트용) 실제 네트워크 없이 로직만
검증할 수 있다 — `GoogleRSSAdapter`의 `http_get` 주입과 동일한 패턴이다.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

from _common import env_or_none, load_yaml


@dataclass(frozen=True)
class NotifierResult:
    sent: bool
    channel: str
    recipient: str
    subject: str
    body_preview: str
    test_mode: bool


def load_notification_config() -> dict:
    """config/notification.yaml 전체(최상위 `notifications`/`email`/`telegram` 세 섹션)를
    그대로 반환한다. 세 섹션은 형제(sibling) 키이며 `notifications` 밑에 중첩되어 있지 않다
    — Notifier는 이 셋을 모두 읽어야 하므로 부분만 잘라 반환하면 안 된다."""
    return load_yaml("config/notification.yaml")


class NotifierDisabledError(RuntimeError):
    """실제 발송 경로가 아직 구현되지 않았거나 채널이 꺼져 있을 때 발생."""


class Notifier(ABC):
    channel: str

    @abstractmethod
    def send(self, subject: str, body: str) -> NotifierResult:
        """제목/본문을 발송(또는 test_mode dry-run)한다."""


class EmailNotifier(Notifier):
    channel = "email"

    def __init__(
        self,
        config: dict | None = None,
        test_mode: bool | None = None,
        auth_mode: str = "oauth_desktop",
        client_factory: Callable[[], object] | None = None,
    ):
        config = config or load_notification_config()
        notifications = config.get("notifications", {})
        self.enabled = notifications.get("email_enabled", False)
        self.recipient_env = config.get("email", {}).get("recipient_env", "")
        self.test_mode = test_mode if test_mode is not None else notifications.get("test_mode", True)
        self.auth_mode = auth_mode
        self._client_factory = client_factory

    def send(self, subject: str, body: str) -> NotifierResult:
        if not self.enabled:
            raise NotifierDisabledError("email_enabled=False — config/notification.yaml에서 꺼져 있다.")
        recipient = env_or_none(self.recipient_env)
        if self.test_mode:
            return NotifierResult(
                sent=False,
                channel=self.channel,
                recipient=recipient or f"(미설정 — .env에 {self.recipient_env} 필요)",
                subject=subject,
                body_preview=body[:200],
                test_mode=True,
            )
        if not recipient:
            raise NotifierDisabledError(f".env에 {self.recipient_env}가 설정되어 있지 않다.")
        sender = env_or_none("GMAIL_SENDER_ADDRESS")
        if not sender:
            raise NotifierDisabledError(".env에 GMAIL_SENDER_ADDRESS가 설정되어 있지 않다.")
        self._send_gmail(sender, recipient, subject, body)
        return NotifierResult(
            sent=True, channel=self.channel, recipient=recipient,
            subject=subject, body_preview=body[:200], test_mode=False,
        )

    def _send_gmail(self, sender: str, recipient: str, subject: str, body: str) -> None:
        client = self._get_client()
        import base64
        from email.mime.text import MIMEText

        message = MIMEText(body)
        message["to"] = recipient
        message["from"] = sender
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        client.users().messages().send(userId="me", body={"raw": raw}).execute()

    def _get_client(self):
        if self._client_factory is not None:
            return self._client_factory()

        from googleapiclient.discovery import build
        from google_auth import GMAIL_SCOPES, load_credentials

        creds = load_credentials(self.auth_mode, GMAIL_SCOPES)
        return build("gmail", "v1", credentials=creds)


class TelegramNotifier(Notifier):
    channel = "telegram"

    def __init__(
        self,
        config: dict | None = None,
        test_mode: bool | None = None,
        http_post: Callable[[str, dict], None] | None = None,
    ):
        config = config or load_notification_config()
        notifications = config.get("notifications", {})
        self.enabled = notifications.get("telegram_enabled", False)
        self.chat_id_env = config.get("telegram", {}).get("chat_id_env", "")
        self.test_mode = test_mode if test_mode is not None else notifications.get("test_mode", True)
        self._http_post = http_post or _default_telegram_post

    def send(self, subject: str, body: str) -> NotifierResult:
        if not self.enabled:
            raise NotifierDisabledError("telegram_enabled=False — config/notification.yaml에서 꺼져 있다.")
        chat_id = env_or_none(self.chat_id_env)
        if self.test_mode:
            return NotifierResult(
                sent=False,
                channel=self.channel,
                recipient=chat_id or f"(미설정 — .env에 {self.chat_id_env} 필요)",
                subject=subject,
                body_preview=body[:200],
                test_mode=True,
            )
        if not chat_id:
            raise NotifierDisabledError(f".env에 {self.chat_id_env}가 설정되어 있지 않다.")
        bot_token = env_or_none("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            raise NotifierDisabledError(".env에 TELEGRAM_BOT_TOKEN이 설정되어 있지 않다.")
        text = f"{subject}\n\n{body}"
        self._http_post(bot_token, {"chat_id": chat_id, "text": text})
        return NotifierResult(
            sent=True, channel=self.channel, recipient=chat_id,
            subject=subject, body_preview=body[:200], test_mode=False,
        )


def _default_telegram_post(bot_token: str, payload: dict) -> None:
    import requests

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()


def build_alert_message(article: dict, intelligence: dict) -> tuple[str, str]:
    """Article/Intelligence 레코드로 알림 제목/본문을 만든다 (TASK-017 데모용)."""
    subject = f"[LCIP] {article.get('title_original', '(제목 없음)')}"
    lines = [
        f"기사: {article.get('title_original', '')}",
        f"원문: {article.get('source_url', '')}",
        f"사실 요약: {intelligence.get('fact_summary', '')}",
        f"LX 영향: {'; '.join(intelligence.get('lx_impact', [])) or '(확인된 영향 없음)'}",
        f"권고 조치: {'; '.join(intelligence.get('recommended_actions', [])) or '(없음)'}",
        f"신뢰도: {intelligence.get('confidence_score', '')}",
    ]
    return subject, "\n".join(lines)


def build_digest_message(records: list[tuple[dict, dict]]) -> tuple[str, str]:
    """뉴스 수집 실체화 라운드(2026-08-08) 신설 — 한 번의 배치 실행에서 나온 여러
    (article, intelligence) 쌍을 하나의 다이제스트 제목/본문으로 합친다.
    `scripts/pipeline/build_digest.py`의 얇은 wrapper다(새 Notifier 클래스 없음,
    `EmailNotifier`/`TelegramNotifier`가 그대로 이 결과를 `send()`한다)."""
    from pipeline.build_digest import build_digest_body, build_digest_subject

    return build_digest_subject(records), build_digest_body(records)
