"""텔레그램 요약 검증.

**안 읽는 알림은 없는 것과 같고, 오히려 진짜 중요한 알림을 묻는다.**
그래서 짧아야 하고, 짧게 줄이는 과정에서 경고가 빠지면 안 된다."""

from datetime import date

import pandas as pd

from muwon.market.analog import Baseline, Forecast
from muwon.market.digest import MAX_LEN, state_line, summarize


def _상태(추세=1.0, 낙폭=-2.0, 변동성=0.5):
    return pd.DataFrame(
        {"kospi_추세20": [추세], "kospi_고점대비": [낙폭], "kospi_변동성": [변동성]},
        index=[date(2026, 8, 19)],
    )


def _전망(대상="반도체", 상승확률=70.0, 기준선=55.0, 구간수=16, 낼수있나=True):
    return Forecast(
        기준일=date(2026, 8, 19), 대상=대상, 구간수=구간수, 총일수=200, 지평=20,
        중앙값=2.0 if 낼수있나 else None,
        상위25=6.0 if 낼수있나 else None,
        하위25=-1.0 if 낼수있나 else None,
        하위10=-8.0 if 낼수있나 else None,
        상승확률=상승확률 if 낼수있나 else None,
        구간들=[],
        사유="" if 낼수있나 else "비슷했던 때가 3번뿐입니다",
        기준선=Baseline(표본수=1000, 중앙값=1.0, 하위10=-9.0, 상승확률=기준선),
    )


def test_the_state_line_shows_direction_not_just_numbers():
    """숫자만 있으면 폰에서 훑어볼 수가 없다."""
    글 = state_line(_상태(추세=2.0, 변동성=-1.5))
    assert "▲" in 글 and "▼" in 글
    assert "코스피" in 글


def test_an_empty_state_says_so_instead_of_crashing():
    assert "잴 수 없음" in state_line(pd.DataFrame())


def test_the_rejection_warning_survives_the_summary():
    """전망은 이미 기각됐다. 요약에서 그 말이 빠지면 매일 아침 그럴듯한
    숫자만 보게 되고, 그러다 어느 날 그걸 근거로 삼게 된다."""
    글 = summarize(_상태(), [_전망()], date(2026, 8, 19))
    assert "기각" in 글
    assert "매매 판단에 쓰지 마세요" in 글
    assert "아무것도 사지 않았습니다" in 글


def test_a_result_within_chance_is_not_starred():
    """우연 폭을 못 넘는 숫자를 강조하면 그게 곧 근거로 읽힌다."""
    # 16개 구간이면 우연 폭이 ±24.5%p. +5%p는 한참 안쪽이다.
    안쪽 = summarize(_상태(), [_전망(상승확률=60.0, 기준선=55.0)], date(2026, 8, 19))
    별 = [줄 for 줄 in 안쪽.splitlines() if "반도체" in 줄]
    assert 별 and "★" not in 별[0]

    # 표본이 많으면 같은 차이도 뜻을 갖는다.
    바깥 = summarize(
        _상태(), [_전망(상승확률=60.0, 기준선=55.0, 구간수=400)], date(2026, 8, 19)
    )
    별2 = [줄 for 줄 in 바깥.splitlines() if "반도체" in 줄]
    assert 별2 and "★" in 별2[0]


def test_it_says_why_a_forecast_could_not_be_made():
    """'없음'만 보이면 고장인지 표본이 모자란 건지 알 수 없다."""
    글 = summarize(_상태(), [_전망("로봇", 낼수있나=False)], date(2026, 8, 19))
    assert "전망 못 냄" in 글
    assert "3번뿐" in 글


def test_a_long_report_is_trimmed_to_one_message():
    """텔레그램 한 통을 넘기면 잘려서 도착한다 — 하필 뒤쪽 경고가 잘린다."""
    많은것 = [_전망(f"섹터{i}") for i in range(200)]
    글 = summarize(_상태(), 많은것, date(2026, 8, 19))
    assert len(글) <= MAX_LEN
    assert "줄임" in 글


def test_the_header_carries_the_date():
    글 = summarize(_상태(), [_전망()], date(2026, 8, 19))
    assert "2026-08-19" in 글.splitlines()[0]
