# Project Status

최종 갱신: 2026-08-05 (Architect Review Round 3 반영)

## 요약

TASK-001~007 완료 → Architect Review Round 2(Q1~Q7) 반영 → **Round 3(Q1~Q5 + TASK-004C/D/E)
반영** 완료. Knowledge Layer(TASK-004A~E)가 TASK-009보다 먼저 전부 완료된 상태다. 외부 API
실제 호출은 여전히 없음 (Google Drive/Sheets 생성 없음, n8n 배포 없음, Claude API 실호출
없음, 이메일/Telegram 실제 발송 없음).

## Task 진행 상태

| Task | 상태 | 비고 |
|---|---|---|
| TASK-001~003 | ✅ 완료 | 변경 없음 (Round 3) |
| TASK-004 Knowledge Templates | ✅ 완료 | |
| TASK-004A Knowledge Foundation Builder | ✅ 완료 | Round 3 Q5로 `LX_HOLDINGS_CONTEXT.md`도 16계층 전부(N/A 포함)로 재구성 |
| TASK-004B Corporate Intelligence Framework | ✅ 완료 | Round 3 Q3로 mission 필드 배열화 반영 |
| **TASK-004C Knowledge Governance** | ✅ 완료 (신규) | `KNOWLEDGE_GOVERNANCE.md` 10개 규칙 + `scripts/knowledge_quality.py` |
| **TASK-004D Quick Company Scan Framework** | ✅ 완료 (신규) | `QUICK_COMPANY_SCAN_FRAMEWORK.md` 20개 항목 + `schemas/quick_company_scan.schema.json` |
| **TASK-004E Corporate Intelligence Taxonomy** | ✅ 완료 (신규) | `INTELLIGENCE_TAXONOMY.md` 19개 카테고리 + `intelligence_categories` 스키마 필드 |
| TASK-005/006 Google Drive/Sheets Tooling | ✅ 완료 (dry-run만) | 변경 없음 |
| TASK-007 n8n Workflow Scaffold | ✅ 완료 (재구성 2회) | Round 2에서 11→5 통합, Round 3에서 ID 원복(WF-P08/09/10, ADR-008) |
| TASK-009~013 | ⏸ 대기 (다음 순서) | Knowledge Layer 완료로 착수 조건 충족, 사용자 API Key 대기 |
| TASK-008 | ⏸ 대기 (마지막 순위) | Round 2 Q5 유지 |
| TASK-014~018 | ⏸ 대기 | 변경 없음 |

## 테스트 결과

```text
$ pytest tests/                                     -> 전부 PASS (80개 테스트)
$ python scripts/validate_config.py                 -> PASS
$ python scripts/secret_scan.py                      -> PASS
$ python scripts/bootstrap_project.py --dry-run       -> PASS
$ python scripts/knowledge_quality.py --verbose
    LX_HAUSYS_COMPANY_DNA.md: 0.0%
    LX_HOLDINGS_CONTEXT.md: 50.0% (N/A 계층 6개가 구조상 완료로 카운트됨)
    전체 평균: 25.0%
```

## Round 3에서 새로 생성/수정된 파일

**신규 (8개)**
- `docs/decisions/ADR-008-workflow-id-policy.md`
- `knowledge/KNOWLEDGE_GOVERNANCE.md`
- `knowledge/QUICK_COMPANY_SCAN_FRAMEWORK.md`
- `knowledge/INTELLIGENCE_TAXONOMY.md`
- `schemas/quick_company_scan.schema.json`
- `scripts/knowledge_quality.py`
- `tests/test_knowledge_templates.py`, `tests/test_knowledge_quality.py`

**n8n 파일명 원복 (ADR-008)**: `WF-P02→WF-P08-source-health.json`,
`WF-P03→WF-P09-cost-guard.json`, `WF-P04→WF-P10-natural-language-admin.json`

**주요 스키마 변경**: `mission`→`mission_category`(배열), `mission_subcategory`(배열화),
`intelligence_categories`(신규, 필수) — `schemas/intelligence.schema.json`,
`schemas/claude_output.schema.json`, `schemas/google_sheets_columns.json` 전부 반영.

**Config 변경**: `config/model_registry.yaml`(신규, 3-tier), `config/cost_policy.yaml`
(모델 tier 관리를 model_registry.yaml로 이전), `config/workflow_registry.yaml`(ID 원복).

**Knowledge 재구성**: `LX_HOLDINGS_CONTEXT.md`가 16계층 전부(해당없는 6개는 N/A) 구조로 재작성.

**코드 변경**: `scripts/claude_client.py`에 `get_model_name()` 3단계 조회 로직
(환경변수→Registry→Prompt fallback) 추가.

## 알려진 설계 결정 이력 (전체, 상세는 docs/04_DATA_AND_CONFIG_SCHEMA.md §1/§5, 각 ADR)

- ADR-006: 문서 우선순위 정책
- ADR-007: n8n Master Pipeline 통합 (11→5)
- ADR-008: Workflow ID 영속성 정책 (재배정 금지, Round 2의 재배정을 원복)
- Round 2 Q2/Q3/Q5/Q6/Q7, Round 3 Q3/Q4/Q5: 각각 스키마·모델 전략·우선순위·Knowledge 구조에 반영

## 남은 사용자 작업

`TODO.md` 참고 — Claude API Key 및 3-tier 모델 ID(classification/deep_analysis/future)
확정이 최우선(TASK-009), 이어서 Google/n8n/Gmail/Telegram 계정 준비 및 Knowledge Base
실제 리서치(우선순위 확정됨).
