# Project Status

최종 갱신: 2026-08-05 (Architect Review Round 4 반영)

## 요약

TASK-001~007 완료 → Round 2(Q1~Q7) → Round 3(Q1~Q5 + TASK-004C/D/E, Knowledge Layer
완성) → **Round 4(Q1~Q3 + TASK-009~017) 반영** 완료. Round 4는 "Framework Completion"에서
"Working Product Completion"으로 방향을 전환 — 새 Framework 문서 없이 Provider
Layer/Source Adapter/Analysis Pipeline/Dashboard Widget/Notifier·Health·Cost 연동/Pilot
MVP 통합 테스트까지 전부 Mock/dry-run 기반으로 실제 동작하는 코드로 구현했다. 외부 API
실제 호출은 여전히 없음 (Anthropic/Google Drive·Sheets/n8n/이메일/Telegram 어느 것도
실제로 호출하지 않음 — 전부 `enabled=False`/`test_mode=true` 기본값 또는 fixture 주입으로
검증).

## Task 진행 상태

| Task | 상태 | 비고 |
|---|---|---|
| TASK-001~007 | ✅ 완료 | 변경 없음 (Round 4) |
| TASK-004A~E (Knowledge Layer) | ✅ 완료·동결 | Round 4에서 "Pilot에 충분" 승인, 이후 신규 Framework 문서 추가 안 함 |
| **TASK-009 Provider Layer** | ✅ 완료 (신규) | `scripts/providers/` — AIProvider/ClaudeProvider/MockProvider/미래 Provider stub |
| **TASK-010 Source Adapter** | ✅ 완료 (신규) | `scripts/adapters/` — SourceAdapter/GoogleRSSAdapter(실동작 파싱)/Naver·DART·정부·IR stub |
| **TASK-011 Analysis Pipeline** | ✅ 완료 (신규) | `scripts/pipeline/` — Collect→Normalize→Rule Filter→Classify→Knowledge Retrieve→Analyze→Validate→Generate Intelligence→Store 8단계 |
| **TASK-012 Dashboard Widget** | ✅ 완료 (신규) | `scripts/dashboard_widgets.py` — Widget 6종(Statistics 신규), `build_dashboard.py` 하위호환 유지 |
| **TASK-013 Notifier** | ✅ 완료 (신규) | `scripts/notifiers.py` — Email/Telegram, test_mode dry-run |
| **TASK-014 Source Health 연동** | ✅ 완료 (신규) | `scripts/health_tracking.py` — Adapter 실제 호출 결과 기반 판정 |
| **TASK-015 Cost Guard 연동** | ✅ 완료 (신규) | `scripts/cost_tracking.py` — Provider 사용량 기반 비용 추정 |
| **TASK-017 Pilot MVP 통합 테스트** | ✅ 완료 (신규) | `tests/test_mvp_integration.py` + `scripts/demo_mvp.py` |
| TASK-016 Natural Language Admin | ⏸ 보류 | Round 4 지시로 보류 |
| TASK-008 n8n API Deployment | ⏸ 대기 (마지막 순위) | 위 항목 전부 완성 후 진행 |
| TASK-018 | ⏸ 대기 | 변경 없음 |

## 테스트 결과

```text
$ pytest tests/ -q                                   -> 전부 PASS (148개 테스트, Round 3: 80개 → +68개)
$ python scripts/validate_config.py                  -> PASS
$ python scripts/secret_scan.py                       -> PASS
$ python scripts/bootstrap_project.py --dry-run        -> PASS
$ python scripts/demo_mvp.py                           -> PASS (Pilot MVP 10단계 전부 정상 동작, Mock 기반)
```

## Round 4에서 새로 생성/수정된 파일

**신규 패키지/모듈 (11개)**
- `scripts/providers/` (`base.py`, `mock_provider.py`, `claude_provider.py`, `future_providers.py`)
- `scripts/adapters/` (`base.py`, `google_rss_adapter.py`, `future_adapters.py`)
- `scripts/pipeline/` (`ids.py`, `normalize.py`, `rule_filter.py`, `classify.py`,
  `knowledge_retrieve.py`, `analyze.py`, `validate.py`, `generate_intelligence.py`,
  `store.py`, `collect.py`, `dashboard_feed.py`)
- `scripts/dashboard_widgets.py`, `scripts/notifiers.py`, `scripts/health_tracking.py`,
  `scripts/cost_tracking.py`, `scripts/demo_mvp.py`

**신규 문서**: `docs/decisions/ADR-009-workflow-lifecycle-policy.md`

**신규 테스트 (10개 파일, 68건)**: `test_providers.py`(14), `test_adapters.py`(9),
`test_pipeline.py`(14), `test_dashboard_widgets.py`(10), `test_cost_tracking.py`(6),
`test_health_tracking.py`(4), `test_notifiers.py`(8), `test_mvp_integration.py`(1) +
fixtures(`sample_google_news_rss.xml`, `quick_company_scan_core_only.json`)

**스키마/Config 변경**: `risk_analysis_output`에 `intelligence_categories` 필수 추가
(Round 4 Q2), `quick_company_scan.schema.json`을 Core(필수 7)/Advanced(선택 13)로 재작성
(Round 4 Q3), `config/workflow_registry.yaml`에 `lifecycle_stage`(active/deprecated)
필드 추가(Round 4 Q1).

**버그 수정 (자체 발견·수정)**: `notifiers.py`가 `config/notification.yaml`의
`email`/`telegram` 섹션이 `notifications`의 형제(sibling) 키임을 반영하지 못해 수신자
env 변수 이름을 항상 놓치던 문제를 `test_load_notification_config_resolves_real_recipient_env_names`
회귀 테스트와 함께 수정.

## 알려진 설계 결정 이력 (전체, 상세는 docs/04_DATA_AND_CONFIG_SCHEMA.md §1/§5, 각 ADR)

- ADR-006: 문서 우선순위 정책
- ADR-007: n8n Master Pipeline 통합 (11→5)
- ADR-008: Workflow ID 영속성 정책 (재배정 금지)
- ADR-009: Workflow ID Active/Deprecated/Archived 3단계 생명주기 (Round 4 Q1)
- Round 2/3/4의 각 Q 항목: `CHANGELOG.md`에 라운드별 상세 기록

## 남은 사용자 작업

`TODO.md` 참고 — 구조/테스트는 Mock 기반으로 전부 완료됐다. 실제 "동작"으로 전환하려면
Claude API Key/모델 ID 3종, Google/n8n 계정, Gmail/Telegram 계정을 사용자가 준비해야
한다. Knowledge Base 실제 리서치도 여전히 남아 있다(우선순위 확정됨).
