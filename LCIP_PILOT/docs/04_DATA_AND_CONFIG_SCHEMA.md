# 04. Data & Config Schema — 통합본 및 설계문서 충돌 로그

이 문서는 `03_BUILD_SPECIFICATION.md`(TASK-003, TASK-006), `02_SYSTEM_BLUEPRINT.md`(§6),
`DEVELOPMENT_MANUAL_REFERENCE.md`(§4)에 흩어져 있던 데이터/설정 스키마를 하나로 정리하고,
문서 간 불일치를 명시적으로 기록한다. **충돌이 있을 경우 이 문서의 "채택 결과" 열이 최종
기준이다.**

---

## 1. 설계문서 충돌 로그

| # | 충돌 내용 | 03_BUILD_SPECIFICATION.md | 다른 문서 | 채택 결과 |
|---|---|---|---|---|
| 1 | 로컬 루트 폴더명 | `LCIP_PILOT/` (대문자), 번호매김 docs(01~05), `output/`,`logs/`,`archive/`,`dashboard/` 최상위 | Handover/Manual: `lcip-pilot/`(소문자), `templates/`,`workflows/` 최상위, 번호매김 docs 없음 | **03_BUILD_SPECIFICATION.md 구조 채택.** 다른 문서 원문은 `docs/`에 참고용으로 보존 |
| 2 | Google Drive 폴더 구조 | TASK-005: `00_Project/,01_Knowledge/,02_Data/,03_Dashboard/,04_Reports/,05_Archive/,06_Admin/` (7개) | Blueprint §5: `00_GOVERNANCE/,01_KNOWLEDGE_BASE/,02_SOURCE_LIBRARY/,03_PROMPTS/,04_TEMPLATES/,05_OUTPUT/,06_LOGS/,07_HANDOVER/` (8개) | **TASK-005 구조 채택** → `config/drive_structure.yaml`. Blueprint 구조는 참고 각주로만 유지 |
| 3 | Google Sheets 탭 개수 | TASK-006: 11개 탭 (`CHANGE_LOG` 포함) | Manual §4: 10개 (CHANGE_LOG 없음) / Blueprint §6: 7개만 컬럼 상세 | **11개 탭 전부 생성.** 컬럼 미문서화 4개 탭(`SENT_HISTORY`,`ERROR_LOG`,`CHANGE_REQUEST`,`CHANGE_LOG`)은 아래 §3에서 초안 작성, `status: draft` 표시 |
| 4 | SOURCE_HEALTH 필드명 | TASK-003 스키마: `checked_at`,`error_message`,`latest_reference_date`,`consecutive_failures`,`recovery_action` 등 | Blueprint §6.6: `last_checked_at`(=checked_at), `error_message` 없음 | **TASK-003의 더 상세한 필드셋 채택** (아래 §2.3) |

---

## 2. Data Schema (스키마 파일: `schemas/*.schema.json`)

### 2.1 Article (`schemas/article.schema.json`)

TASK-003 필수필드: `article_id, topic_id, title_original, title_ko, source_name, source_type,
source_url, canonical_url, published_at, collected_at, language, country, summary_ko,
litigation_amount_total, litigation_currency, litigation_amount_total_usd, claimant_count,
average_amount_per_person_usd, related_companies, related_lx_companies, event_type,
confidence_score, source_reliability_grade, duplicate_group_id, is_new_change, status`

계산규칙: `average_amount_per_person_usd = litigation_amount_total_usd ÷ claimant_count`.
총액 또는 원고 수가 없으면 `null` — AI가 임의로 추정하지 않는다.

### 2.2 Intelligence (`schemas/intelligence.schema.json`)

필수필드: `intelligence_id, article_ids, mission, fact_summary, verified_facts,
ai_interpretation, ai_inference, lx_impact, recommended_actions, unknowns, confidence_score,
evidence, created_at, prompt_version, knowledge_version`

### 2.3 Source Health (`schemas/source_health.schema.json`)

필수필드(TASK-003 기준 채택): `source_id, checked_at, last_success_at, http_status,
response_ms, record_count, latest_reference_date, health_status, consecutive_failures,
error_type, error_message, recovery_action`

상태값: `HEALTHY, DEGRADED, STALE, BROKEN_LINK, SCHEMA_CHANGED, AUTH_ERROR, RATE_LIMITED,
CONTENT_INVALID, ANOMALY`

### 2.4 Change Request (`schemas/change_request.schema.json`)

필수필드(자연어 관리자 출력 예시 기준): `request_id, intent, target, changes[], affected_workflows,
estimated_cost_impact, risks, requires_approval, status`. `status`는
`DRAFT | PENDING_APPROVAL | APPROVED | REJECTED | APPLIED` 중 하나.

### 2.5 Claude Output (`schemas/claude_output.schema.json`)

Master Pipeline의 Rule Filter/AI Analyze 단계(舊 WF-P04 Relevance Classifier / WF-P05 Risk
Analysis, ADR-007로 통합)의 공용 출력 포맷 검증 스키마.
relevance: `relevant, relevance_score, mission, mission_subcategory, related_companies, reason, needs_deep_analysis`.
risk analysis: `facts, significance, mission_subcategory, lx_impact, actions, confidence, evidence, unknowns`.
`mission_subcategory`는 Architect Review Q3(2026-08-05) 반영, `knowledge/MISSION_FRAMEWORK.md` 기준.

---

## 3. Google Sheets 컬럼 (스키마 파일: `schemas/google_sheets_columns.json`)

11개 탭 전부의 컬럼을 담는다. 문서화된 7개(CONFIG_MASTER, TOPIC_CONFIG, SOURCE_REGISTRY,
ARTICLE_DB, INTELLIGENCE_DB, SOURCE_HEALTH, COST_LOG)는 Blueprint §6 / TASK-003 기준.
아래 4개는 처음엔 초안(draft)이었으나 **Architect Review Q2(2026-08-05)로 컬럼이 확장되어
`status: confirmed`로 확정**되었다:

- **SENT_HISTORY**: `sent_id, intelligence_id, channel, recipient, sent_at, dedupe_key,
  status, workflow_id, topic_id, subject, content_hash, delivery_latency_ms`
- **ERROR_LOG**: `error_id, workflow_id, node_name, error_type, error_message, occurred_at,
  resolved, resolution_note, severity, retry_count, stack_trace, first_occurred,
  last_occurred`
- **CHANGE_REQUEST**: §2.4 Change Request 스키마와 동일 컬럼 + `created_at, decided_at,
  decided_by, request_source, requested_by, approved_by, approved_at, implemented_at`
- **CHANGE_LOG**: `change_id, entity_type, entity_id, before_version, after_version,
  change_request_id, applied_at, change_summary, rollback_version, implemented_by`

`INTELLIGENCE_DB`에는 `mission_subcategory` 컬럼이 추가되었다 (Architect Review Q3).

---

## 4. Config 파일 요약 (`config/*.yaml`)

| 파일 | 목적 |
|---|---|
| `project.yaml` | 프로젝트 메타(타임존, pilot_mode, 정보 등급, 출력 언어) |
| `topics.yaml` | 모니터링 Topic 정의 (TOP-0001 등) |
| `sources.yaml` | 수집 Source Registry (RSS/API 엔드포인트, 신뢰등급) |
| `cost_policy.yaml` | Claude API 예산·토큰 한도·단계별 통제 |
| `notification.yaml` | 발송 시간대·채널 on/off·test_mode |
| `drive_structure.yaml` | Google Drive 폴더 트리 (§1 충돌 #2 채택 결과 반영) |
| `sheet_structure.yaml` | Google Sheets 11개 탭·컬럼 정의 (§3 반영, 전부 confirmed) |
| `workflow_registry.yaml` | n8n 워크플로우 5개(ADR-007) ID·이름·의존관계·기본 active 상태 |
| `model_pricing.yaml` | Claude 모델별 단가 Registry (TASK-015 Cost Guard용, 하드코딩 금지 원칙 충족) |

모든 Config 값은 `scripts/validate_config.py`로 YAML 문법·필수값·ID 중복을 검증한다.

---

## 5. Architect Review 반영사항 (2026-08-05)

TASK-001~007 검토 후 Architect Review로 아래 결정이 추가되었다. 상세 근거는 각 ADR 참고.

| Q | 결정 요약 | 근거 문서 |
|---|---|---|
| Q1 | 문서 우선순위 고정 (BUILD_SPEC → BLUEPRINT → MANUAL → HANDOVER) | `decisions/ADR-006-document-priority-policy.md` |
| Q2 | Sheets 4개 draft 탭 컬럼 확정 (`confirmed`로 전환) | 본 문서 §3 |
| Q3 | Claude 모델 tier 권장(Haiku/Sonnet), Prompt를 Static/Dynamic Block으로 분리 | `config/cost_policy.yaml`, `prompts/*.md`, `scripts/claude_client.py` |
| Q4 | n8n 11개 워크플로우 → 5개(Master Pipeline + Source Health + Cost Guard + NL Admin + Error Handler)로 통합 | `decisions/ADR-007-n8n-workflow-consolidation.md` |
| Q5 | TASK 우선순위 변경: TASK-009→010→011→012→013→TASK-008(마지막) | `TODO.md` |
| Q6 | Knowledge 파일 우선순위 및 출처 우선순위 확정 | `knowledge/KNOWLEDGE_POLICY.md`, `knowledge/SOURCE_PRIORITY.md` |
| Q7 | Dashboard Mode1(Single HTML, 기본)/Mode2(분리 Export) 이원화 | `scripts/build_dashboard.py` |
| 추가 | TASK-004A(Knowledge Foundation Builder), TASK-004B(Corporate Intelligence Framework) 신설 | `knowledge/KNOWLEDGE_POLICY.md`, `knowledge/MISSION_FRAMEWORK.md` 등 5개 신규 문서 |
