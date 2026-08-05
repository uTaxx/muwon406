# Project Status

최종 갱신: 2026-08-05 (Architect Review 반영, 2차 갱신)

## 요약

LCIP Pilot 로컬 구현 라운드 1 (TASK-001~007) 완료 후, Architect Review(ChatGPT 검토, 사용자
승인)를 반영해 TASK-004A/004B를 추가 완료하고 TASK-001~007 산출물 일부를 재구성했다. 외부
API 실제 호출은 여전히 없음 (Google Drive/Sheets 생성 없음, n8n 배포 없음, Claude API 실호출
없음, 이메일/Telegram 발송 없음).

## Task 진행 상태

| Task | 상태 | 비고 |
|---|---|---|
| TASK-001 Project Scaffold | ✅ 완료 | 폴더/기본파일 생성, `bootstrap_project.py --dry-run` PASS |
| TASK-002 Core Configuration | ✅ 완료 | `validate_config.py` PASS |
| TASK-003 Data Schemas | ✅ 완료 | Architect Review Q2/Q3로 `mission_subcategory`/CHANGE_REQUEST 필드 확장 |
| TASK-004 Knowledge Templates | ✅ 완료 | 7개 템플릿 |
| **TASK-004A Knowledge Foundation Builder** | ✅ 완료 (신규) | 16계층 Taxonomy로 `LX_HAUSYS_COMPANY_DNA.md`/`LX_HOLDINGS_CONTEXT.md` 재구성 |
| **TASK-004B Corporate Intelligence Framework** | ✅ 완료 (신규) | `KNOWLEDGE_POLICY`/`MISSION_FRAMEWORK`/`SOURCE_PRIORITY`/`ANALYSIS_FRAMEWORK`/`INVESTMENT_FRAMEWORK` 5개 문서 |
| TASK-005 Google Drive Tooling | ✅ 완료 (dry-run만) | 변경 없음 |
| TASK-006 Google Sheets Tooling | ✅ 완료 (dry-run만) | Q2로 4개 탭 draft→confirmed 전환 |
| TASK-007 n8n Workflow Scaffold | ✅ 완료 (재구성) | Q4/ADR-007로 11개→5개 워크플로우(Master Pipeline 통합) |
| TASK-008 n8n API Deployment Tooling | ⏸ 대기 (마지막 순위로 변경) | Q5: 실제 Workflow 로직 완성 후 진행 |
| TASK-009~013 | ⏸ 대기 (우선순위로 변경) | Q5: TASK-008보다 먼저 진행 예정 |
| TASK-014~018 | ⏸ 대기 | 변경 없음 |

## 테스트 결과

```text
$ python scripts/bootstrap_project.py --dry-run   -> PASS
$ python scripts/validate_config.py               -> PASS
$ python scripts/secret_scan.py                    -> PASS
$ pytest tests/                                     -> 전부 PASS (57개 테스트)
```

## 생성/수정된 파일 (Architect Review 반영분 요약)

**신규 생성**
- `docs/decisions/ADR-006-document-priority-policy.md`, `ADR-007-n8n-workflow-consolidation.md`
- `knowledge/KNOWLEDGE_POLICY.md`, `MISSION_FRAMEWORK.md`, `SOURCE_PRIORITY.md`,
  `ANALYSIS_FRAMEWORK.md`, `INVESTMENT_FRAMEWORK.md`
- `n8n/workflows/WF-P01-master-pipeline.json`, `WF-P02-source-health.json`,
  `WF-P03-cost-guard.json`, `WF-P04-natural-language-admin.json`
- `tests/test_claude_client.py`

**재구성/대체**
- `n8n/workflows/`: 舊 11개 파일(WF-P01~P10, WF-P99) → 5개(WF-P01,02,03,04,99) —
  WF-P99만 이름 유지, 나머지는 통합/재번호
- `knowledge/LX_HAUSYS_COMPANY_DNA.md`, `LX_HOLDINGS_CONTEXT.md` — 16계층 Taxonomy로 전면 재작성
- `prompts/*.md` 6개 전부 — Static Block(캐시 대상)/Dynamic Block(요청별) 구조로 재작성

**주요 수정**
- `schemas/google_sheets_columns.json`, `config/sheet_structure.yaml` — 4개 탭 컬럼 확장, draft→confirmed
- `schemas/change_request.schema.json` — `request_source`/`requested_by`/`approved_by`/`approved_at`/`implemented_at` 추가
- `schemas/intelligence.schema.json`, `schemas/claude_output.schema.json` — `mission_subcategory` 추가
- `config/cost_policy.yaml` — 모델 tier 권장값, Prompt Cache 구조 설정 추가
- `config/workflow_registry.yaml` — 5-워크플로우 구조로 재작성
- `scripts/claude_client.py` — `split_prompt_blocks()`, `build_cached_messages()` 추가
- `scripts/build_dashboard.py` — Mode1(single)/Mode2(split) 이원화
- `tests/test_n8n_json.py`, `tests/test_dashboard.py` — 위 변경사항 반영
- `CLAUDE.md`, `docs/04_DATA_AND_CONFIG_SCHEMA.md`, `docs/05_ACCEPTANCE_TESTS.md` — 문서 우선순위/충돌 로그/완료조건 갱신
- `knowledge/GROUP_RISK_MAP.md`, `GROUP_OPPORTUNITY_MAP.md`, `STRATEGY_PLAYBOOK.md`,
  `PLATFORM_CONSTITUTION.md`, `LX_HAUSYS_VALUE_CHAIN.md` — Mission Framework/신규 워크플로우 명칭 참조 갱신

## 알려진 설계문서 충돌 및 Architect Review 반영 (상세는 docs/04_DATA_AND_CONFIG_SCHEMA.md §1, §5)

1. 문서 우선순위 고정 — ADR-006 (BUILD_SPEC → BLUEPRINT → MANUAL → HANDOVER)
2. Google Sheets 4개 탭 컬럼 확정 — Architect Review Q2
3. Claude 모델 tier 권장 및 Prompt Caching 구조 — Architect Review Q3
4. n8n 11개 → 5개 워크플로우 통합 — ADR-007
5. TASK 우선순위 변경 (TASK-008 마지막 순위) — Architect Review Q5
6. Knowledge 파일·출처 우선순위 확정 — Architect Review Q6
7. Dashboard Mode1/Mode2 이원화 — Architect Review Q7

## 남은 사용자 작업

`TODO.md` 참고 — Claude API Key/모델 확정이 최우선(TASK-009), 이어서 Google/n8n/Gmail/Telegram
계정·인증 준비 및 승인 항목.
