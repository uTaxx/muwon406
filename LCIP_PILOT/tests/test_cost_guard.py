import cost_guard


FIXTURE_POLICY = {
    "monthly_budget_usd": 20,
    "target_budget_usd": 15,
    "warning_rate": 0.70,
    "restrict_rate": 0.90,
    "hard_stop_rate": 1.00,
    "daily_deep_analysis_limit": 5,
}


def test_normal_state_below_warning():
    result = cost_guard.evaluate(5.0, FIXTURE_POLICY)
    assert result.state == "NORMAL"
    assert result.allow_deep_analysis is True


def test_warning_state_at_70_percent():
    result = cost_guard.evaluate(14.0, FIXTURE_POLICY)  # 70%
    assert result.state == "WARNING"
    assert result.allow_deep_analysis is True


def test_restricted_state_at_90_percent():
    result = cost_guard.evaluate(18.0, FIXTURE_POLICY)  # 90%
    assert result.state == "RESTRICTED"
    assert result.allow_emergency_only is True


def test_stopped_state_at_100_percent():
    result = cost_guard.evaluate(20.0, FIXTURE_POLICY)  # 100%
    assert result.state == "STOPPED"
    assert result.allow_deep_analysis is False


def test_stopped_state_over_budget():
    result = cost_guard.evaluate(25.0, FIXTURE_POLICY)
    assert result.state == "STOPPED"


def test_daily_deep_analysis_limit():
    assert cost_guard.check_daily_deep_analysis_limit(4, FIXTURE_POLICY) is True
    assert cost_guard.check_daily_deep_analysis_limit(5, FIXTURE_POLICY) is False


def test_estimate_cost_usd():
    cost = cost_guard.estimate_cost_usd(
        input_tokens=1_000_000, output_tokens=1_000_000,
        usd_per_million_input=3.0, usd_per_million_output=15.0,
    )
    assert cost == 18.0
