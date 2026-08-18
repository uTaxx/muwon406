"""자동 실행 일정 계산 검증.

이 계산이 틀리면 화면이 "내일 아침 09:05"라고 말하는데 실제로는 오늘
저녁에 돈다. 안내가 아니라 거짓말이 된다."""

from datetime import datetime
from pathlib import Path

from muwon.dashboard.schedule import KST, describe_cron, next_fire, upcoming


def test_weekday_cron_fires_on_the_right_korean_morning():
    """`5 0 * * 1-5`는 UTC 월~금 00:05 = 한국시간 평일 09:05."""
    # 2026-08-19는 수요일
    now = datetime(2026, 8, 19, 8, 0, tzinfo=KST)
    fire = next_fire("5 0 * * 1-5", now)
    assert fire == datetime(2026, 8, 19, 9, 5, tzinfo=KST)


def test_after_todays_run_it_points_at_tomorrow():
    now = datetime(2026, 8, 19, 10, 0, tzinfo=KST)  # 수요일 오전, 이미 지남
    fire = next_fire("5 0 * * 1-5", now)
    assert fire == datetime(2026, 8, 20, 9, 5, tzinfo=KST)


def test_friday_evening_skips_the_weekend():
    now = datetime(2026, 8, 21, 20, 0, tzinfo=KST)  # 금요일 저녁
    fire = next_fire("5 0 * * 1-5", now)
    assert fire.weekday() == 0, "다음은 월요일이어야 한다"
    assert fire == datetime(2026, 8, 24, 9, 5, tzinfo=KST)


def test_sunday_utc_becomes_monday_in_korea():
    """`0 15 * * 0`은 UTC 일요일 15:00 = 한국시간 월요일 00:00.

    요일까지 밀리는 경우다. cron 요일을 그대로 화면에 쓰면 '일요일'이라고
    잘못 안내하게 된다."""
    now = datetime(2026, 8, 19, 12, 0, tzinfo=KST)
    fire = next_fire("0 15 * * 0", now)
    assert fire == datetime(2026, 8, 24, 0, 0, tzinfo=KST)
    assert fire.weekday() == 0
    assert describe_cron("0 15 * * 0") == "매주 월 00:00"


def test_cron_weekday_numbering_is_not_pythons():
    """cron은 일요일이 0, 파이썬 weekday()는 월요일이 0이다.

    그대로 비교하면 하루씩 밀린다 — 조용히 틀리는 종류의 버그라 못 박아 둔다."""
    now = datetime(2026, 8, 19, 12, 0, tzinfo=KST)  # 수요일
    # cron 1 = 월요일 → UTC 월 03:00 = KST 월 12:00
    fire = next_fire("0 3 * * 1", now)
    assert fire.weekday() == 0


def test_describe_reads_in_korean_time():
    assert describe_cron("5 0 * * 1-5") == "평일 09:05"
    assert describe_cron("30 6 * * 1-5") == "평일 15:30"
    assert describe_cron("0 0 * * *") == "매일 09:00"


def test_a_malformed_cron_does_not_crash_the_screen():
    """워크플로를 잘못 고쳤을 때 화면 전체가 죽으면 안 된다."""
    assert next_fire("이건 cron이 아니다", datetime.now(KST)) is None
    assert describe_cron("*/5") == "*/5"


def test_it_reads_the_real_workflow_files():
    """시각을 화면에 손으로 적지 않는다는 것이 이 기능의 핵심이다.

    실제 파일을 안 읽고 상수를 쓰기 시작하면, 일정을 바꿨을 때 화면만
    옛 시각으로 남는다."""
    jobs = upcoming(datetime(2026, 8, 19, 8, 0, tzinfo=KST))
    assert jobs, "워크플로에서 cron을 하나도 못 읽었다"
    assert any(j.이름 == "자동매매" for j in jobs)
    for job in jobs:
        assert job.설명문, f"{job.이름}: 사람이 읽을 문장이 비었다"


def test_missing_workflow_directory_is_not_an_error(tmp_path: Path):
    assert upcoming(datetime.now(KST), workflow_dir=tmp_path) == []


def test_remaining_time_is_worded_by_size():
    now = datetime(2026, 8, 19, 8, 0, tzinfo=KST)
    jobs = upcoming(now)
    assert all(job.남은시간(now) for job in jobs)
