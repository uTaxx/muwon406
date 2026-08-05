---
prompt_id: policy_analysis
prompt_version: 0.2.0
used_by: Master Pipeline — AI Analyze 단계, policy/regulatory 이벤트 전용 보조 프롬프트 (舊 WF-P05, ADR-007로 통합)
max_input_tokens: 8000
max_output_tokens: 1200
cache_structure: static_block + dynamic_block (Architect Review Q3)
---

# Policy / Regulatory Analysis Prompt

## Static Block (Cacheable)

### 역할

정책·규제·입법 관련 기사(예: 세이프가드, 관세, 결정형 실리카 규제 강화)를 분석해 규제
단계와 LX Hausys에 대한 잠재적 영향 경로를 정리한다. `risk_analysis.md`의 일반 규칙을 모두
따르되, 규제 단계 분류가 추가된다. `mission_subcategory`(배열)는 대개 `regulatory`를
포함한다 (`knowledge/MISSION_FRAMEWORK.md` 참고). 규제 강화가 동시에 기술 전환 기회이면
`mission_category`에 `future_readiness`도 함께 포함한다.

### 규제 단계 분류 (원문에서 확인 가능한 경우에만 선택)

```text
proposed        - 발의/제안 단계
public_comment  - 공청회/의견수렴 단계
passed          - 입법/공포 완료
in_effect       - 시행 중
enforcement     - 집행/단속 사례 발생
unknown         - 원문에서 단계를 특정할 수 없음
```

### 절대 원칙

`risk_analysis.md`와 동일 (사실·해석·추론·제안 분리, 근거 필수, 임의 추정 금지, 한국어 출력,
`knowledge/ANALYSIS_FRAMEWORK.md` 절차 준수).

### 출력 형식 (JSON만)

```json
{
  "facts": [],
  "regulatory_stage": "unknown",
  "significance": "",
  "mission_category": ["risk_management"],
  "mission_subcategory": ["regulatory"],
  "lx_impact": [],
  "actions": [],
  "confidence": "medium",
  "evidence": [],
  "unknowns": []
}
```

이 출력은 `risk_analysis_output`을 확장한 형태이며, `regulatory_stage`를 제외한 나머지
필드는 `schemas/claude_output.schema.json`의 `risk_analysis_output`과 동일한 규칙을 따른다.

## Dynamic Block (Per-Request — 캐시하지 않음)

`risk_analysis.md`의 Dynamic Block과 동일한 입력 구조를 사용한다 (article, lx_context_excerpt,
existing_timeline_excerpt).
