"""Round 8 — Financial Provider 검증."""
from __future__ import annotations

from financial_provider import FinancialDataProvider, MockFinancialDataProvider
from investment_review import ComparablePeer


def test_mock_financial_data_provider_is_a_financial_data_provider():
    assert isinstance(MockFinancialDataProvider(), FinancialDataProvider)


def test_mock_financial_data_provider_returns_comparable_peers():
    peers = MockFinancialDataProvider().get_comparable_peers("LX_HAUSYS")
    assert len(peers) == 2
    assert all(isinstance(p, ComparablePeer) for p in peers)


def test_mock_financial_data_provider_same_result_regardless_of_company():
    provider = MockFinancialDataProvider()
    assert provider.get_comparable_peers("LX_HAUSYS") == provider.get_comparable_peers(None)


def test_mock_financial_data_provider_peers_are_labeled_as_examples():
    peers = MockFinancialDataProvider().get_comparable_peers("LX_HAUSYS")
    assert all("예시" in p.peer_name for p in peers)
