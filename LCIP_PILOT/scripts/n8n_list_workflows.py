#!/usr/bin/env python3
"""TASK-008 — n8n 워크플로우 목록 조회 도구 (dry-run 기본).

N8N_BASE_URL / N8N_API_KEY가 .env에 없으면 로컬 n8n/workflows/*.json 목록만 보여준다.
실제 n8n Cloud API 호출은 이번 라운드에서 구현하지 않는다 (TASK-008은 다음 라운드).
"""
from __future__ import annotations

from _common import env_or_none, load_dotenv_if_present, mask_secret, project_root


def local_workflow_files() -> list[str]:
    wf_dir = project_root() / "n8n" / "workflows"
    return sorted(p.name for p in wf_dir.glob("*.json"))


def main() -> int:
    load_dotenv_if_present()
    base_url = env_or_none("N8N_BASE_URL")
    api_key = env_or_none("N8N_API_KEY")

    print("=== n8n 워크플로우 목록 (로컬) ===")
    for name in local_workflow_files():
        print(f"  - {name}")

    print("\n=== n8n Cloud API 연결 상태 ===")
    print(f"N8N_BASE_URL: {base_url or '(미설정)'}")
    print(f"N8N_API_KEY: {mask_secret(api_key)}")
    if not base_url or not api_key:
        print(
            "N8N_BASE_URL/N8N_API_KEY가 없어 실제 API 조회는 생략한다. "
            "TASK-008(외부 연결 승인) 라운드에서 사용자 준비 후 연결한다."
        )
    else:
        print(
            "자격 증명이 감지되었으나, 이번 라운드는 실제 n8n API를 호출하지 않는다 "
            "(TASK-001~007 범위 밖)."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
