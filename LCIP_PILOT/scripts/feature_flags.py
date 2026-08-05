"""Feature Flags — Architect Review Round 6.

`config/feature_flags.yaml`을 읽는 단일 진실 공급원. Provider/Adapter/Storage가
`enabled` 인자를 명시적으로 받지 않았을 때 이 값을 기본값으로 사용한다 — "다음 Architect
승인 전까지는 실제 외부 호출을 하지 않는다"는 원칙이 코드 곳곳에 하드코딩된 `False` 대신
이 파일 하나로 관리되도록 하기 위함이다.
"""
from __future__ import annotations

from _common import load_yaml


def load_feature_flags() -> dict:
    return load_yaml("config/feature_flags.yaml")["feature_flags"]


def is_enabled(flag_name: str, flags: dict | None = None) -> bool:
    flags = flags if flags is not None else load_feature_flags()
    if flag_name not in flags:
        raise ValueError(
            f"알 수 없는 feature flag: '{flag_name}' — config/feature_flags.yaml을 확인해야 한다."
        )
    return bool(flags[flag_name])
