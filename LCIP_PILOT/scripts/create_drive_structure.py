#!/usr/bin/env python3
"""TASK-005 — Google Drive 폴더 구조 생성 도구.

기본은 항상 --dry-run이다. 실제 Google Drive API를 호출하려면 --apply와 함께
LCIP_DRY_RUN=false, 그리고 인증 정보(.env)가 준비되어 있어야 한다.

Claude Code는 사용자 인증정보를 생성하거나 추정하지 않는다 (03_BUILD_SPECIFICATION.md TASK-005).
인증 방식은 세 가지 중 하나를 사용자가 선택한다:
  1. Google OAuth Desktop App  (--auth-mode oauth_desktop)
  2. Service Account + 공유폴더 권한  (--auth-mode service_account)
  3. n8n Google Drive Credential만 사용, 로컬 스크립트는 계획만 생성  (--auth-mode n8n_only)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _common import env_or_none, load_dotenv_if_present, load_yaml, project_root


def build_plan() -> dict:
    """config/drive_structure.yaml을 읽어 생성할 폴더 계획을 만든다. 외부 호출 없음."""
    cfg = load_yaml("config/drive_structure.yaml")
    root_name = cfg["drive_root_folder_name"]
    folders = cfg["folders"]
    subfolders = cfg.get("subfolders", {})

    plan = {
        "root_folder_name": root_name,
        "root_folder_id_env": cfg["drive_root_folder_id_env"],
        "existing_root_folder_id": env_or_none(cfg["drive_root_folder_id_env"]),
        "folders_to_ensure": [],
    }
    for folder in folders:
        entry = {"path": f"{root_name}/{folder['name']}", "purpose": folder["purpose"]}
        plan["folders_to_ensure"].append(entry)
        for sub in subfolders.get(folder["name"], []):
            plan["folders_to_ensure"].append(
                {"path": f"{root_name}/{folder['name']}/{sub}", "purpose": f"{folder['purpose']} (하위)"}
            )
    return plan


def print_plan(plan: dict) -> None:
    print("=== Google Drive 폴더 생성 계획 (dry-run) ===")
    if plan["existing_root_folder_id"]:
        print(f"기존 Root Folder ID 감지: {plan['existing_root_folder_id']} (동일 이름 재생성 안 함)")
    else:
        print(f"Root Folder ID 미설정 ({plan['root_folder_id_env']}) — 최초 생성 필요")
    print(f"Root 폴더명: {plan['root_folder_name']}")
    print(f"생성 예정 폴더 수: {len(plan['folders_to_ensure'])}")
    for entry in plan["folders_to_ensure"]:
        print(f"  - {entry['path']}  ({entry['purpose']})")


def _ensure_folder(service, name: str, parent_id: str | None) -> str:
    """이름+부모 조합이 같은 폴더가 이미 있으면 재사용하고, 없으면 새로 만든다(멱등성 —
    이 스크립트를 여러 번 실행해도 중복 폴더가 생기지 않는다)."""
    query = (
        f"name = '{name}' and mimeType = 'application/vnd.google-apps.folder' "
        "and trashed = false"
    )
    if parent_id:
        query += f" and '{parent_id}' in parents"
    results = service.files().list(q=query, spaces="drive", fields="files(id, name)").execute()
    existing = results.get("files", [])
    if existing:
        return existing[0]["id"]

    metadata = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        metadata["parents"] = [parent_id]
    created = service.files().create(body=metadata, fields="id").execute()
    return created["id"]


def apply_plan(plan: dict, auth_mode: str) -> None:
    """실제 Google Drive API 호출. dry-run이 아닐 때만 이 함수가 실행된다.

    Architect Review Round 13(RC2 실체화) — `oauth_desktop`/`service_account`
    실제 쓰기 로직을 완성했다. Credential이 아직 준비되지 않았다면
    `scripts/google_auth.py`가 명확한 안내 메시지와 함께 멈춘다(임의로 빈 값을
    쓰거나 추측하지 않는다).
    """
    if auth_mode == "n8n_only":
        print(
            "auth-mode=n8n_only: 로컬 스크립트는 실제 생성을 수행하지 않는다. "
            "위 계획을 n8n Google Drive Credential 기반 워크플로우에서 수동 반영하라."
        )
        return

    # Google API 클라이언트는 dry-run 경로에서 불필요한 의존성 설치를 강제하지 않도록
    # apply 시점에만 지연 import한다.
    try:
        from googleapiclient.discovery import build  # type: ignore
    except ImportError as exc:  # pragma: no cover - 실제 환경 의존
        print(
            "google-api-python-client가 설치되어 있지 않다. "
            "실제 적용 전 `pip install -r requirements.txt` 필요.",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    from google_auth import GoogleAuthError, DRIVE_SCOPES, load_credentials

    try:
        creds = load_credentials(auth_mode, DRIVE_SCOPES)
    except GoogleAuthError as exc:
        raise SystemExit(str(exc)) from exc

    service = build("drive", "v3", credentials=creds)

    root_folder_id = plan["existing_root_folder_id"]
    if not root_folder_id:
        root_folder_id = _ensure_folder(service, plan["root_folder_name"], parent_id=None)
        print(f"Root 폴더 생성/확인됨: {plan['root_folder_name']} (id={root_folder_id})")
        print(f"  -> .env의 {plan['root_folder_id_env']}에 이 ID를 저장하면 다음 실행부터 재사용된다.")
    else:
        print(f"기존 Root 폴더 재사용: {root_folder_id}")

    id_by_path: dict[str, str] = {plan["root_folder_name"]: root_folder_id}
    for entry in plan["folders_to_ensure"]:
        parts = entry["path"].split("/")
        current_path = parts[0]
        parent_id = id_by_path[current_path]
        for part in parts[1:]:
            current_path = f"{current_path}/{part}"
            if current_path in id_by_path:
                parent_id = id_by_path[current_path]
                continue
            folder_id = _ensure_folder(service, part, parent_id=parent_id)
            id_by_path[current_path] = folder_id
            print(f"  폴더 생성/확인됨: {current_path} (id={folder_id})")
            parent_id = folder_id

    print(f"\n완료 — 폴더 {len(id_by_path)}개 생성/확인됨.")


def main() -> int:
    parser = argparse.ArgumentParser(description="LCIP Pilot Google Drive 폴더 구조 도구")
    parser.add_argument("--dry-run", action="store_true", default=True, help="계획만 출력 (기본값)")
    parser.add_argument("--apply", action="store_true", help="실제 Google Drive에 폴더를 생성한다 (승인 필요)")
    parser.add_argument(
        "--auth-mode",
        choices=["oauth_desktop", "service_account", "n8n_only"],
        default="n8n_only",
        help="인증 방식 선택 (기본: n8n_only — 로컬에서는 계획만 생성)",
    )
    parser.add_argument("--out", default=None, help="계획 JSON을 파일로도 저장 (선택)")
    args = parser.parse_args()

    load_dotenv_if_present()
    plan = build_plan()
    print_plan(plan)

    if args.out:
        out_path = project_root() / args.out
        out_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n계획을 저장했다: {out_path}")

    if args.apply:
        print("\n--apply 플래그 감지 — 사용자 승인 여부를 다시 확인하라.")
        confirm = env_or_none("LCIP_CONFIRM_APPLY")
        if confirm != "yes":
            print(
                "안전장치: 실제 적용을 위해서는 환경변수 LCIP_CONFIRM_APPLY=yes 를 명시적으로 "
                "설정해야 한다 (사용자 승인의 명시적 증거). 현재 미설정이므로 dry-run으로 종료한다."
            )
            return 0
        apply_plan(plan, args.auth_mode)
    else:
        print("\n(dry-run) 실제 Google Drive API 호출 없음.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
