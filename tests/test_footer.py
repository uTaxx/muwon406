"""모든 텔레그램 글 아래에 붙는 대시보드 링크.

"항상 달려 있다"가 약속이라, 조용히 빠지는 경우가 없어야 한다."""

from muwon.notify import footer


def test_글_아래에_링크가_붙는다():
    결과 = footer.붙이기("오늘 2종목 샀습니다")

    assert 결과.startswith("오늘 2종목 샀습니다")
    assert 결과.rstrip().endswith(footer.주소())
    assert footer.이름 in 결과


def test_여러_번_붙여도_링크는_하나():
    """버튼을 누르면 이미 링크가 붙은 글을 통째로 갈아 끼운다 —
    떼지 않고 붙이면 누를 때마다 한 줄씩 쌓인다."""
    한번 = footer.붙이기("후보 3종목")
    세번 = footer.붙이기(footer.붙이기(한번))

    assert 세번 == 한번
    assert 세번.count(footer.표시) == 1


def test_한도를_넘으면_링크가_아니라_본문을_줄인다():
    """링크가 빠지면 약속이 조용히 깨진다. 잘린 본문은 눈에 보이지만
    없는 링크는 안 보인다."""
    결과 = footer.붙이기("가" * 5000, 한도=200)

    assert len(결과) <= 200
    assert 결과.rstrip().endswith(footer.주소())
    assert "…" in 결과


def test_주소는_환경변수로_갈아_끼울_수_있다(monkeypatch):
    """배포 주소는 우리가 정하는 값이 아니라, 코드를 안 고치고 바꿔야 한다."""
    monkeypatch.setenv("MUWON_DASHBOARD_URL", "https://예시.example")

    assert footer.주소() == "https://예시.example"
    assert "https://예시.example" in footer.붙이기("아무 글")


def test_빈_환경변수는_기본주소로_돌아간다(monkeypatch):
    """워크플로에서 빈 값이 넘어오는 일이 흔하다 — 그때 주소가 사라지면 안 된다."""
    monkeypatch.setenv("MUWON_DASHBOARD_URL", "   ")

    assert footer.주소() == footer.기본주소


def test_링크가_없는_글에서_떼면_그대로():
    assert footer.떼기("아무 글") == "아무 글"


def test_버튼을_눌러_글을_갈아_끼워도_링크가_남는다():
    """버튼 누름 → 상태 블록 교체 → 다시 보내기 흐름 전체를 태워 본다.

    상태 블록을 갈아 끼울 때 '상태표시 앞부분'만 남기는데, 링크는 그
    뒤에 있어서 같이 떨어져 나간다. 내보내는 쪽에서 다시 붙이지 않으면
    **버튼을 한 번 누르는 순간 링크가 조용히 사라진다.**"""
    from muwon.notify.telegram_buttons import 글에_상태붙이기, 버튼항목

    후보 = [버튼항목(symbol="403870", name="HPSP")]
    보낸글 = footer.붙이기("■ 매수 후보 1종목\n- HPSP")

    갈아낀글 = 글에_상태붙이기(보낸글, 후보, {"403870": "Y"})
    assert footer.표시 not in 갈아낀글  # 여기서는 떨어져 나간 상태다

    내보낼글 = footer.붙이기(갈아낀글)  # telegram_api.edit_text가 하는 일
    assert 내보낼글.rstrip().endswith(footer.주소())
    assert 내보낼글.count(footer.표시) == 1
    assert "HPSP" in 내보낼글
