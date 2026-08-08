"""Reference Library MVP — Architect Review Round 12 TASK 2.

목적("AI가 어떤 공개자료를 근거로 판단하는지 사용자가 쉽게 관리하고 확인할 수 있어야
한다")을 Pilot 최소 기능으로 구현한다. 지시대로 기존 Knowledge Engine
(`scripts/knowledge_engine.py`, Knowledge Base *.md 문서 전용)을 대체하지 않고, 새로운
대형 Architecture(Embedding/Vector DB/RAG Server/Semantic Search)도 만들지 않는다 —
파일이 물리적으로 어느 폴더(inbox/active/archive)에 있는지와 최소 Metadata만으로
동작하는 얕은 카탈로그다.

**읽기 전용 스캔 원칙**: `scan_and_register()`는 사용자의 파일을 옮기거나 지우지
않는다(위험한 파일시스템 변경 회피). `inbox/`=아직 분류 전, `active/`=AI가 참고
가능, `archive/`=보관 — 이 분류는 사용자가 파일을 직접 폴더 간 이동시켜 관리하고,
Pilot은 그 위치를 읽어 `status`만 반영한다.

Metadata는 `schemas/reference_metadata.schema.json`으로 검증한다. `reliability_grade`
(A/B/C)는 새 척도가 아니라 `knowledge/SOURCE_PRIORITY.md`가 이미 정의한 축을 그대로
재사용한다 — `document_type`에서 결정론적으로 도출한다(`DOCUMENT_TYPE_GRADE`). 미분류
자료(`document_type: other`, 대부분의 자동 등록 직후 상태)는 Round 12 Source Priority가
가장 낮게 두는 "User Upload"에 해당하므로 보수적으로 C등급을 받는다 — 사용자가 자료를
검토하고 `document_type`을 구체화하면(예: annual_report) 등급도 함께 올라간다.

PDF/DOCX/XLSX/PPTX는 이번 Round에서 텍스트를 파싱하지 않는다(`parseable: False`) —
"등록됨 / Parsing 미지원"으로 정직하게 표시한다. Markdown/TXT만 향후 실제 텍스트 발췌가
가능하다(`parseable: True`, 발췌 자체는 이번 Round 범위 밖).

디렉터리 경로는 `project_root()`를 매 호출마다 다시 읽는 함수로 제공한다(모듈 import
시점에 고정하지 않음) — 다른 Scenario 모듈들과 동일하게, 테스트가
`monkeypatch.setattr(reference_library, "project_root", lambda: tmp_path)`로 격리된
디렉터리를 주입할 수 있게 하기 위해서다.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import yaml
from _common import project_root
from jsonschema import validate as jsonschema_validate

# 스키마는 코드베이스의 일부라 실행 시점의 실제 project_root에 고정한다(모듈 import
# 시점 1회 계산) — 아래 디렉터리 함수들처럼 매 호출마다 `project_root()`를 다시 읽지
# 않는다. reference_library 데이터 자체(inbox/active/archive/index)만 테스트에서
# `project_root`를 monkeypatch해 격리된 tmp 디렉터리로 옮길 수 있으면 된다.
_SCHEMA_PATH = project_root() / "schemas" / "reference_metadata.schema.json"

_STATUS_BY_DIR = {"inbox": "unclassified", "active": "active", "archive": "archived"}

# Round 12 지원 대상("PDF/DOCX/XLSX/PPTX/Markdown/TXT/URL Registry"). URL Registry는
# 파일이 아니라 `inbox/url_registry.yaml` 매니페스트로 별도 처리한다(_scan_url_registry).
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".pptx", ".md", ".txt"}
PARSEABLE_EXTENSIONS = {".md", ".txt"}

DEFAULT_DOCUMENT_TYPE = "other"
DEFAULT_SOURCE_TYPE = "user_upload"

# document_type -> reliability_grade(A/B/C). SOURCE_PRIORITY.md Grade A 목록(공식
# 홈페이지/사업보고서/지속가능경영보고서/DART/IR/공식 보도자료/정부자료)과 1:1 대응시켰다.
# research_report는 2차 해석 자료라 Grade B(신뢰할 수 있는 언론과 동급)로 두고,
# 미분류(other, User Upload 기본값)는 "임의로 높은 등급을 주지 않는다"는 기존 원칙
# (source_reliability.yaml의 default_score와 동일한 보수적 태도)에 따라 C로 둔다.
DOCUMENT_TYPE_GRADE: dict[str, str] = {
    "official_website": "A",
    "annual_report": "A",
    "sustainability_report": "A",
    "ir_material": "A",
    "company_brochure": "A",
    "disclosure": "A",
    "government": "A",
    "press_release": "A",
    "research_report": "B",
    "other": "C",
}


def library_dir() -> Path:
    return project_root() / "reference_library"


def inbox_dir() -> Path:
    return library_dir() / "inbox"


def active_dir() -> Path:
    return library_dir() / "active"


def archive_dir() -> Path:
    return library_dir() / "archive"


def index_dir() -> Path:
    return library_dir() / "index"


def index_file() -> Path:
    return index_dir() / "reference_index.yaml"


def ensure_directories() -> None:
    for directory in (inbox_dir(), active_dir(), archive_dir(), index_dir()):
        directory.mkdir(parents=True, exist_ok=True)


def load_index() -> list[dict]:
    path = index_file()
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return list(data.get("references", []))


def validate_reference_entry(entry: dict) -> None:
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema_validate(instance=entry, schema=schema)


def save_index(entries: list[dict]) -> None:
    ensure_directories()
    for entry in entries:
        validate_reference_entry(entry)
    index_file().write_text(
        yaml.safe_dump({"references": entries}, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def reliability_grade_for(document_type: str) -> str:
    return DOCUMENT_TYPE_GRADE.get(document_type, "C")


def _next_reference_id(entries: list[dict]) -> str:
    max_n = 0
    for entry in entries:
        rid = entry.get("reference_id", "")
        if rid.startswith("REF-"):
            try:
                max_n = max(max_n, int(rid.split("-")[1]))
            except (IndexError, ValueError):
                continue
    return f"REF-{max_n + 1:04d}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _scan_folders(entries: list[dict]) -> int:
    """inbox/active/archive에 실제로 존재하는 파일을 인식해 새 항목만 등록하고, 이미
    등록된 파일은 폴더 위치에 따라 `status`만 갱신한다(다른 필드는 사용자가 채운 값을
    덮어쓰지 않는다). 반환값은 새로 추가한 건수.

    사용자가 검토를 마친 자료를 inbox/에서 active/로 물리적으로 옮기는 것이 이 Pilot의
    승격 워크플로우다(모듈 docstring 참고) — 그래서 파일이 옮겨진 경우, 원래 경로에
    등록됐던 Metadata(사용자가 채워 둔 company/document_type 등)를 잃지 않고 그대로
    새 경로에 이어 붙인다. 같은 파일명이 여러 개 "사라진(stale)" 상태로 동시에 남아
    있어 어느 항목이 이동한 것인지 애매하면, 잘못 추측하지 않고 새 항목으로 등록한다."""
    root = project_root()
    current_files: dict[str, str] = {}
    for dir_name, status in _STATUS_BY_DIR.items():
        folder = library_dir() / dir_name
        if not folder.is_dir():
            continue
        for path in sorted(folder.iterdir()):
            if not path.is_file() or path.name.startswith("."):
                continue
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue  # 지원 목록 밖의 파일은 자동 인식 대상이 아니다(정직하게 무시)
            current_files[str(path.relative_to(root))] = status

    by_path = {e["file_path"]: e for e in entries if e.get("file_path")}
    stale_by_basename: dict[str, list[dict]] = {}
    for entry in entries:
        fp = entry.get("file_path")
        if fp and fp not in current_files:
            stale_by_basename.setdefault(Path(fp).name, []).append(entry)

    added = 0
    for rel_path, status in current_files.items():
        if rel_path in by_path:
            by_path[rel_path]["status"] = status
            continue

        candidates = stale_by_basename.get(Path(rel_path).name, [])
        if len(candidates) == 1:
            moved = candidates.pop()
            moved["file_path"] = rel_path
            moved["status"] = status
            by_path[rel_path] = moved
            continue

        document_type = DEFAULT_DOCUMENT_TYPE
        entry = {
            "reference_id": _next_reference_id(entries),
            "title": Path(rel_path).stem,
            "company": None,
            "document_type": document_type,
            "source_type": DEFAULT_SOURCE_TYPE,
            "source_url": None,
            "file_path": rel_path,
            "published_date": None,
            "added_at": _now_iso(),
            "official_source": False,
            "reliability_grade": reliability_grade_for(document_type),
            "status": status,
            "latest_version": True,
            "applicable_services": [],
            "last_verified": None,
            "parseable": Path(rel_path).suffix.lower() in PARSEABLE_EXTENSIONS,
        }
        entries.append(entry)
        by_path[rel_path] = entry
        added += 1

    return added


def _scan_url_registry(entries: list[dict]) -> int:
    """URL Registry 지원: 웹을 크롤링하지 않는다(Round 12 금지 항목) — 사용자가
    `inbox/url_registry.yaml`에 직접 적어 둔 URL과 최소 Metadata를 그대로 등록한다."""
    manifest_path = inbox_dir() / "url_registry.yaml"
    if not manifest_path.exists():
        return 0

    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    by_url = {e.get("source_url"): e for e in entries if e.get("source_url")}
    added = 0

    for item in data.get("urls", []) or []:
        url = item.get("url")
        if not url or url in by_url:
            continue
        document_type = item.get("document_type") or DEFAULT_DOCUMENT_TYPE
        entry = {
            "reference_id": _next_reference_id(entries),
            "title": item.get("title") or url,
            "company": item.get("company"),
            "document_type": document_type,
            "source_type": item.get("source_type") or "official_website",
            "source_url": url,
            "file_path": None,
            "published_date": item.get("published_date"),
            "added_at": _now_iso(),
            "official_source": bool(item.get("official_source", False)),
            "reliability_grade": item.get("reliability_grade") or reliability_grade_for(document_type),
            "status": "active",
            "latest_version": True,
            "applicable_services": list(item.get("applicable_services", [])),
            "last_verified": item.get("last_verified"),
            "parseable": False,
        }
        entries.append(entry)
        by_url[url] = entry
        added += 1

    return added


def scan_and_register() -> dict:
    """항목 1~2(폴더에 추가 -> 자동 인식) + 항목 3(기본 Metadata 등록)을 수행한다.
    `{"total": N, "added": N}`을 반환한다. 여러 번 실행해도 안전하다(이미 등록된 파일은
    중복 추가되지 않고 status만 갱신됨)."""
    ensure_directories()
    entries = load_index()
    added = _scan_folders(entries)
    added += _scan_url_registry(entries)
    save_index(entries)
    return {"total": len(entries), "added": added}


def list_references(company: str | None = None, status: str | None = None) -> list[dict]:
    entries = load_index()
    if company is not None:
        entries = [e for e in entries if e.get("company") == company]
    if status is not None:
        entries = [e for e in entries if e.get("status") == status]
    return entries


_GRADE_RANK = {"A": 0, "B": 1, "C": 2}


def list_active_references_for_company(company_id: str | None) -> list[dict]:
    """항목 4(Knowledge Retrieval에서 참조 가능): `active/`에 있는(=검토를 마친) 자료 중
    해당 회사 것만, 신뢰도 높은 순 -> 최신 등록 순으로 반환한다. `company_id`가 없으면
    빈 목록(임의로 아무 자료나 붙이지 않는다)."""
    if not company_id:
        return []
    matches = list_references(company=company_id, status="active")
    matches.sort(key=lambda e: e.get("added_at") or "", reverse=True)
    matches.sort(key=lambda e: _GRADE_RANK.get(e.get("reliability_grade"), 3))
    return matches


def reference_citation_rows(entries: list[dict]) -> list[dict]:
    """항목 5(결과물에서 어떤 Reference를 사용했는지 표시)의 최소 표시 형식 —
    문서명/자료유형/발행일/Source URL 또는 파일 경로/신뢰도."""
    return [
        {
            "문서명": e.get("title") or "-",
            "자료유형": e.get("document_type") or "-",
            "발행일": e.get("published_date") or "-",
            "Source URL / 파일 경로": e.get("source_url") or e.get("file_path") or "-",
            "신뢰도": e.get("reliability_grade") or "-",
        }
        for e in entries
    ]


def reference_library_summary() -> dict:
    """Home Dashboard "Reference Library" 섹션(새 Widget 아님, Round 11의 HOME_* 토큰과
    동일한 패턴)이 쓰는 집계치 — 등록 자료 수/회사별 자료 수/최신 자료/공식자료 여부."""
    entries = load_index()
    by_company: dict[str, int] = {}
    for e in entries:
        company = e.get("company")
        if company:
            by_company[company] = by_company.get(company, 0) + 1

    latest = max(entries, key=lambda e: e.get("added_at") or "", default=None)

    return {
        "total": len(entries),
        "active_count": sum(1 for e in entries if e.get("status") == "active"),
        "unclassified_count": sum(1 for e in entries if e.get("status") == "unclassified"),
        "by_company": by_company,
        "latest_title": latest.get("title") if latest else None,
        "official_count": sum(1 for e in entries if e.get("official_source")),
    }


def main() -> int:
    result = scan_and_register()
    print(f"Reference Library 스캔 완료 — 전체 {result['total']}건, 신규 {result['added']}건")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
