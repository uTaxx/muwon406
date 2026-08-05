#!/usr/bin/env python3
"""TASK-002 — config/*.yaml 검증 도구.

- YAML 문법 검증
- 필수 최상위 키 존재 검증
- topic_id / source_id / workflow_id 중복 검증
- Secret으로 보이는 키에 실제 값(플레이스홀더가 아닌)이 들어있는지 간단 검사
"""
from __future__ import annotations

import sys
from pathlib import Path

from _common import load_yaml, looks_like_secret_key, project_root

REQUIRED_TOP_LEVEL_KEY = {
    "project.yaml": "project",
    "topics.yaml": "topics",
    "sources.yaml": "sources",
    "cost_policy.yaml": "cost",
    "notification.yaml": "notifications",
    "drive_structure.yaml": "folders",
    "sheet_structure.yaml": "tabs",
    "workflow_registry.yaml": "workflows",
}


def check_syntax_and_required_keys() -> list[str]:
    errors = []
    for filename, required_key in REQUIRED_TOP_LEVEL_KEY.items():
        try:
            data = load_yaml(f"config/{filename}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{filename}: YAML 파싱 실패 — {exc}")
            continue
        if not isinstance(data, dict) or required_key not in data:
            errors.append(f"{filename}: 필수 최상위 키 '{required_key}' 없음")
    return errors


def check_duplicate_ids() -> list[str]:
    errors = []

    topics = load_yaml("config/topics.yaml").get("topics", [])
    topic_ids = [t["topic_id"] for t in topics]
    dupes = {t for t in topic_ids if topic_ids.count(t) > 1}
    if dupes:
        errors.append(f"topics.yaml: 중복 topic_id {sorted(dupes)}")

    sources = load_yaml("config/sources.yaml").get("sources", [])
    source_ids = [s["source_id"] for s in sources]
    dupes = {s for s in source_ids if source_ids.count(s) > 1}
    if dupes:
        errors.append(f"sources.yaml: 중복 source_id {sorted(dupes)}")

    workflows = load_yaml("config/workflow_registry.yaml").get("workflows", [])
    workflow_ids = [w["workflow_id"] for w in workflows]
    dupes = {w for w in workflow_ids if workflow_ids.count(w) > 1}
    if dupes:
        errors.append(f"workflow_registry.yaml: 중복 workflow_id {sorted(dupes)}")

    return errors


def check_no_plaintext_secrets() -> list[str]:
    errors = []
    config_dir = project_root() / "config"
    for path in sorted(config_dir.glob("*.yaml")):
        text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            if ":" not in line or line.strip().startswith("#"):
                continue
            key, _, value = line.partition(":")
            key = key.strip().strip("-").strip()
            value = value.strip().strip('"').strip("'")
            if not value or value.endswith("_env") or value.startswith("$"):
                continue
            if looks_like_secret_key(key) and len(value) > 6:
                errors.append(f"{path.name}:{line_no}: '{key}' 항목에 평문 값이 있는 것으로 보임")
    return errors


def main() -> int:
    all_errors: list[str] = []
    all_errors += check_syntax_and_required_keys()
    if not all_errors:
        all_errors += check_duplicate_ids()
    all_errors += check_no_plaintext_secrets()

    if all_errors:
        print("=== Config 검증 실패 ===")
        for e in all_errors:
            print(f"  - {e}")
        return 1

    print("=== Config 검증 통과 ===")
    print(f"검사한 파일: {len(REQUIRED_TOP_LEVEL_KEY)}개")
    print("YAML 문법 OK / 필수 키 OK / ID 중복 없음 / 평문 Secret 미발견")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
