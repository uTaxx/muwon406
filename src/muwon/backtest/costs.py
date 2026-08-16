from dataclasses import dataclass


@dataclass(frozen=True)
class TransactionCosts:
    """국내 주식 기준 근사치. 실제 수수료율은 증권사·시점에 따라 다르므로
    실거래 전환 전 반드시 실제 계좌 조건으로 다시 확인할 것."""

    buy_fee_pct: float = 0.00015  # 매수 수수료 약 0.015%
    sell_fee_pct: float = 0.00015  # 매도 수수료 약 0.015%
    sell_tax_pct: float = 0.0018  # 매도 시 증권거래세 약 0.18% (근사치)

    @property
    def total_sell_cost_pct(self) -> float:
        return self.sell_fee_pct + self.sell_tax_pct
