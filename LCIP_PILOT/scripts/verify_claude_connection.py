"""Claude API 실제 연결 최소 비용 검증 스크립트 (Round 13 이어서, 2026-08-08).

`config/feature_flags.yaml`의 `claude_api_enabled=true` + `.env`의
`ANTHROPIC_API_KEY`가 모두 준비된 상태에서, classification tier(가장 저렴한
모델)로 1회만 실제 API를 호출해 연결이 되는지 확인한다. 새로운 Provider/Pipeline
경로를 추가하지 않는다 — 기존 `providers.factory.get_default_provider()` +
`ClaudeProvider.classify_relevance()`를 그대로 사용한다(실체화 검증 목적이며
새 기능이 아니다).

API Key/Secret 값은 어디에도 출력하지 않는다 — 사용된 Provider 종류/모델명/
토큰 사용량/추정 비용만 표시한다.
"""
from __future__ import annotations

from _common import load_dotenv_if_present, load_yaml
from feature_flags import is_enabled
from providers.claude_provider import ClaudeProvider
from providers.factory import get_default_provider

_MINIMAL_ARTICLE = {
    "title_original": "Engineered stone silicosis lawsuit filed in California",
    "source_url": "https://example.com/verify-claude-connection",
    "published_at": "2026-08-08T00:00:00Z",
    "language": "en",
}
_MINIMAL_TOPIC = {"topic_id": "TOP-0001", "related_lx_companies": ["LX_HAUSYS"]}


def main() -> int:
    load_dotenv_if_present()

    if not is_enabled("claude_api_enabled"):
        print(
            "중단: config/feature_flags.yaml의 claude_api_enabled가 false다 — "
            "먼저 true로 전환해야 검증할 수 있다."
        )
        return 1

    provider = get_default_provider()
    if not isinstance(provider, ClaudeProvider):
        print(
            "중단: get_default_provider()가 MockProvider를 반환했다 — "
            "ANTHROPIC_API_KEY(.env)가 비어 있는지 확인하라."
        )
        return 1

    print("실제 Claude API 연결을 검증한다 (classification tier, 최소 비용 1회 호출)...")
    result = provider.classify_relevance(_MINIMAL_ARTICLE, _MINIMAL_TOPIC)

    # usage는 API 자체가 실패(인증/네트워크 오류 등)했을 때만 None이다 — 응답은 왔지만
    # JSON 파싱/스키마 검증에서 걸린 경우는 실제 과금이 발생했으므로 비용을 함께 보여준다.
    if result.usage is not None:
        usage = result.usage
        pricing = load_yaml("config/model_pricing.yaml")["pricing"]["classification"]
        cost = (
            usage.input_tokens * pricing["usd_per_million_input_tokens"] / 1_000_000
            + usage.output_tokens * pricing["usd_per_million_output_tokens"] / 1_000_000
        )
        print(f"모델: {usage.model}")
        print(f"토큰 사용량: input={usage.input_tokens}, output={usage.output_tokens}")
        print(f"추정 비용: ${cost:.6f}")

    if not result.ok:
        print(f"응답은 받았으나 실패: {result.error}")
        print(
            "(usage가 위에 표시됐다면 네트워크/인증 연결 자체는 성공했다는 뜻이다 — "
            "이 실패는 JSON 파싱 또는 스키마 검증 단계에서 발생했다.)"
        )
        return 1

    print("성공 — 연결 확인됨 (스키마 검증까지 통과).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
