from datetime import date

import knowledge_engine as ke


def test_parse_knowledge_sections_reads_real_company_dna_file():
    sections = ke.parse_knowledge_sections("LX_HAUSYS_COMPANY_DNA.md")
    assert len(sections) == 12
    assert sections[0].section_number == 1
    assert "Company" in sections[0].section_title
    assert sections[0].file == "LX_HAUSYS_COMPANY_DNA.md"
    assert sections[0].company == "LX Hausys"


def test_parse_knowledge_sections_handles_section_with_no_metadata_block():
    """섹션에 Source/Confidence 메타데이터 블록이 아예 없어도 예외 없이 빈 문자열로
    처리되어야 한다 (Round 6 TASK-K01 리서치 반영 전에는 LX_HAUSYS_VALUE_CHAIN.md 전체가
    이 상태였다 — 이제는 실제 콘텐츠가 채워졌으므로, 이 엣지 케이스는 합성 텍스트로
    직접 검증한다)."""
    # parse_knowledge_sections()는 파일명을 받으므로, 메타데이터 추출 로직 자체를 직접 검증한다.
    source, url, confidence, last_verified = ke.extract_section_metadata(
        "아직 메타데이터가 없는 섹션 본문.\n"
    )
    assert (source, url, confidence, last_verified) == ("", "", "", "")


def test_parse_knowledge_sections_reads_real_value_chain_file_with_populated_metadata():
    """Round 6 TASK-K01 리서치 반영 후: LX_HAUSYS_VALUE_CHAIN.md는 이제 실제 Source/
    Confidence 메타데이터를 갖는다."""
    sections = ke.parse_knowledge_sections("LX_HAUSYS_VALUE_CHAIN.md")
    assert len(sections) >= 1
    assert sections[0].source != ""
    assert sections[0].source_reliability_score >= 0


def test_extract_section_metadata_supports_inline_and_four_line_formats():
    inline = "- Source: DART / Reference URL: https://x / Confidence: high / Last Verified: 2026-08-01\n"
    four_line = (
        "- Source: DART\n- Reference URL: https://x\n- Confidence: high\n"
        "- Last Verified: 2026-08-01\n"
    )
    assert ke.extract_section_metadata(inline) == ("DART", "https://x", "high", "2026-08-01")
    assert ke.extract_section_metadata(four_line) == ("DART", "https://x", "high", "2026-08-01")


def test_extract_section_metadata_returns_empty_when_no_metadata():
    assert ke.extract_section_metadata("그냥 본문 텍스트") == ("", "", "", "")


def test_search_by_section_matches_title_substring():
    results = ke.search_by_section("Risk", sections=ke.parse_knowledge_sections("LX_HAUSYS_COMPANY_DNA.md"))
    assert len(results) == 1
    assert results[0].section_number == 10


def test_search_by_section_matches_number():
    results = ke.search_by_section("10", sections=ke.parse_knowledge_sections("LX_HAUSYS_COMPANY_DNA.md"))
    assert len(results) == 1
    assert "Risk" in results[0].section_title


def test_search_by_company_returns_sections_from_mapped_files():
    from pipeline.knowledge_retrieve import COMPANY_KNOWLEDGE_FILES

    results = ke.search_by_company("LX_HAUSYS")
    assert len(results) > 0
    result_files = {r.file for r in results}
    assert result_files <= set(COMPANY_KNOWLEDGE_FILES["LX_HAUSYS"])
    assert "LX_HAUSYS_COMPANY_DNA.md" in result_files


def test_search_by_company_unknown_company_returns_empty():
    assert ke.search_by_company("UNKNOWN_CO") == []


def test_search_by_topic_resolves_via_related_lx_companies():
    results = ke.search_by_topic("TOP-0001")
    assert len(results) > 0


def test_search_by_topic_unknown_topic_returns_empty():
    assert ke.search_by_topic("TOP-9999") == []


def test_search_by_source_priority_filters_by_score():
    sections = [
        ke.KnowledgeSection("f.md", None, 1, "A", "", "government", "", "high", "2026-08-01", 5),
        ke.KnowledgeSection("f.md", None, 2, "B", "", "blog", "", "high", "2026-08-01", 2),
    ]
    results = ke.search_by_source_priority(4, sections=sections)
    assert len(results) == 1
    assert results[0].section_title == "A"


def test_search_by_confidence_treats_na_as_high():
    sections = [
        ke.KnowledgeSection("f.md", None, 1, "A", "", "", "", "N/A", "", 0),
        ke.KnowledgeSection("f.md", None, 2, "B", "", "", "", "draft", "", 0),
    ]
    results = ke.search_by_confidence("high", sections=sections)
    assert [s.section_title for s in results] == ["A"]


def test_search_by_last_verified_excludes_unparseable_dates():
    sections = [
        ke.KnowledgeSection("f.md", None, 1, "Fresh", "", "", "", "high", "2026-08-01", 0),
        ke.KnowledgeSection("f.md", None, 2, "Old", "", "", "", "high", "2020-01-01", 0),
        ke.KnowledgeSection("f.md", None, 3, "Unverified", "", "", "", "draft", "(미확인)", 0),
    ]
    results = ke.search_by_last_verified(date(2026, 1, 1), sections=sections)
    assert [s.section_title for s in results] == ["Fresh"]
