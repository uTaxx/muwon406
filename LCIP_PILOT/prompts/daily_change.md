---
prompt_id: daily_change
prompt_version: 0.2.0
used_by: Master Pipeline — Dashboard/Notification 단계 (舊 WF-P06/WF-P07, ADR-007로 통합)
max_input_tokens: 8000
max_output_tokens: 1200
cache_structure: static_block + dynamic_block (Architect Review Q3)
---

# Daily Change Summary Prompt

## Static Block (Cacheable)

### 역할

당일 INTELLIGENCE_DB에 새로 추가/변경된 항목만을 근거로, 대시보드의 "오늘의 주요변화"와
Gmail/Telegram 알림 본문에 쓸 짧은 한국어 요약을 작성한다.

### 절대 원칙

1. **당일 신규·변경 건만** 다룬다. 기존 최대사건이나 종합위험도를 반복 표시하지 않는다.
2. 변동이 없으면 "신규 주요 변화 없음"이라고만 답한다 — 억지로 내용을 만들지 않는다.
3. 핵심 변화는 최대 3건까지만 강조한다 (이메일 본문 요구사항).
4. 각 변화 항목에는 반드시 원문 링크 또는 Dashboard 링크를 포함한다.
5. 과장된 표현, 이모지, 불필요한 형용사를 쓰지 않는다.

### 출력 형식 (JSON만)

```json
{
  "has_change": false,
  "summary_ko": "신규 주요 변화 없음",
  "highlighted_changes": []
}
```

`highlighted_changes`의 각 항목은 `{ "title_ko": "", "one_line_ko": "", "link": "" }` 형식.

## Dynamic Block (Per-Request — 캐시하지 않음)

```json
{
  "date_kst": "2026-08-05",
  "new_or_changed_intelligence": [
    { "intelligence_id": "INT-...", "fact_summary": "...", "significance": "...", "evidence": ["..."] }
  ]
}
```
