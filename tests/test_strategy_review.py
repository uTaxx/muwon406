from datetime import date

from muwon.analysis.strategy_review import (
    SweepResult,
    build_review_report,
    format_review_message,
    persist_sweep_results,
    sweep_strategies,
)
from muwon.db.models import BacktestRunRow
from muwon.db.session import make_session_factory
from muwon.risk.manager import RiskManager
from muwon.settings.schema import RiskPolicy
from muwon.strategy.registry import list_definitions
from tests.price_series import breakout_entry_then_dead_cross_exit


def make_result(key: str, return_pct: float) -> SweepResult:
    return SweepResult(
        key=key,
        display_name=key,
        status="hypothesis",
        return_pct=return_pct,
        mdd_pct=-5.0,
        win_rate_pct=50.0,
        num_trades=3,
        params_json="{}",
    )


def test_sweep_strategies_runs_every_registered_definition_independently():
    df = breakout_entry_then_dead_cross_exit()
    risk_manager = RiskManager(policy_provider=lambda: RiskPolicy())

    results = sweep_strategies(list_definitions(), {"TEST": df}, risk_manager)

    assert {r.key for r in results} == {d.key for d in list_definitions()}
    for r in results:
        assert r.num_trades >= 0
        assert r.params_json != ""


def test_persist_sweep_results_tags_notes_for_later_filtering():
    session_factory = make_session_factory("sqlite:///:memory:")
    results = [make_result("ma_rsi_v1", 3.0), make_result("ma_rsi_fast5_20", -2.0)]

    persist_sweep_results(session_factory, results, date(2026, 1, 1), date(2026, 3, 1), notes="daily_review")

    with session_factory() as session:
        rows = session.query(BacktestRunRow).all()
    assert len(rows) == 2
    assert all(row.notes == "daily_review" for row in rows)
    assert {row.strategy_key for row in rows} == {"ma_rsi_v1", "ma_rsi_fast5_20"}


def test_review_report_flags_live_as_best_when_it_wins():
    results = [make_result("ma_rsi_v1", 5.0), make_result("ma_rsi_fast5_20", -2.0)]
    report = build_review_report(results, "ma_rsi_v1", date(2026, 1, 1), date(2026, 3, 1))

    assert report.live_is_best is True
    assert report.best_result.key == "ma_rsi_v1"

    message = format_review_message(report)
    assert "최고 성과 중" in message or "최고 성과입니다" in message
    assert "전환 검토" not in message


def test_review_report_suggests_switch_when_another_strategy_wins():
    results = [make_result("ma_rsi_v1", -3.0), make_result("ma_rsi_fast5_20", 6.0)]
    report = build_review_report(results, "ma_rsi_v1", date(2026, 1, 1), date(2026, 3, 1))

    assert report.live_is_best is False
    assert report.best_result.key == "ma_rsi_fast5_20"

    message = format_review_message(report)
    assert "다른 전략이었다면" in message
    assert "ma_rsi_fast5_20" in message
    assert "+9.00%p" in message  # 6.0 - (-3.0)
    assert "전환 검토: python scripts/configure.py strategy --active-key ma_rsi_fast5_20" in message


def test_review_report_handles_live_key_missing_from_results():
    results = [make_result("ma_rsi_fast5_20", 1.0)]
    report = build_review_report(results, "does-not-exist", date(2026, 1, 1), date(2026, 3, 1))

    assert report.live_result is None
    message = format_review_message(report)
    assert "비교 대상에 없습니다" in message
