"""PromptValidator — Prompt Engine이 조립한 결과가 최소 조건을 만족하는지 검사한다."""
from __future__ import annotations

from .template import PromptTemplate


class PromptValidationError(ValueError):
    pass


class PromptValidator:
    def validate_template(self, template: PromptTemplate) -> None:
        if not template.static_block.strip():
            raise PromptValidationError(f"'{template.name}' 프롬프트의 Static Block이 비어 있다.")
        if not template.meta.prompt_version or template.meta.prompt_version == "unknown":
            raise PromptValidationError(
                f"'{template.name}' 프롬프트에 prompt_version frontmatter가 없다."
            )

    def validate_messages(self, messages: list[dict]) -> None:
        if not messages:
            raise PromptValidationError("조립된 메시지가 비어 있다.")
        if not any(m.get("text", "").strip() for m in messages):
            raise PromptValidationError("모든 메시지 블록의 내용이 비어 있다.")
        # Static Block(첫 블록)은 항상 존재해야 한다 — Dynamic 이하 블록만 있는 것은 허용하지 않는다.
        if not messages[0].get("text", "").strip():
            raise PromptValidationError("Static Block(첫 번째 메시지)이 비어 있다.")
