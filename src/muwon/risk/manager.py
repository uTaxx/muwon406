from dataclasses import dataclass


@dataclass
class RiskDecision:
    approved: bool
    reason: str


class RiskManager:
    """주문 실행 전 마지막으로 거치는 검증 계층.

    전략이 매수 신호를 내더라도, 여기서 정한 규칙을 어기면 주문은 거부된다.
    """

    def __init__(
        self,
        max_position_weight: float,
        stop_loss_pct: float,
        daily_loss_limit_pct: float,
        max_concurrent_positions: int,
    ):
        self.max_position_weight = max_position_weight
        self.stop_loss_pct = stop_loss_pct
        self.daily_loss_limit_pct = daily_loss_limit_pct
        self.max_concurrent_positions = max_concurrent_positions

    def check_new_position(
        self,
        proposed_weight: float,
        current_open_positions: int,
        daily_pnl_pct: float,
    ) -> RiskDecision:
        if daily_pnl_pct <= self.daily_loss_limit_pct:
            return RiskDecision(
                approved=False,
                reason=f"일일 손실 한도 도달 (daily_pnl={daily_pnl_pct:.2%}, "
                f"한도={self.daily_loss_limit_pct:.2%}) — 신규 진입 중단",
            )
        if current_open_positions >= self.max_concurrent_positions:
            return RiskDecision(
                approved=False,
                reason=f"최대 동시 보유 종목 수 초과 ({current_open_positions}/"
                f"{self.max_concurrent_positions})",
            )
        if proposed_weight > self.max_position_weight:
            return RiskDecision(
                approved=False,
                reason=f"종목당 최대 비중 초과 (제안={proposed_weight:.2%}, "
                f"한도={self.max_position_weight:.2%})",
            )
        return RiskDecision(approved=True, reason="승인")

    def should_stop_loss(self, entry_price: float, current_price: float) -> bool:
        if entry_price <= 0:
            return False
        change_pct = (current_price - entry_price) / entry_price
        return change_pct <= self.stop_loss_pct
