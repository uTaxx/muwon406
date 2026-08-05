"""TASK-013 — Gmail/Telegram Notifier.

CLAUDE.md 절대 원칙 #8("실제 외부 쓰기는 사용자의 명시적 승인 전까지 금지, 기본은 항상
dry-run")에 따라, `config/notification.yaml`의 `test_mode: true`인 동안은 실제 발송 API를
전혀 호출하지 않는다 — 발송했다면 어떤 내용이 누구에게 갔을지를 나타내는 `NotifierResult`만
반환한다. `test_mode=False`로 두더라도 실제 발송 경로(`_send_real`)는 TASK-013 본구현
(사용자 승인 후) 대상으로 명시적으로 막아둔다 — Provider/Adapter와 동일한 2중 안전장치
패턴이다.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

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

    def __init__(self, config: dict | None = None, test_mode: bool | None = None):
        config = config or load_notification_config()
        notifications = config.get("notifications", {})
        self.enabled = notifications.get("email_enabled", False)
        self.recipient_env = config.get("email", {}).get("recipient_env", "")
        self.test_mode = test_mode if test_mode is not None else notifications.get("test_mode", True)

    def send(self, subject: str, body: str) -> NotifierResult:
        if not self.enabled:
            raise NotifierDisabledError("email_enabled=False — config/notification.yaml에서 꺼져 있다.")
        recipient = env_or_none(self.recipient_env) or f"(미설정 — .env에 {self.recipient_env} 필요)"
        if self.test_mode:
            return NotifierResult(
                sent=False,
                channel=self.channel,
                recipient=recipient,
                subject=subject,
                body_preview=body[:200],
                test_mode=True,
            )
        raise NotifierDisabledError(
            "EmailNotifier 실제 발송 경로는 TASK-013 본구현(사용자 승인 후)에서 완성한다. "
            "지금은 test_mode=True로만 사용하라."
        )


class TelegramNotifier(Notifier):
    channel = "telegram"

    def __init__(self, config: dict | None = None, test_mode: bool | None = None):
        config = config or load_notification_config()
        notifications = config.get("notifications", {})
        self.enabled = notifications.get("telegram_enabled", False)
        self.chat_id_env = config.get("telegram", {}).get("chat_id_env", "")
        self.test_mode = test_mode if test_mode is not None else notifications.get("test_mode", True)

    def send(self, subject: str, body: str) -> NotifierResult:
        if not self.enabled:
            raise NotifierDisabledError("telegram_enabled=False — config/notification.yaml에서 꺼져 있다.")
        recipient = env_or_none(self.chat_id_env) or f"(미설정 — .env에 {self.chat_id_env} 필요)"
        if self.test_mode:
            return NotifierResult(
                sent=False,
                channel=self.channel,
                recipient=recipient,
                subject=subject,
                body_preview=body[:200],
                test_mode=True,
            )
        raise NotifierDisabledError(
            "TelegramNotifier 실제 발송 경로는 TASK-013 본구현(사용자 승인 후)에서 완성한다. "
            "지금은 test_mode=True로만 사용하라."
        )


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
