"""Validate 단계 — 각 산출물을 해당 JSON Schema로 검증한다.

`ValidationError`가 나면 다음 단계(Generate Intelligence/Store)로 넘어가지 않는다
(CLAUDE.md 작업절차 #8 "실패 시 다음 Task로 넘어가지 않는다"와 동일한 원칙을 파이프라인
레코드 단위에 적용한 것).
"""
from __future__ import annotations

import json

from jsonschema import validate as jsonschema_validate
from _common import project_root

SCHEMAS_DIR = project_root() / "schemas"


def validate_claude_output(parsed_json: dict, schema_def: str) -> None:
    """schemas/claude_output.schema.json의 $defs/<schema_def>로 검증한다."""
    schema = json.loads((SCHEMAS_DIR / "claude_output.schema.json").read_text(encoding="utf-8"))
    sub_schema = {**schema["$defs"][schema_def], "$defs": schema["$defs"]}
    jsonschema_validate(instance=parsed_json, schema=sub_schema)


def validate_article(article: dict) -> None:
    schema = json.loads((SCHEMAS_DIR / "article.schema.json").read_text(encoding="utf-8"))
    jsonschema_validate(instance=article, schema=schema)


def validate_intelligence(intelligence: dict) -> None:
    schema = json.loads((SCHEMAS_DIR / "intelligence.schema.json").read_text(encoding="utf-8"))
    jsonschema_validate(instance=intelligence, schema=schema)
