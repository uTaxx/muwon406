"""Knowledge Retrieval Engine — Architect Review Round 5 (TASK-009B).

Round 4까지 `pipeline/knowledge_retrieve.py`는 "회사와 관련된 Knowledge 파일 전체를 읽어서
발췌"하는 문서 읽기 수준이었다. Round 5 지시("Knowledge는 문서가 아니라 검색 가능한
데이터가 되어야 한다")에 따라, knowledge/*.md를 Section 단위 레코드로 파싱하고
Section/Topic/Company/Source Priority/Confidence/Last Verified 기준으로 검색할 수 있게
한다. `pipeline/knowledge_retrieve.py`(LLM에 넘길 발췌 생성)는 이 엔진 위에서 계속 동작하며,
이 모듈은 그보다 세분화된 조회를 제공한다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime

from _common import load_yaml, project_root
from source_priority import score_for_source_type

KNOWLEDGE_DIR = project_root() / "knowledge"

SECTION_HEADER_RE = re.compile(r"^## (\d+)\. ([^\n]+)$", re.MULTILINE)

# knowledge/*.md는 실제로 두 가지 메타데이터 서식이 섞여 있다:
#   (a) 한 줄 "/" 구분 — LX_HOLDINGS_CONTEXT.md
#       "- Source: X / Reference URL: Y / Confidence: Z / Last Verified: W"
#   (b) 4줄 분리 — LX_HAUSYS_COMPANY_DNA.md, LX_HAUSYS_VALUE_CHAIN.md 등
#       "- Source: X\n- Reference URL: Y\n- Confidence: Z\n- Last Verified: W"
# 이 엔진은 둘 다 파싱한다 — (a)만 지원하던 옛 정규식(scripts/knowledge_quality.py)은
# (b) 서식의 문서를 전부 "메타데이터 없음"으로 오판정했었다(예: COMPANY_DNA.md가 항상
# Quality Score 0%로 나온 원인). knowledge_quality.py도 이 모듈의 파서를 재사용하도록
# 함께 고쳤다.
INLINE_METADATA_RE = re.compile(
    r"-\s*Source:\s*(?P<source>.*?)\s*/\s*Reference URL:\s*(?P<url>.*?)\s*/\s*"
    r"Confidence:\s*(?P<confidence>.*?)\s*/\s*Last Verified:\s*(?P<last_verified>.*?)\s*$",
    re.MULTILINE,
)
SOURCE_LINE_RE = re.compile(r"^-\s*Source:\s*(?P<value>.*?)\s*$", re.MULTILINE)
REFERENCE_URL_LINE_RE = re.compile(r"^-\s*Reference URL:\s*(?P<value>.*?)\s*$", re.MULTILINE)
CONFIDENCE_LINE_RE = re.compile(r"^-\s*Confidence:\s*(?P<value>.*?)\s*$", re.MULTILINE)
LAST_VERIFIED_LINE_RE = re.compile(r"^-\s*Last Verified:\s*(?P<value>.*?)\s*$", re.MULTILINE)

# N/A는 knowledge/KNOWLEDGE_POLICY.md 정책상 "확인할 필요 자체가 없는 계층"이라 최고
# 신뢰 등급(high)과 동일하게 취급한다(scripts/knowledge_quality.py의 기존 규칙과 동일).
CONFIDENCE_RANK = {"n/a": 3, "high": 3, "medium": 2, "low": 1, "draft": 0}


@dataclass(frozen=True)
class KnowledgeSection:
    file: str
    company: str | None
    section_number: int
    section_title: str
    content: str
    source: str
    reference_url: str
    confidence: str
    last_verified: str
    source_reliability_score: int


def extract_frontmatter_field(text: str, field: str) -> str | None:
    for line in text.splitlines():
        if line.strip().startswith(f"{field}:"):
            value = line.split(":", 1)[1].strip()
            return value or None
    return None


def extract_section_metadata(section_text: str) -> tuple[str, str, str, str]:
    """(source, reference_url, confidence, last_verified)를 반환한다.

    한 줄 "/" 구분 서식을 먼저 시도하고, 없으면 4줄 분리 서식을 시도한다. 둘 다 없으면
    빈 문자열 4개를 반환한다(예: LX_HAUSYS_VALUE_CHAIN.md처럼 섹션에 메타데이터 블록
    자체가 아직 없는 경우).
    """
    inline_match = None
    for inline_match in INLINE_METADATA_RE.finditer(section_text):
        pass  # 섹션 내 마지막 매치를 사용
    if inline_match is not None:
        return (
            inline_match.group("source"),
            inline_match.group("url"),
            inline_match.group("confidence"),
            inline_match.group("last_verified"),
        )

    def _last(pattern: re.Pattern) -> str:
        matches = list(pattern.finditer(section_text))
        return matches[-1].group("value") if matches else ""

    return (
        _last(SOURCE_LINE_RE),
        _last(REFERENCE_URL_LINE_RE),
        _last(CONFIDENCE_LINE_RE),
        _last(LAST_VERIFIED_LINE_RE),
    )


def parse_knowledge_sections(filename: str) -> list[KnowledgeSection]:
    """knowledge/<filename>을 Section(`## N. 제목`) 단위 레코드로 파싱한다."""
    text = (KNOWLEDGE_DIR / filename).read_text(encoding="utf-8")
    company = extract_frontmatter_field(text, "company")
    headers = list(SECTION_HEADER_RE.finditer(text))
    sections = []
    for i, match in enumerate(headers):
        number = int(match.group(1))
        title = match.group(2).strip()
        start = match.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        section_text = text[start:end]

        content = section_text.split("\n- Source:")[0].strip()
        source, url, confidence, last_verified = extract_section_metadata(section_text)

        sections.append(
            KnowledgeSection(
                file=filename,
                company=company,
                section_number=number,
                section_title=title,
                content=content,
                source=source,
                reference_url=url,
                confidence=confidence,
                last_verified=last_verified,
                source_reliability_score=score_for_source_type(source) if source else 0,
            )
        )
    return sections


def _company_knowledge_files() -> dict[str, list[str]]:
    # 회사→Knowledge 파일 매핑은 pipeline/knowledge_retrieve.py가 단일 진실 공급원이다 —
    # 여기서 다시 정의하지 않고 재사용한다.
    from pipeline.knowledge_retrieve import COMPANY_KNOWLEDGE_FILES

    return COMPANY_KNOWLEDGE_FILES


def all_sections(files: list[str] | None = None) -> list[KnowledgeSection]:
    """files를 지정하지 않으면 회사 매핑에 등록된 모든 Knowledge 파일을 대상으로 한다."""
    if files is None:
        mapping = _company_knowledge_files()
        seen: list[str] = []
        for filelist in mapping.values():
            for f in filelist:
                if f not in seen:
                    seen.append(f)
        files = seen

    sections: list[KnowledgeSection] = []
    for filename in files:
        if (KNOWLEDGE_DIR / filename).exists():
            sections.extend(parse_knowledge_sections(filename))
    return sections


def search_by_section(query: str, sections: list[KnowledgeSection] | None = None) -> list[KnowledgeSection]:
    """Section 번호(예: "5") 또는 제목 일부(예: "Risk")로 검색한다."""
    sections = sections if sections is not None else all_sections()
    query_lower = query.strip().lower()
    return [
        s
        for s in sections
        if query_lower in s.section_title.lower()
        or (query_lower.isdigit() and int(query_lower) == s.section_number)
    ]


def search_by_company(company_id: str) -> list[KnowledgeSection]:
    files = _company_knowledge_files().get(company_id, [])
    return all_sections(files)


def search_by_topic(topic_id: str) -> list[KnowledgeSection]:
    """config/topics.yaml의 related_lx_companies를 통해 Topic → 관련 회사 → Knowledge
    Section으로 연결한다."""
    topics = load_yaml("config/topics.yaml")["topics"]
    topic = next((t for t in topics if t["topic_id"] == topic_id), None)
    if topic is None:
        return []
    sections: list[KnowledgeSection] = []
    for company_id in topic.get("related_lx_companies", []):
        sections.extend(search_by_company(company_id))
    return sections


def search_by_source_priority(
    min_score: int, sections: list[KnowledgeSection] | None = None
) -> list[KnowledgeSection]:
    """Source Reliability Score(1~5)가 min_score 이상인 Section만 반환한다."""
    sections = sections if sections is not None else all_sections()
    return [s for s in sections if s.source_reliability_score >= min_score]


def search_by_confidence(
    min_confidence: str, sections: list[KnowledgeSection] | None = None
) -> list[KnowledgeSection]:
    """min_confidence(low/medium/high) 이상인 Section만 반환한다. N/A는 high와 동급으로
    취급한다(knowledge/KNOWLEDGE_POLICY.md 기존 정책과 동일)."""
    sections = sections if sections is not None else all_sections()
    threshold = CONFIDENCE_RANK.get(min_confidence.strip().lower(), 0)
    return [s for s in sections if CONFIDENCE_RANK.get(s.confidence.strip().lower(), 0) >= threshold]


def search_by_last_verified(
    after: date, sections: list[KnowledgeSection] | None = None
) -> list[KnowledgeSection]:
    """after 날짜 이후에 검증된(Last Verified) Section만 반환한다. 날짜 형식이 아니거나
    미확인인 Section은 제외한다(임의로 최신으로 간주하지 않는다)."""
    sections = sections if sections is not None else all_sections()
    result = []
    for s in sections:
        try:
            verified_date = datetime.strptime(s.last_verified.strip(), "%Y-%m-%d").date()
        except ValueError:
            continue
        if verified_date >= after:
            result.append(s)
    return result
