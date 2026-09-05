"""화면 저장소로 옮길 때 남의 파일을 조용히 지우지 않는가.

## 무엇이 문제였나 (2026-09-05)

옮기는 방법이 이랬다.

    git ls-files -z | xargs -0 rm -f
    git -C ../muwon406 archive HEAD | tar -x

화면 저장소를 통째로 비우고 매매 저장소를 푼다. **화면 저장소에만 있는
파일이 생기는 순간 조용히 사라진다.** 지금까지는 그런 파일이 없어서
우연히 안전했을 뿐이다.

주인이 "저장소를 같이 두면 다른 시스템이랑 엉키지 않느냐"고 물어서
확인하다 찾았다. 정기 실행은 저장소 조건으로 막혀 있어 안 엉키는데,
이 지우는 방식은 남아 있었다.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from publish_dashboard import 전용파일, 지울것정하기


def test_양쪽에_다_있으면_안_지운다():
    assert 지울것정하기(["a.py", "b.py"], ["a.py", "b.py"], ()) == []


def test_화면_저장소에만_있으면_알려_준다():
    """이것을 안 알려 주면 조용히 사라진다."""
    assert 지울것정하기(["a.py", "남은것.txt"], ["a.py"], ()) == ["남은것.txt"]


def test_매매_저장소에만_있는_것은_상관없다():
    """푸는 쪽에서 새로 생긴다. 지울 것이 아니다."""
    assert 지울것정하기(["a.py"], ["a.py", "새것.py"], ()) == []


def test_전용_파일로_적어_두면_봐준다():
    assert 지울것정하기(["a.py", "화면만.txt"], ["a.py"], ("화면만.txt",)) == []


def test_전용_파일은_glob으로_적을_수_있다():
    남는것 = ["docs/화면전용/하나.md", "docs/화면전용/둘.md", "몰래.txt"]
    나온것 = 지울것정하기(["a.py", *남는것], ["a.py"], ("docs/화면전용/*",))
    assert 나온것 == ["몰래.txt"]


def test_지금은_전용_파일이_비어_있다():
    """2026-09-05에 두 저장소를 견줘 보니 화면 저장소에만 있는 파일이
    하나도 없었다. 여기에 무엇을 더하는 것은 두 저장소를 갈라놓는 일이라
    한 번 물어야 한다."""
    assert 전용파일 == ()


def test_기본은_안_지우는_쪽이다():
    """실수로 도는 쪽이 아니라 실수로 안 도는 쪽으로 기울인다. 이 저장소가
    `switch-strategy.yml`에서 쓰는 것과 같은 규칙이다."""
    글 = (Path(__file__).resolve().parent.parent
          / "scripts" / "publish_dashboard.py").read_text(encoding="utf-8")
    assert "--지워도됨" in 글
    assert "if not 인자.지워도됨" in 글
    assert "return 1" in 글


def test_옛_방식을_문서가_더는_안_시킨다():
    """CLAUDE.md가 통째로 지우는 명령을 그대로 적고 있으면, 다음에 읽는
    사람이 스크립트 대신 그것을 그대로 친다."""
    글 = (Path(__file__).resolve().parent.parent
          / "CLAUDE.md").read_text(encoding="utf-8")
    assert "git ls-files -z | xargs -0 rm -f" not in 글
    assert "publish_dashboard.py" in 글
