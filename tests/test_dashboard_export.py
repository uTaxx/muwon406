"""뽑아 둔 JSON이 파이썬 원본과 어긋나지 않는지 본다.

원본(`glossary.py`·`strategy_rules.py`)을 고치고 JSON을 다시 안 뽑으면
**화면은 옛 설명을 계속 보여 준다.** 조용히 틀리는 쪽이라 막아야 한다.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

뿌리 = Path(__file__).resolve().parent.parent
자료 = 뿌리 / "dashboard" / "자료"


def test_뽑아둔_자료가_파이썬_원본과_같다():
    """다르면 `python scripts/export_dashboard_data.py`를 돌리고 같이 커밋한다."""
    끝난것 = subprocess.run(
        [sys.executable, "scripts/export_dashboard_data.py", "--check"],
        cwd=뿌리, capture_output=True, text=True, check=False,
    )
    assert 끝난것.returncode == 0, 끝난것.stderr


def test_용어사전이_비어_있지_않다():
    낱말들 = json.loads((자료 / "용어사전.json").read_text(encoding="utf-8"))
    assert len(낱말들) >= 30
    # 뜻만 있고 읽는법이 없으면 "그래서 뭘 판단하나"를 알 수 없다.
    # 이 저장소가 용어를 다루는 방식이 그것이라 화면에서도 지킨다.
    빠진것 = [ㄴ["이름"] for ㄴ in 낱말들 if not ㄴ["읽는법"].strip()]
    assert not 빠진것, f"읽는 법이 없는 용어: {빠진것}"


def test_전략설명에_산다_규칙이_있다():
    전략들 = json.loads((자료 / "전략설명.json").read_text(encoding="utf-8"))
    assert len(전략들) >= 20
    설명없음 = [ㅈ["키"] for ㅈ in 전략들 if not ㅈ["설명있음"]]
    # 설명이 없는 전략이 있어도 막지는 않는다 — 다만 몇 개인지는 보이게 둔다.
    assert len(설명없음) <= len(전략들) // 2, f"설명 없는 전략이 너무 많다: {설명없음}"
