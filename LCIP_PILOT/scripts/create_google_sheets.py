#!/usr/bin/env python3
"""TASK-006 — Google Sheets(Master Spreadsheet) 탭 구조 생성 도구.

기본은 항상 --dry-run이다. 기존 Spreadsheet ID가 있으면 누락된 탭만 생성 대상으로 표시하고,
기존 탭 데이터는 절대 삭제하지 않는다.
"""
from __future__ import annotations

import argparse
import json
import sys

from _common import env_or_none, load_dotenv_if_present, load_yaml, mask_secret, project_root


def load_columns() -> dict:
    path = project_root() / "schemas" / "google_sheets_columns.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["sheets"]


def build_plan(existing_tabs: list[str] | None = None) -> dict:
    cfg = load_yaml("config/sheet_structure.yaml")
    columns = load_columns()
    existing_tabs = existing_tabs or []

    plan = {
        "master_spreadsheet_id_env": cfg["master_spreadsheet_id_env"],
        "existing_spreadsheet_id": mask_secret(env_or_none(cfg["master_spreadsheet_id_env"])),
        "tabs_to_create": [],
        "tabs_already_present": [],
        "draft_status_warning": [],
    }

    for tab in cfg["tabs"]:
        name = tab["name"]
        entry = {
            "name": name,
            "status": tab["status"],
            "freeze_rows": tab["freeze_rows"],
            "columns": columns.get(name, {}).get("columns", []),
        }
        if name in existing_tabs:
            plan["tabs_already_present"].append(entry)
        else:
            plan["tabs_to_create"].append(entry)
        if tab["status"] == "draft":
            plan["draft_status_warning"].append(name)

    return plan


def print_plan(plan: dict) -> None:
    print("=== Google Sheets 탭 생성 계획 (dry-run) ===")
    print(f"Master Spreadsheet ID: {plan['existing_spreadsheet_id']}")
    print(f"생성 예정 탭: {len(plan['tabs_to_create'])} / 이미 존재: {len(plan['tabs_already_present'])}")
    for tab in plan["tabs_to_create"]:
        print(f"  + {tab['name']} ({len(tab['columns'])}개 컬럼, freeze_rows={tab['freeze_rows']})")
        print(f"      columns: {', '.join(tab['columns'])}")
    for tab in plan["tabs_already_present"]:
        print(f"  = {tab['name']} (이미 존재 — 데이터 삭제하지 않음, 누락 컬럼만 확인 필요)")
    if plan["draft_status_warning"]:
        print(
            "\n[주의] 아래 탭은 원본 설계문서에 컬럼이 명문화되어 있지 않아 이번 라운드에서 "
            "초안(draft) 작성했다. 실제 생성 전 사용자 확인 필요: "
            + ", ".join(plan["draft_status_warning"])
        )


def apply_plan(plan: dict) -> None:
    try:
        import gspread  # type: ignore  # noqa: F401
    except ImportError as exc:  # pragma: no cover
        print(
            "gspread가 설치되어 있지 않다. 실제 적용 전 `pip install gspread google-auth` 필요.",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    raise SystemExit(
        "이번 라운드(TASK-001~007)는 Google Sheets 실제 생성을 수행하지 않는다. "
        "TASK-008 이후, 사용자가 Master Spreadsheet ID와 인증 정보를 제공하고 명시적으로 "
        "승인한 뒤 apply 로직을 완성한다."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="LCIP Pilot Google Sheets 탭 구조 도구")
    parser.add_argument("--dry-run", action="store_true", default=True, help="계획만 출력 (기본값)")
    parser.add_argument("--apply", action="store_true", help="실제 Google Sheets에 탭을 생성한다 (승인 필요)")
    parser.add_argument(
        "--existing-tabs",
        default="",
        help="쉼표로 구분된, 이미 존재하는 탭 이름 목록 (테스트/시뮬레이션용)",
    )
    parser.add_argument("--out", default=None, help="계획 JSON을 파일로도 저장 (선택)")
    args = parser.parse_args()

    load_dotenv_if_present()
    existing = [t.strip() for t in args.existing_tabs.split(",") if t.strip()]
    plan = build_plan(existing_tabs=existing)
    print_plan(plan)

    if args.out:
        out_path = project_root() / args.out
        out_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n계획을 저장했다: {out_path}")

    if args.apply:
        confirm = env_or_none("LCIP_CONFIRM_APPLY")
        if confirm != "yes":
            print(
                "\n안전장치: 실제 적용을 위해서는 환경변수 LCIP_CONFIRM_APPLY=yes 를 명시적으로 "
                "설정해야 한다. 현재 미설정이므로 dry-run으로 종료한다."
            )
            return 0
        apply_plan(plan)
    else:
        print("\n(dry-run) 실제 Google Sheets API 호출 없음.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
