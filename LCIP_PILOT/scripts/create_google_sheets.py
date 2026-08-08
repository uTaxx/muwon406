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


def _create_master_spreadsheet(creds) -> str:
    """`GOOGLE_SHEETS_MASTER_SPREADSHEET_ID`가 아직 없을 때 새 Spreadsheet를 만든다
    (뉴스 수집 실체화 라운드 이어서, 2026-08-08 신설). `GOOGLE_DRIVE_ROOT_FOLDER_ID`
    가 설정돼 있으면 그 폴더 안에 만들고, 없으면 Drive 루트에 만든다 — 임의로 새
    폴더를 만들지 않는다(사용자가 이미 만들어 둔 폴더만 사용한다)."""
    from googleapiclient.discovery import build

    drive_service = build("drive", "v3", credentials=creds)
    metadata = {
        "name": "LCIP Master Spreadsheet",
        "mimeType": "application/vnd.google-apps.spreadsheet",
    }
    parent_folder_id = env_or_none("GOOGLE_DRIVE_ROOT_FOLDER_ID")
    if parent_folder_id:
        metadata["parents"] = [parent_folder_id]
    created = drive_service.files().create(body=metadata, fields="id").execute()
    return created["id"]


def apply_plan(plan: dict, auth_mode: str) -> None:
    """실제 Google Sheets API 호출(gspread 경유). dry-run이 아닐 때만 실행된다.

    Architect Review Round 13(RC2 실체화) — 탭 생성 apply 로직을 완성했다. 기존 탭은
    절대 건드리지 않고(`plan["tabs_to_create"]`만 대상), 각 탭 생성 직후 헤더 행을
    쓰고 `freeze_rows`만큼 고정한다.

    뉴스 수집 실체화 라운드 이어서(2026-08-08) — `GOOGLE_SHEETS_MASTER_SPREADSHEET_ID`
    가 없어도 더 이상 즉시 실패하지 않는다. `GOOGLE_DRIVE_ROOT_FOLDER_ID`(사용자가
    이미 만들어 둔 Drive 폴더) 안에 새 Master Spreadsheet를 만든 뒤 이어서 탭을
    생성한다.
    """
    try:
        import gspread  # type: ignore
    except ImportError as exc:  # pragma: no cover
        print(
            "gspread가 설치되어 있지 않다. 실제 적용 전 `pip install -r requirements.txt` 필요.",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    from google_auth import DRIVE_SCOPES, GoogleAuthError, SHEETS_SCOPES, load_credentials

    spreadsheet_id = env_or_none("GOOGLE_SHEETS_MASTER_SPREADSHEET_ID")
    try:
        creds = load_credentials(auth_mode, DRIVE_SCOPES + SHEETS_SCOPES)
    except GoogleAuthError as exc:
        raise SystemExit(str(exc)) from exc

    if not spreadsheet_id:
        spreadsheet_id = _create_master_spreadsheet(creds)
        print(
            f"Master Spreadsheet 신규 생성됨 (id={spreadsheet_id}) — .env의 "
            "GOOGLE_SHEETS_MASTER_SPREADSHEET_ID에 이 값을 저장해야 다음 실행부터 "
            "재사용된다(임의로 .env를 대신 수정하지 않는다)."
        )

    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(spreadsheet_id)
    existing_titles = {ws.title for ws in spreadsheet.worksheets()}

    created = 0
    for tab in plan["tabs_to_create"]:
        if tab["name"] in existing_titles:
            continue  # 이미 있는 탭은 건드리지 않는다(데이터 삭제 금지 원칙)
        cols = max(len(tab["columns"]), 1)
        worksheet = spreadsheet.add_worksheet(title=tab["name"], rows=100, cols=cols)
        if tab["columns"]:
            worksheet.append_row(tab["columns"])
        if tab["freeze_rows"]:
            worksheet.freeze(rows=tab["freeze_rows"])
        print(f"  탭 생성됨: {tab['name']} ({len(tab['columns'])}개 컬럼)")
        created += 1

    print(f"\n완료 — 탭 {created}개 생성됨(이미 존재하던 탭은 건드리지 않음).")


def main() -> int:
    parser = argparse.ArgumentParser(description="LCIP Pilot Google Sheets 탭 구조 도구")
    parser.add_argument("--dry-run", action="store_true", default=True, help="계획만 출력 (기본값)")
    parser.add_argument("--apply", action="store_true", help="실제 Google Sheets에 탭을 생성한다 (승인 필요)")
    parser.add_argument(
        "--existing-tabs",
        default="",
        help="쉼표로 구분된, 이미 존재하는 탭 이름 목록 (테스트/시뮬레이션용)",
    )
    parser.add_argument(
        "--auth-mode",
        choices=["oauth_desktop", "service_account"],
        default="oauth_desktop",
        help="--apply 시 사용할 Google 인증 방식 (기본: oauth_desktop)",
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
        apply_plan(plan, args.auth_mode)
    else:
        print("\n(dry-run) 실제 Google Sheets API 호출 없음.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
