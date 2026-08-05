"""PromptBuilder — Static/Dynamic/Knowledge/Source/Context Block을 조립해 Anthropic
Messages API의 content 배열을 만든다.

조립 순서: **PromptTemplate → PromptBuilder → PromptValidator → PromptCache → Provider**
(Architect Review Round 5). `ClaudeProvider`는 이 클래스가 반환한 messages를 그대로
`messages[0]["content"]`로 사용한다(TASK-009 본구현에서 실제 호출부를 완성할 때).

블록 5종의 역할:
- **Static Block**: 프롬프트 지시문 자체(역할/규칙/출력 형식) — prompts/*.md에서 로드,
  항상 캐시 대상.
- **Dynamic Block**: 이번 요청의 핵심 대상(기사 등) — 매 호출마다 다르므로 캐시하지 않는다.
- **Knowledge Block**: Knowledge Retrieval Engine이 만든 발췌(회사/Topic 관련 Knowledge
  Section) — Knowledge Base 버전이 바뀌기 전까지는 안정적이므로 캐시 대상.
- **Source Block**: 이번 기사의 출처와 Source Reliability Score — 캐시 대상(기사 단위로는
  바뀌지만 같은 출처가 반복되면 재사용 가능).
- **Context Block**: 그 외 배경 정보(기존 타임라인 요약 등) — 매 호출마다 다르므로 캐시하지 않는다.
"""
from __future__ import annotations

import json

from .cache import PromptCache
from .template import PromptTemplate
from .validator import PromptValidator


class PromptBuilder:
    def __init__(
        self,
        template: PromptTemplate,
        cache: PromptCache | None = None,
        validator: PromptValidator | None = None,
    ):
        self.template = template
        self.cache = cache or PromptCache()
        self.validator = validator or PromptValidator()

    def build(
        self,
        dynamic_payload: dict,
        knowledge_block: str = "",
        source_block: str = "",
        context_block: str = "",
    ) -> list[dict]:
        self.validator.validate_template(self.template)
        cache_control_type = self.cache.cache_control_type()
        static_text = self.cache.get_static_block(self.template)

        messages: list[dict] = [
            {
                "type": "text",
                "text": static_text,
                "cache_control": {"type": cache_control_type},
            }
        ]

        if knowledge_block.strip():
            messages.append(
                {
                    "type": "text",
                    "text": f"## Knowledge Block\n\n{knowledge_block}",
                    "cache_control": {"type": cache_control_type},
                }
            )

        if source_block.strip():
            messages.append(
                {
                    "type": "text",
                    "text": f"## Source Block\n\n{source_block}",
                    "cache_control": {"type": cache_control_type},
                }
            )

        if context_block.strip():
            messages.append(
                {"type": "text", "text": f"## Context Block\n\n{context_block}"}
            )

        messages.append(
            {
                "type": "text",
                "text": json.dumps(dynamic_payload, ensure_ascii=False, indent=2),
            }
        )

        self.validator.validate_messages(messages)
        return messages
