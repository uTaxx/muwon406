"""PromptTemplate — prompts/*.md 파일 하나를 감싸는 객체.

파일 파싱 자체(frontmatter 읽기, Static/Dynamic Block 분리)는 `scripts/claude_client.py`가
이미 갖고 있는 로직을 그대로 재사용한다 — 이 클래스는 그 결과를 OOP 형태로 감싸는 얇은
Wrapper다. Model Registry 조회(`get_model_name`)는 여전히 claude_client.py의 책임이다.
"""
from __future__ import annotations

from dataclasses import dataclass

import claude_client


@dataclass(frozen=True)
class PromptTemplateMeta:
    prompt_version: str
    default_model_id: str | None


class PromptTemplate:
    def __init__(self, name: str):
        self.name = name
        text, version = claude_client.load_prompt(name)
        self.text = text
        static_block, dynamic_block = claude_client.split_prompt_blocks(text)
        self.static_block = static_block
        self.dynamic_block_template = dynamic_block
        default_model_id = claude_client._frontmatter_field(text, "default_model_id")
        self.meta = PromptTemplateMeta(prompt_version=version, default_model_id=default_model_id)
