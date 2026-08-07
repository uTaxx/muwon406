#!/usr/bin/env python3
"""TASK-001 — 프로젝트 구조 부트스트랩 검증/생성 도구.

--dry-run(기본값): 03_BUILD_SPECIFICATION.md §3에 정의된 폴더/기본파일이 존재하는지만
검사하고 보고한다. 아무것도 쓰지 않는다.
--apply: 누락된 "빈 폴더"만 생성한다 (기존 파일은 절대 덮어쓰지 않음. 충돌 시 `.generated`
접미사로 별도 생성 후 보고).

Architect Review Round 8: "RegistryManager는 Project Boot 시 전체 Registry를 검증한다."
이 스크립트가 Pilot의 "Project Boot" 지점이므로, 폴더/파일 스캐폴드 점검 뒤에
`RegistryManager.validate_all()`(Validation + Integrity Check + Dependency Check)을
호출한다 — 폴더 구조와 무관한 별개의 검사이므로 실패해도 스캐폴드 결과 자체는 그대로
보고한다.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from _common import project_root

REQUIRED_DIRS = [
    "docs", "docs/decisions",
    "config", "schemas", "knowledge", "prompts",
    "dashboard", "dashboard/current",
    "scripts",
    "n8n/workflows", "n8n/backups",
    "tests", "tests/fixtures",
    "output", "logs", "archive",
]

REQUIRED_FILES = [
    "CLAUDE.md", "README.md", "PROJECT_STATUS.md", "TODO.md", "CHANGELOG.md",
    ".env.example", ".gitignore", "requirements.txt",
]


def check() -> tuple[list[str], list[str]]:
    root = project_root()
    missing_dirs = [d for d in REQUIRED_DIRS if not (root / d).is_dir()]
    missing_files = [f for f in REQUIRED_FILES if not (root / f).is_file()]
    return missing_dirs, missing_files


def apply(missing_dirs: list[str]) -> list[str]:
    root = project_root()
    created = []
    for d in missing_dirs:
        target = root / d
        target.mkdir(parents=True, exist_ok=True)
        created.append(d)
    return created


def main() -> int:
    parser = argparse.ArgumentParser(description="LCIP Pilot 프로젝트 구조 부트스트랩")
    parser.add_argument("--dry-run", action="store_true", default=True, help="검사만 수행 (기본값)")
    parser.add_argument("--apply", action="store_true", help="누락된 빈 폴더를 생성한다 (파일은 생성하지 않음)")
    args = parser.parse_args()

    missing_dirs, missing_files = check()

    print("=== LCIP Pilot Scaffold 점검 ===")
    print(f"필수 폴더 {len(REQUIRED_DIRS)}개 중 누락: {len(missing_dirs)}개")
    for d in missing_dirs:
        print(f"  - {d}")
    print(f"필수 파일 {len(REQUIRED_FILES)}개 중 누락: {len(missing_files)}개")
    for f in missing_files:
        print(f"  - {f}")

    if missing_files:
        print(
            "\n[안내] 기본 파일은 이 스크립트가 생성하지 않는다 (내용이 있는 파일은 Claude Code가 "
            "직접 작성/검토해야 하므로). 누락된 파일이 있다면 TASK-001 작업을 다시 확인하라."
        )

    if args.apply and missing_dirs:
        created = apply(missing_dirs)
        print(f"\n생성한 빈 폴더: {len(created)}개")
        for d in created:
            print(f"  + {d}")
    elif not args.apply:
        print("\n(dry-run) 폴더/파일을 생성하지 않았다.")

    ok = not missing_dirs and not missing_files
    if ok:
        print("\n결과: PASS — 모든 필수 폴더/파일 존재")
    else:
        print("\n결과: 누락 항목 있음 (위 목록 참고)")

    registry_errors = run_registry_validation()

    # dry-run은 항상 보고만 하고 성공(0)으로 종료한다. --apply는 폴더 생성 후에도
    # 파일 누락이 남아있을 수 있으므로 그 경우에만 비정상 종료(1)로 알린다.
    if args.apply:
        return 1 if (missing_files or registry_errors) else 0
    return 0


def run_registry_validation() -> list[str]:
    """RegistryManager 전체(Company/Source/Model/Prompt/Workflow/Config/Storage/
    Technical Debt)에 Validation + Integrity Check + Dependency Check를 수행하고
    결과를 출력한다."""
    from registries.manager import RegistryManager

    manager = RegistryManager()
    errors = manager.validate_all()

    print("\n=== Registry 검증 (Architect Review Round 8) ===")
    if errors:
        print(f"Registry 검증 실패: {len(errors)}건")
        for e in errors:
            print(f"  - {e}")
    else:
        print(f"Registry {len(manager.registry_ids())}개 전체 통과 — Validation/Integrity/Dependency 오류 없음")
    return errors


if __name__ == "__main__":
    raise SystemExit(main())
