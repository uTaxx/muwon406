import pytest

from feature_flags import is_enabled, load_feature_flags


def test_load_feature_flags_returns_dict_with_expected_keys():
    flags = load_feature_flags()
    assert set(flags.keys()) == {
        "real_network_calls", "claude_api_enabled", "google_sheets_enabled",
        "notification_send_enabled",
    }


def test_all_flags_default_off_until_next_architect_approval():
    """Round 6 지시: "외부 API 실제 호출은 다음 Architect 승인 이후 시작한다" — 지금은
    전부 false여야 한다."""
    flags = load_feature_flags()
    assert all(value is False for value in flags.values())


def test_is_enabled_reads_from_config():
    assert is_enabled("real_network_calls") is False


def test_is_enabled_accepts_injected_flags_dict():
    assert is_enabled("real_network_calls", {"real_network_calls": True}) is True


def test_is_enabled_unknown_flag_raises():
    with pytest.raises(ValueError):
        is_enabled("no_such_flag")
