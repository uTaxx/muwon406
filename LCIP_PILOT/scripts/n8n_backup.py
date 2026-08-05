#!/usr/bin/env python3
"""TASK-008 — n8n 워크플로우 백업 도구 (dry-run 기본).

이번 라운드는 로컬 n8n/workflows/*.json을 n8n/backups/<timestamp>/로 복사하는 로컬 백업만
지원한다 (실제 n8n Cloud에서 배포된 워크플로우를 가져오는 기능은 TASK-008에서 구현).
"""
from __future__ import annotations

import argparse
import shutil
from datetime import datetime, timezone

from _common import project_root


def backup_local(apply: bool) -> list[str]:
    src_dir = project_root() / "n8n" / "workflows"
    files = sorted(src_dir.glob("*.json"))
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest_dir = project_root() / "n8n" / "backups" / ts

    print(f"백업 대상 {len(files)}개 파일 -> {dest_dir.relative_to(project_root())}/")
    if not apply:
        for f in files:
            print(f"  (dry-run) {f.name}")
        return [f.name for f in files]

    dest_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for f in files:
        shutil.copy2(f, dest_dir / f.name)
        copied.append(f.name)
    return copied


def main() -> int:
    parser = argparse.ArgumentParser(description="LCIP Pilot n8n 워크플로우 로컬 백업")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply", action="store_true", help="실제로 n8n/backups/에 복사한다")
    args = parser.parse_args()

    copied = backup_local(apply=args.apply)
    if args.apply:
        print(f"백업 완료: {len(copied)}개 파일")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
