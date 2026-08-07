"""Round 8/10 — Financial Provider 검증.

Round 10 지시: "Peer를 회사별 실제 Peer로 변경한다. 현재 'Peer A/Peer B' 삭제. Mock
데이터여도 회사별 Peer는 실제 회사여야 한다." 이 테스트는 (1) 더 이상 "Peer A/B (예시)"
placeholder를 쓰지 않는지, (2) 회사마다 다른 실제 Comparable Peer 그룹을 반환하는지,
(3) 자기 자신은 자신의 Peer 목록에 포함되지 않는지, (4) 확인하지 못한 배수는 None으로
정직하게 남아 있는지를 검증한다.
"""
from __future__ import annotations

from financial_provider import FinancialDataProvider, MockFinancialDataProvider
from investment_review import ComparablePeer


def test_mock_financial_data_provider_is_a_financial_data_provider():
    assert isinstance(MockFinancialDataProvider(), FinancialDataProvider)


def test_mock_financial_data_provider_returns_comparable_peers():
    peers = MockFinancialDataProvider().get_comparable_peers("LX_HAUSYS")
    assert len(peers) > 0
    assert all(isinstance(p, ComparablePeer) for p in peers)


def test_lx_hausys_peers_match_architect_specified_group():
    """Architect Review Round 10이 직접 예시로 지정한 LX Hausys의 5개 Peer(KCC/한샘/
    LIXIL/YKK AP/Saint-Gobain)를 그대로 반환하는지 확인한다."""
    peers = MockFinancialDataProvider().get_comparable_peers("LX_HAUSYS")
    peer_names = {p.peer_name for p in peers}
    assert peer_names == {"KCC Corporation", "Hanssem", "LIXIL Corporation", "YKK AP", "Saint-Gobain"}


def test_peers_differ_by_company_no_longer_identical_placeholder():
    """Round 8까지는 회사와 무관하게 항상 동일한 'Peer A/B'를 반환했다 — Round 10부터는
    회사마다 다른 실제 Peer 그룹이 나와야 한다."""
    provider = MockFinancialDataProvider()
    lx_peers = {p.peer_name for p in provider.get_comparable_peers("LX_HAUSYS")}
    caesarstone_peers = {p.peer_name for p in provider.get_comparable_peers("CAESARSTONE")}
    assert lx_peers != caesarstone_peers


def test_peer_names_are_never_the_old_example_placeholder():
    """"Peer A (예시)"/"Peer B (예시)" 같은 placeholder 이름이 완전히 삭제됐는지 확인한다."""
    provider = MockFinancialDataProvider()
    for company_id in ("LX_HAUSYS", "KCC", "HANSSEM", "CAESARSTONE", "COSENTINO", None):
        for peer in provider.get_comparable_peers(company_id):
            assert "예시" not in peer.peer_name
            assert peer.peer_name not in ("Peer A", "Peer B")


_PEER_COMPANY_IDS_UNDER_TEST = [
    "LX_HAUSYS", "KCC", "HANSSEM", "CAESARSTONE", "COSENTINO",
    "SHAW_INDUSTRIES", "LIXIL", "YKK_AP", "SCHUCO", "SAINT_GOBAIN",
]


def test_company_never_appears_as_its_own_peer():
    from _common import load_yaml

    provider = MockFinancialDataProvider()
    companies = {c["company_id"]: c["display_name"] for c in load_yaml("config/company_registry.yaml")["companies"]}
    for company_id in _PEER_COMPANY_IDS_UNDER_TEST:
        peer_names = {p.peer_name for p in provider.get_comparable_peers(company_id)}
        assert companies[company_id] not in peer_names


def test_unmapped_company_gets_default_real_peer_group_not_empty():
    """Company Registry에는 있지만 아직 전용 Peer 그룹이 없는 회사(TOP10 외 20개사)도
    빈 목록이 아니라 실제 회사로 구성된 기본 Peer 그룹을 받는다."""
    peers = MockFinancialDataProvider().get_comparable_peers("WILSONART")
    assert len(peers) > 0
    assert all("예시" not in p.peer_name for p in peers)


def test_unconfirmed_multiples_stay_none_not_fabricated():
    """비상장이거나 배수를 확인하지 못한 회사(Cosentino/YKK AP/Schüco 등)는 EV/EBITDA·
    PER·PBR을 임의로 추정하지 않고 None으로 남긴다."""
    peers = MockFinancialDataProvider().get_comparable_peers("YKK_AP")
    schuco_peer = next(p for p in peers if p.peer_name == "Schüco International")
    assert schuco_peer.ev_ebitda is None
    assert schuco_peer.per is None
    assert schuco_peer.pbr is None


def test_confirmed_multiples_are_populated_for_saint_gobain():
    """실제로 확인된 배수(Saint-Gobain)는 채워져 있어야 한다."""
    peers = MockFinancialDataProvider().get_comparable_peers("LX_HAUSYS")
    saint_gobain_peer = next(p for p in peers if p.peer_name == "Saint-Gobain")
    assert saint_gobain_peer.ev_ebitda is not None
    assert saint_gobain_peer.per is not None
    assert saint_gobain_peer.pbr is not None
