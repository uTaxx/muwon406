"""Round 12 TASK 2 — Reference Library MVP 검증.

Architect Review Round 12 지시: "AI가 어떤 공개자료를 근거로 판단하는지 사용자가
쉽게 관리하고 확인할 수 있어야 한다." 새 Knowledge Engine이나 대형 Architecture가
아니라, 파일 위치(inbox/active/archive)와 최소 Metadata만으로 동작하는지 확인한다.
"""
from __future__ import annotations

import reference_library as rl


def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(rl, "project_root", lambda: tmp_path)
    rl.ensure_directories()
    return tmp_path


def test_ensure_directories_creates_four_folders(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    assert rl.inbox_dir().is_dir()
    assert rl.active_dir().is_dir()
    assert rl.archive_dir().is_dir()
    assert rl.index_dir().is_dir()


def test_scan_registers_new_files_with_honest_defaults(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    (rl.inbox_dir() / "report.pdf").write_text("fake", encoding="utf-8")
    (rl.active_dir() / "notes.md").write_text("# Notes", encoding="utf-8")

    result = rl.scan_and_register()
    assert result == {"total": 2, "added": 2}

    entries = {e["file_path"].split("/")[-1]: e for e in rl.load_index()}
    pdf_entry = entries["report.pdf"]
    assert pdf_entry["status"] == "unclassified"
    assert pdf_entry["document_type"] == "other"
    assert pdf_entry["reliability_grade"] == "C"  # 보수적 기본값 — 임의로 높은 등급 부여 금지
    assert pdf_entry["parseable"] is False  # PDF는 이번 Round Parsing 미지원

    md_entry = entries["notes.md"]
    assert md_entry["status"] == "active"
    assert md_entry["parseable"] is True


def test_unsupported_extension_is_not_auto_registered(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    (rl.inbox_dir() / "ignored.xyz").write_text("nope", encoding="utf-8")

    result = rl.scan_and_register()
    assert result == {"total": 0, "added": 0}


def test_rescan_is_idempotent(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    (rl.inbox_dir() / "report.pdf").write_text("fake", encoding="utf-8")

    rl.scan_and_register()
    result = rl.scan_and_register()
    assert result == {"total": 1, "added": 0}  # 재실행해도 중복 등록 없음


def test_moving_file_between_folders_preserves_user_edited_metadata(tmp_path, monkeypatch):
    """완료조건과 동일한 정신: 사용자가 inbox에서 분류한 뒤 active로 옮겨도(Pilot의
    승격 워크플로우) 이미 채워 넣은 Metadata(회사/자료유형/등급)를 잃지 않아야 한다."""
    _isolate(tmp_path, monkeypatch)
    (rl.inbox_dir() / "annual.pdf").write_text("fake", encoding="utf-8")
    rl.scan_and_register()

    entries = rl.load_index()
    entries[0]["company"] = "LX_HAUSYS"
    entries[0]["document_type"] = "annual_report"
    entries[0]["reliability_grade"] = rl.reliability_grade_for("annual_report")
    rl.save_index(entries)

    (rl.inbox_dir() / "annual.pdf").rename(rl.active_dir() / "annual.pdf")
    result = rl.scan_and_register()

    assert result["added"] == 0  # 새 항목이 아니라 기존 항목이 이동한 것으로 인식
    entries = rl.load_index()
    assert len(entries) == 1
    assert entries[0]["status"] == "active"
    assert entries[0]["company"] == "LX_HAUSYS"
    assert entries[0]["document_type"] == "annual_report"
    assert entries[0]["reliability_grade"] == "A"


def test_ambiguous_same_basename_move_registers_as_new_instead_of_guessing(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    (rl.inbox_dir() / "dup.pdf").write_text("a", encoding="utf-8")
    rl.scan_and_register()

    # 이미 사라진 파일을 가리키는 stale 항목을 하나 더 인위적으로 추가한다(예: 사용자가
    # 예전에 지운 자료의 색인 흔적이 남아 있는 상황) — 이제 basename "dup.pdf"를 가리키는
    # stale 후보가 2개가 된다.
    entries = rl.load_index()
    fabricated = dict(entries[0])
    fabricated["reference_id"] = "REF-9999"
    fabricated["file_path"] = "reference_library/archive/dup.pdf"  # 실제로는 존재하지 않음
    entries.append(fabricated)
    rl.save_index(entries)

    (rl.inbox_dir() / "dup.pdf").rename(rl.active_dir() / "dup.pdf")
    result = rl.scan_and_register()

    # stale 후보가 2개(원래 inbox 항목 + 인위적으로 추가한 항목)라 어느 쪽이 이동한
    # 것인지 애매하므로, 잘못 추측하지 않고 active/dup.pdf를 새 항목으로 등록해야 한다.
    assert result["added"] == 1
    assert len(rl.load_index()) == 3


def test_list_active_references_for_company_filters_and_sorts_by_grade(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    entries = [
        {
            "reference_id": "REF-0001", "title": "B등급 문서", "company": "LX_HAUSYS",
            "document_type": "research_report", "source_type": "research", "source_url": None,
            "file_path": None, "published_date": None, "added_at": "2026-08-01T00:00:00Z",
            "official_source": False, "reliability_grade": "B", "status": "active",
            "latest_version": True, "applicable_services": [], "last_verified": None,
        },
        {
            "reference_id": "REF-0002", "title": "A등급 문서", "company": "LX_HAUSYS",
            "document_type": "annual_report", "source_type": "official_company", "source_url": None,
            "file_path": None, "published_date": None, "added_at": "2026-08-02T00:00:00Z",
            "official_source": True, "reliability_grade": "A", "status": "active",
            "latest_version": True, "applicable_services": [], "last_verified": None,
        },
        {
            "reference_id": "REF-0003", "title": "미분류 상태 문서", "company": "LX_HAUSYS",
            "document_type": "other", "source_type": "user_upload", "source_url": None,
            "file_path": None, "published_date": None, "added_at": "2026-08-03T00:00:00Z",
            "official_source": False, "reliability_grade": "C", "status": "unclassified",
            "latest_version": True, "applicable_services": [], "last_verified": None,
        },
        {
            "reference_id": "REF-0004", "title": "다른 회사 문서", "company": "KCC",
            "document_type": "annual_report", "source_type": "official_company", "source_url": None,
            "file_path": None, "published_date": None, "added_at": "2026-08-04T00:00:00Z",
            "official_source": True, "reliability_grade": "A", "status": "active",
            "latest_version": True, "applicable_services": [], "last_verified": None,
        },
    ]
    rl.save_index(entries)

    refs = rl.list_active_references_for_company("LX_HAUSYS")
    assert [r["reference_id"] for r in refs] == ["REF-0002", "REF-0001"]  # A등급 우선, unclassified/타사 제외


def test_list_active_references_for_company_returns_empty_without_company_id():
    assert rl.list_active_references_for_company(None) == []
    assert rl.list_active_references_for_company("") == []


def test_reference_citation_rows_minimal_display_fields():
    entries = [{
        "title": "문서 A", "document_type": "annual_report", "published_date": "2024-05-01",
        "source_url": "https://example.com/a", "file_path": None, "reliability_grade": "A",
    }]
    rows = rl.reference_citation_rows(entries)
    assert rows == [{
        "문서명": "문서 A", "자료유형": "annual_report", "발행일": "2024-05-01",
        "Source URL / 파일 경로": "https://example.com/a", "신뢰도": "A",
    }]


def test_reference_citation_rows_empty_list_when_no_references():
    assert rl.reference_citation_rows([]) == []


def test_url_registry_manifest_registers_without_crawling(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    manifest = rl.inbox_dir() / "url_registry.yaml"
    manifest.write_text(
        "urls:\n"
        "  - title: LX Hausys 지속가능경영보고서 2024\n"
        "    url: https://example.com/lx-hausys-2024.html\n"
        "    company: LX_HAUSYS\n"
        "    document_type: sustainability_report\n"
        "    published_date: '2024-05-01'\n",
        encoding="utf-8",
    )

    result = rl.scan_and_register()
    assert result == {"total": 1, "added": 1}

    entries = rl.load_index()
    assert entries[0]["source_url"] == "https://example.com/lx-hausys-2024.html"
    assert entries[0]["file_path"] is None
    assert entries[0]["reliability_grade"] == "A"  # sustainability_report -> A
    assert entries[0]["status"] == "active"


def test_reference_library_summary_counts(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    (rl.inbox_dir() / "a.pdf").write_text("x", encoding="utf-8")
    (rl.active_dir() / "b.md").write_text("y", encoding="utf-8")
    rl.scan_and_register()

    entries = rl.load_index()
    entries[1]["company"] = "LX_HAUSYS"
    entries[1]["official_source"] = True
    rl.save_index(entries)

    summary = rl.reference_library_summary()
    assert summary["total"] == 2
    assert summary["active_count"] == 1
    assert summary["unclassified_count"] == 1
    assert summary["by_company"] == {"LX_HAUSYS": 1}
    assert summary["official_count"] == 1


def test_reliability_grade_for_document_types():
    assert rl.reliability_grade_for("annual_report") == "A"
    assert rl.reliability_grade_for("government") == "A"
    assert rl.reliability_grade_for("research_report") == "B"
    assert rl.reliability_grade_for("other") == "C"
    assert rl.reliability_grade_for("unknown_type_not_in_table") == "C"  # 보수적 기본값


def test_save_index_rejects_entry_that_fails_schema_validation(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    import pytest
    from jsonschema import ValidationError

    bad_entry = {"reference_id": "REF-0001", "title": "누락된 필수 필드 있음"}
    with pytest.raises(ValidationError):
        rl.save_index([bad_entry])
