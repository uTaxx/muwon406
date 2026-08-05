#!/usr/bin/env python3
"""TASK-008 — n8n 워크플로우 배포 도구 (dry-run 기본, 실제 배포는 다음 라운드).

안전장치 (03_BUILD_SPECIFICATION.md TASK-008):
- 기본은 --dry-run
- --apply와 사용자 명시적 승인(LCIP_CONFIRM_APPLY=yes) 없이는 쓰기 금지
- 기존 Workflow 삭제 금지
- 배포해도 항상 active:false
"""
from __future__ import annotations

import argparse
import json

from _common import env_or_none, load_dotenv_if_present, mask_secret, project_root


def load_local_workflows() -> list[dict]:
    wf_dir = project_root() / "n8n" / "workflows"
    workflows = []
    for path in sorted(wf_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        workflows.append({"file": path.name, "name": data["name"], "active": data["active"]})
    return workflows


def main() -> int:
    parser = argparse.ArgumentParser(description="LCIP Pilot n8n 워크플로우 배포 도구")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply", action="store_true", help="실제 n8n Cloud에 배포한다 (승인 필요)")
    args = parser.parse_args()

    load_dotenv_if_present()
    workflows = load_local_workflows()

    print("=== n8n 배포 계획 (dry-run) ===")
    for wf in workflows:
        print(f"  - {wf['file']}: \"{wf['name']}\" (active={wf['active']})")

    base_url = env_or_none("N8N_BASE_URL")
    api_key = env_or_none("N8N_API_KEY")
    print(f"\nN8N_BASE_URL: {base_url or '(미설정)'}")
    print(f"N8N_API_KEY: {mask_secret(api_key)}")

    if not args.apply:
        print("\n(dry-run) 실제 n8n API 호출 없음. 모든 워크플로우는 배포되어도 active:false 유지 예정.")
        return 0

    confirm = env_or_none("LCIP_CONFIRM_APPLY")
    if confirm != "yes" or not base_url or not api_key:
        print(
            "\n안전장치: 실제 배포를 위해서는 N8N_BASE_URL/N8N_API_KEY와 "
            "LCIP_CONFIRM_APPLY=yes가 모두 필요하다. 현재 조건 미충족 — dry-run으로 종료."
        )
        return 0

    raise SystemExit(
        "이번 라운드(TASK-001~007)는 n8n 실제 배포를 수행하지 않는다. "
        "TASK-008 승인 후 별도 라운드에서 n8n REST API 연동을 완성한다."
    )


if __name__ == "__main__":
    raise SystemExit(main())
