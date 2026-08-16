from muwon.risk.manager import RiskManager


def make_manager() -> RiskManager:
    return RiskManager(
        max_position_weight=0.15,
        stop_loss_pct=-0.05,
        daily_loss_limit_pct=-0.03,
        max_concurrent_positions=8,
    )


def test_approves_within_all_limits():
    rm = make_manager()
    decision = rm.check_new_position(
        proposed_weight=0.10, current_open_positions=3, daily_pnl_pct=-0.01
    )
    assert decision.approved


def test_blocks_when_daily_loss_limit_hit():
    rm = make_manager()
    decision = rm.check_new_position(
        proposed_weight=0.05, current_open_positions=1, daily_pnl_pct=-0.04
    )
    assert not decision.approved
    assert "일일 손실 한도" in decision.reason


def test_blocks_when_max_positions_reached():
    rm = make_manager()
    decision = rm.check_new_position(
        proposed_weight=0.05, current_open_positions=8, daily_pnl_pct=0.0
    )
    assert not decision.approved
    assert "최대 동시 보유" in decision.reason


def test_blocks_when_weight_exceeds_limit():
    rm = make_manager()
    decision = rm.check_new_position(
        proposed_weight=0.20, current_open_positions=1, daily_pnl_pct=0.0
    )
    assert not decision.approved
    assert "최대 비중" in decision.reason


def test_stop_loss_triggers_below_threshold():
    rm = make_manager()
    assert rm.should_stop_loss(entry_price=10000, current_price=9400)
    assert not rm.should_stop_loss(entry_price=10000, current_price=9600)
