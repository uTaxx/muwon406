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


def apply_plan(plan: dict, auth_mode: str) -> None:
    """실제 Google Drive API 호출. dry-run이 아닐 때만 이 함수가 실행된다."""
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
            "실제 적용 전 `pip install google-api-python-client google-auth` 필요.",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    if auth_mode == "oauth_desktop":
        raise SystemExit(
            "OAuth Desktop 인증 흐름은 사용자 브라우저 승인이 필요하다. "
            "docs/GOOGLE_DRIVE_SETUP.md의 절차를 먼저 완료한 뒤 이 스크립트를 다시 실행하라."
        )
    if auth_mode == "service_account":
        sa_path = env_or_none("GOOGLE_SERVICE_ACCOUNT_JSON_PATH")
        if not sa_path:
            raise SystemExit("GOOGLE_SERVICE_ACCOUNT_JSON_PATH가 .env에 설정되어 있지 않다.")
        raise SystemExit(
            "Service Account 자격 증명이 감지되었으나, 이번 라운드(TASK-001~007)는 "
            "실제 쓰기를 수행하지 않는다. 사용자 승인 후 별도 라운드에서 apply 로직을 완성한다."
        )
    raise SystemExit(f"알 수 없는 auth-mode: {auth_mode}")


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
