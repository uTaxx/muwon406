#!/usr/bin/env python3
"""Secret 평문 저장 검사 도구.

.env 자체는 검사 대상에서 제외한다 (그 파일은 평문 저장이 허용된 유일한 곳이며,
.gitignore로 커밋되지 않는다). 그 외 코드/문서/설정/JSON 파일에서 실제 값처럼 보이는
API Key/Token 패턴을 찾는다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from _common import project_root

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", "logs", "output", "archive"}
SKIP_FILES = {".env"}  # .env는 gitignore 대상이며 평문 저장이 허용되는 유일한 위치

# 실제 발급된 값처럼 보이는 패턴만 매칭한다 (placeholder/예시 값 오탐을 줄이기 위해
# 최소 길이·문자구성을 요구한다).
PATTERNS = [
    ("Anthropic API Key", re.compile(r"sk-ant-[A-Za-z0-9\-_]{20,}")),
    ("Generic 'sk-' style key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("Telegram Bot Token", re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b")),
    ("Google OAuth Client Secret", re.compile(r"\bGOCSPX-[A-Za-z0-9_-]{20,}\b")),
    ("AWS Access Key ID", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Generic Bearer token", re.compile(r"Bearer\s+[A-Za-z0-9\-_.=]{20,}")),
]

TEXT_EXTENSIONS = {".py", ".md", ".yaml", ".yml", ".json", ".js", ".html", ".css", ".txt"}


def iter_text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in SKIP_FILES:
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        yield path


def scan(root: Path) -> list[str]:
    findings = []
    for path in iter_text_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            for label, pattern in PATTERNS:
                if pattern.search(line):
                    rel = path.relative_to(root)
                    findings.append(f"{rel}:{line_no}: {label} 패턴 감지")
    return findings


def main() -> int:
    root = project_root()
    findings = scan(root)
    if findings:
        print("=== Secret Scan 실패 — 평문 Secret으로 보이는 값 발견 ===")
        for f in findings:
            print(f"  - {f}")
        return 1
    print("=== Secret Scan 통과 — 평문 Secret 미발견 ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
