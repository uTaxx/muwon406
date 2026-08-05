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
    notifier = EmailNotifier(CONFIG, test_mode=False)
    with pytest.raises(NotifierDisabledError):
        notifier.send("제목", "본문")


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
