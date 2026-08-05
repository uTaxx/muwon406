"""LCIP Pilot 스크립트 공용 유틸리티.

Config/​.env 로드, Secret 마스킹 등 여러 scripts/*.py가 공통으로 쓰는 최소한의 헬퍼만 담는다.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent

_SECRET_KEY_HINTS = ("key", "token", "secret", "password", "credential")


def project_root() -> Path:
    return PROJECT_ROOT


def load_yaml(relative_path: str) -> Any:
    path = PROJECT_ROOT / relative_path
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_dotenv_if_present() -> None:
    """python-dotenv가 설치되어 있으면 .env를 로드한다. 없으면 조용히 넘어간다."""
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(env_path)
    except ImportError:
        # dry-run 경로에서는 python-dotenv가 없어도 동작해야 한다.
        pass


def mask_secret(value: str | None) -> str:
    if not value:
        return "(미설정)"
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"


def looks_like_secret_key(key: str) -> bool:
    lowered = key.lower()
    return any(hint in lowered for hint in _SECRET_KEY_HINTS)


def env_or_none(name: str) -> str | None:
    return os.environ.get(name)
