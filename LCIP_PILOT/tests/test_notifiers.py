import pytest

from notifiers import (
    EmailNotifier,
    NotifierDisabledError,
    TelegramNotifier,
    build_alert_message,
    load_notification_config,
)

CONFIG = {
    "notifications": {
        "test_mode": True,
        "email_enabled": True,
        "telegram_enabled": True,
    },
    "email": {"recipient_env": "LCIP_TEST_EMAIL_RECIPIENT"},
    "telegram": {"chat_id_env": "TELEGRAM_CHAT_ID"},
}


def _with_notifications(overrides: dict) -> dict:
    return {**CONFIG, "notifications": {**CONFIG["notifications"], **overrides}}


def test_email_notifier_dry_run_does_not_send_when_test_mode(monkeypatch):
    monkeypatch.setenv("LCIP_TEST_EMAIL_RECIPIENT", "tester@example.com")
    notifier = EmailNotifier(CONFIG)
    result = notifier.send("제목", "본문 내용입니다")
    assert result.sent is False
    assert result.test_mode is True
    assert result.channel == "email"
    assert result.recipient == "tester@example.com"


def test_email_notifier_disabled_channel_raises():
    notifier = EmailNotifier(_with_notifications({"email_enabled": False}))
    with pytest.raises(NotifierDisabledError):
        notifier.send("제목", "본문")


def test_email_notifier_real_send_blocked_even_when_test_mode_false(monkeypatch):
    monkeypatch.setenv("LCIP_TEST_EMAIL_RECIPIENT", "tester@example.com")
    monkeypatch.delenv("GMAIL_SENDER_ADDRESS", raising=False)
    notifier = EmailNotifier(CONFIG, test_mode=False)
    with pytest.raises(NotifierDisabledError):
        notifier.send("제목", "본문")


class _FakeGmailMessages:
    def __init__(self, sent_log: list[dict]):
        self._sent_log = sent_log

    def send(self, userId: str, body: dict):  # noqa: N803 - Gmail API 파라미터명 그대로
        self._sent_log.append({"userId": userId, "body": body})
        return self

    def execute(self):
        return {"id": "fake-message-id"}


class _FakeGmailUsers:
    def __init__(self, sent_log: list[dict]):
        self._sent_log = sent_log

    def messages(self):
        return _FakeGmailMessages(self._sent_log)


class _FakeGmailClient:
    def __init__(self, sent_log: list[dict]):
        self._sent_log = sent_log

    def users(self):
        return _FakeGmailUsers(self._sent_log)


def test_email_notifier_real_send_succeeds_with_injected_client(monkeypatch):
    """Round 13(RC2 실체화) — GoogleRSSAdapter의 http_get 주입과 동일한 패턴으로,
    실제 Gmail API/네트워크 없이 발송 로직만 검증한다."""
    monkeypatch.setenv("LCIP_TEST_EMAIL_RECIPIENT", "tester@example.com")
    monkeypatch.setenv("GMAIL_SENDER_ADDRESS", "lcip-bot@example.com")
    sent_log: list[dict] = []
    notifier = EmailNotifier(
        CONFIG, test_mode=False, client_factory=lambda: _FakeGmailClient(sent_log)
    )

    result = notifier.send("제목", "본문 내용입니다")

    assert result.sent is True
    assert result.test_mode is False
    assert result.recipient == "tester@example.com"
    assert len(sent_log) == 1
    assert sent_log[0]["userId"] == "me"
    assert "raw" in sent_log[0]["body"]


def test_telegram_notifier_dry_run_does_not_send(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456")
    notifier = TelegramNotifier(CONFIG)
    result = notifier.send("제목", "본문 내용입니다")
    assert result.sent is False
    assert result.channel == "telegram"
    assert result.recipient == "123456"


def test_telegram_notifier_disabled_channel_raises():
    notifier = TelegramNotifier(_with_notifications({"telegram_enabled": False}))
    with pytest.raises(NotifierDisabledError):
        notifier.send("제목", "본문")


def test_telegram_notifier_real_send_blocked_without_bot_token(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456")
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    notifier = TelegramNotifier(CONFIG, test_mode=False)
    with pytest.raises(NotifierDisabledError):
        notifier.send("제목", "본문")


def test_telegram_notifier_real_send_succeeds_with_injected_http_post(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    calls: list[tuple[str, dict]] = []

    def fake_post(bot_token: str, payload: dict) -> None:
        calls.append((bot_token, payload))

    notifier = TelegramNotifier(CONFIG, test_mode=False, http_post=fake_post)
    result = notifier.send("제목", "본문 내용입니다")

    assert result.sent is True
    assert result.test_mode is False
    assert result.recipient == "123456"
    assert len(calls) == 1
    assert calls[0][0] == "fake-token"
    assert calls[0][1]["chat_id"] == "123456"
    assert "제목" in calls[0][1]["text"]
    assert "본문 내용입니다" in calls[0][1]["text"]


def test_load_notification_config_resolves_real_recipient_env_names(monkeypatch):
    """config/notification.yaml은 email/telegram을 notifications의 형제(sibling) 키로
    둔다 — load_notification_config()가 부분만 잘라 반환하면 recipient_env/chat_id_env를
    찾지 못해 항상 "(미설정)"으로 표시되는 회귀가 생긴다."""
    monkeypatch.setenv("LCIP_TEST_EMAIL_RECIPIENT", "real-test@example.com")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "999999")
    config = load_notification_config()

    email_result = EmailNotifier(config).send("제목", "본문")
    telegram_result = TelegramNotifier(config).send("제목", "본문")

    assert email_result.recipient == "real-test@example.com"
    assert telegram_result.recipient == "999999"


def test_build_alert_message_includes_key_fields():
    article = {"title_original": "샘플 기사", "source_url": "https://example.com/a"}
    intelligence = {
        "fact_summary": "사실 요약",
        "lx_impact": ["영향 A"],
        "recommended_actions": ["조치 A"],
        "confidence_score": "low",
    }
    subject, body = build_alert_message(article, intelligence)
    assert "샘플 기사" in subject
    assert "https://example.com/a" in body
    assert "영향 A" in body
    assert "조치 A" in body
    assert "low" in body
