from muwon.domain.types import OrderSide
from muwon.execution.simulated_executor import SimulatedOrderExecutor


def test_submit_order_fills_at_reference_price():
    executor = SimulatedOrderExecutor()
    result = executor.submit_order("005930", OrderSide.BUY, 10, 71000.0)

    assert result.symbol == "005930"
    assert result.side == OrderSide.BUY
    assert result.quantity == 10
    assert result.price == 71000.0
    assert result.is_paper is True
    assert result.order_id.startswith("SIM-")


def test_each_order_gets_a_unique_id():
    executor = SimulatedOrderExecutor()
    a = executor.submit_order("005930", OrderSide.BUY, 1, 100.0)
    b = executor.submit_order("005930", OrderSide.BUY, 1, 100.0)
    assert a.order_id != b.order_id
