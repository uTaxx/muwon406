#!/usr/bin/env python3
"""TASK-008 — n8n 워크플로우 배포 도구.

안전장치 (03_BUILD_SPECIFICATION.md TASK-008):
- 기본은 --dry-run
- --apply와 사용자 명시적 승인(LCIP_CONFIRM_APPLY=yes) 없이는 쓰기 금지
- 기존 Workflow 삭제 금지
- 배포해도 항상 active:false

Architect Review Round 13(RC2 실체화) — 실제 n8n REST API 호출(`apply_deploy()`)을
완성했다. n8n Public API(`/api/v1/workflows`, `X-N8N-API-KEY` 헤더)를 `requests`로
직접 호출한다(이미 있는 의존성, 새 라이브러리 없음). **주의**: 이 코드는 실제 n8n
Cloud 인스턴스로 검증되지 않았다(N8N_BASE_URL/N8N_API_KEY가 아직 준비되지 않음) —
n8n Public API가 `name`/`nodes`/`connections`/`settings`를 요구한다는 공식 문서
기준으로 작성했으며, `tags`(태그 ID 별도 관리 필요)와 `active`(생성 API가 거부하는
버전이 있어 생성 후 항상 비활성 상태로 남는 n8n 기본 동작에 맡김)는 페이로드에서
제외했다. 사용자가 실제 Credential을 제공하면 1회 실행으로 이 가정을 검증해야 한다.
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


def apply_deploy(base_url: str, api_key: str, http=None) -> list[dict]:
    """워크플로우별로 이름이 이미 존재하면 갱신(PUT), 없으면 생성(POST)한다. 기존
    Workflow를 삭제하는 API 호출은 어디에도 없다(안전장치). `http`를 주입하면(테스트용)
    실제 네트워크 없이 로직만 검증할 수 있다."""
    import requests as _requests

    http = http or _requests
    headers = {"X-N8N-API-KEY": api_key, "Content-Type": "application/json"}

    list_resp = http.get(f"{base_url}/api/v1/workflows", headers=headers, timeout=15)
    list_resp.raise_for_status()
    existing_by_name = {wf["name"]: wf["id"] for wf in list_resp.json().get("data", [])}

    results = []
    wf_dir = project_root() / "n8n" / "workflows"
    for path in sorted(wf_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        name = data["name"]
        # n8n Public API 생성/수정 payload는 name/nodes/connections/settings만 받는다
        # (tags는 태그 ID 매핑이 별도로 필요해 이번 라운드는 보내지 않는다 — 태그 없이
        # 배포된 워크플로우는 n8n UI에서 수동으로 붙여야 한다. active는 절대 보내지
        # 않는다 — "배포해도 항상 active:false" 원칙을 API 계약에 기대지 않고 payload
        # 자체에서 보장한다).
        payload = {
            "name": name,
            "nodes": data["nodes"],
            "connections": data["connections"],
            "settings": data.get("settings", {}),
        }

        if name in existing_by_name:
            wf_id = existing_by_name[name]
            resp = http.put(
                f"{base_url}/api/v1/workflows/{wf_id}", headers=headers, json=payload, timeout=15
            )
            resp.raise_for_status()
            print(f"  갱신됨: {name} (id={wf_id})")
            results.append({"name": name, "action": "updated", "id": wf_id})
        else:
            resp = http.post(f"{base_url}/api/v1/workflows", headers=headers, json=payload, timeout=15)
            resp.raise_for_status()
            new_id = resp.json().get("id")
            print(f"  생성됨: {name} (id={new_id})")
            results.append({"name": name, "action": "created", "id": new_id})

    return results


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

    apply_deploy(base_url, api_key)
    print("\n완료 — 기존 Workflow는 삭제되지 않았고, 배포된 Workflow는 n8n 기본값대로 비활성 상태다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
