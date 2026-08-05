"""Knowledge Retrieve 단계 — 관련 LX 계열사 Knowledge 문서를 읽어 Analyze 단계에 넘길 발췌를
만든다.

CLAUDE.md의 Knowledge 파일 우선순위(Architect Review Round 2 Q6)를 따른다:
LX_HAUSYS_COMPANY_DNA → LX_HAUSYS_VALUE_CHAIN → GROUP_RISK_MAP → GROUP_OPPORTUNITY_MAP →
STRATEGY_PLAYBOOK → LX_HOLDINGS_CONTEXT → PLATFORM_CONSTITUTION.

전체 Knowledge Base를 매번 Claude에 보내지 않기 위해 `claude_client.clip_context()`로 길이를
제한한다 — semantic search 등 정교한 발췌 선택은 Pilot 이후 확장 대상이다.
"""
from __future__ import annotations

import re

from _common import project_root

KNOWLEDGE_DIR = project_root() / "knowledge"

# 회사별로 참고할 Knowledge 문서 (우선순위 순). Pilot 범위상 LX_HAUSYS만 채워져 있다 —
# 다른 계열사가 추가되면 이 매핑만 확장하면 된다.
COMPANY_KNOWLEDGE_FILES: dict[str, list[str]] = {
    "LX_HAUSYS": [
        "LX_HAUSYS_COMPANY_DNA.md",
        "LX_HAUSYS_VALUE_CHAIN.md",
        "GROUP_RISK_MAP.md",
        "GROUP_OPPORTUNITY_MAP.md",
        "STRATEGY_PLAYBOOK.md",
        "LX_HOLDINGS_CONTEXT.md",
        "PLATFORM_CONSTITUTION.md",
    ],
}

_VERSION_RE = re.compile(r"^version:\s*(?P<version>\S+)\s*$", re.MULTILINE)


def _file_version(text: str) -> str:
    match = _VERSION_RE.search(text)
    return match.group("version") if match else "unknown"


def retrieve_context(related_lx_companies: list[str], max_chars: int = 6000) -> tuple[str, str]:
    """(lx_context_excerpt, knowledge_version) 튜플을 반환한다.

    knowledge_version은 `<파일명>@<버전>` 형식을 세미콜론으로 이어붙인 문자열로, 이 Intelligence
    레코드가 어떤 Knowledge 스냅샷을 근거로 생성됐는지 추적 가능하게 한다.
    """
    files_used: list[str] = []
    for company in related_lx_companies:
        for filename in COMPANY_KNOWLEDGE_FILES.get(company, []):
            if filename not in files_used:
                files_used.append(filename)

    excerpts: list[str] = []
    versions: list[str] = []
    for filename in files_used:
        path = KNOWLEDGE_DIR / filename
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        versions.append(f"{filename}@{_file_version(text)}")
        excerpts.append(f"### {filename}\n\n{text}")

    from claude_client import clip_context

    full_context = "\n\n---\n\n".join(excerpts)
    return clip_context(full_context, max_chars), ";".join(versions)
