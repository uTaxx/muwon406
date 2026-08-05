# Project Status

최종 갱신: 2026-08-05 (Architect Review Round 5 반영)

## 요약

TASK-001~007 → Round 2/3/4(Knowledge Layer, Provider/Adapter/Pipeline/Widget) →
**Round 5(Storage/Knowledge Retrieval/Prompt Engine/Dashboard Data Provider + Quick
Company Scan 실제 서비스 + Investment Review Engine + Technical Debt 4건) 반영** 완료.
Round 5는 "Pilot을 실제 사용할 수 있는 방향으로 고도화"가 목표였다 — Round 4의 아키텍처
5종(Provider/Adapter/Pipeline/Widget + Framework/Knowledge Layer)은 그대로 두고 그 위에
4개 하위 엔진(Storage Backend/Knowledge Retrieval Engine/Prompt Engine/Dashboard Data
Provider)을 추가했다. 외부 API 실제 호출은 여전히 없음.

## Task 진행 상태

| Task | 상태 | 비고 |
|---|---|---|
| TASK-001~007, TASK-004A~E | ✅ 완료·동결 | 변경 없음 (Round 5) |
| TASK-009~017 (Round 4) | ✅ 완료 | Provider/Adapter/Pipeline/Widget/Notifier·Health·Cost/Pilot MVP 통합 테스트 |
| **TASK-010A Storage Backend** | ✅ 완료 (신규) | `scripts/storage/` — StorageBackend/LocalJSONLStorage/GoogleSheetsStorage/FutureDatabaseStorage |
| **Source Reliability Score** | ✅ 완료 (신규) | `config/source_reliability.yaml`, `scripts/source_priority.py` |
| **TASK-009B Knowledge Retrieval Engine** | ✅ 완료 (신규) | `scripts/knowledge_engine.py` — Section/Topic/Company/Source Priority/Confidence/Last Verified 검색 |
| **TASK-009A Prompt Engine** | ✅ 완료 (신규) | `scripts/prompt_engine/` — Template→Builder→Validator→Cache, 5블록 조립 |
| **TASK-012A Dashboard Data Provider** | ✅ 완료 (신규) | `scripts/dashboard_data_provider.py` + Widget Data Layer 분리 |
| **Quick Company Scan 실제 서비스** | ✅ 완료 (신규) | `scripts/quick_company_scan.py`, `config/company_registry.yaml` |
| **Investment Review Engine** | ✅ 완료 (신규) | `scripts/investment_review.py`, `schemas/investment_review.schema.json` |
| **Technical Debt 4건** | ✅ 완료 (신규) | claude_client Mock 제거/Pricing Key 통일/Widget 반복 제거/Health Module 병합 |
| TASK-016 Natural Language Admin | ⏸ 보류 | Round 4/5 유지 |
| TASK-008 n8n API Deployment | ⏸ 대기 (마지막 순위) | 위 항목 전부 완성 후 진행 |
| TASK-018 | ⏸ 대기 | 변경 없음 |

## 테스트 결과

```text
$ pytest tests/ -q                                    -> 전부 PASS (239개 테스트, Round 4: 148개 → +91개)
$ python scripts/validate_config.py                   -> PASS
$ python scripts/secret_scan.py                        -> PASS
$ python scripts/bootstrap_project.py --dry-run         -> PASS
$ python scripts/demo_mvp.py                            -> PASS (Pilot MVP 10단계, Data Provider→Widget→Dashboard 경유)
```

## Round 5에서 새로 생성/수정된 파일

**신규 패키지/모듈**
- `scripts/storage/` (`base.py`, `local_jsonl_storage.py`, `google_sheets_storage.py`, `future_storage.py`)
- `scripts/prompt_engine/` (`template.py`, `builder.py`, `validator.py`, `cache.py`)
- `scripts/knowledge_engine.py`, `scripts/source_priority.py`
- `scripts/dashboard_data_provider.py`
- `scripts/quick_company_scan.py`, `scripts/investment_review.py`

**신규 Config/Schema**: `config/source_reliability.yaml`, `config/company_registry.yaml`,
`schemas/investment_review.schema.json`

**신규 테스트 (8개 파일, 91건)**: `test_storage.py`(10), `test_source_priority.py`(18),
`test_knowledge_engine.py`(13), `test_prompt_engine.py`(10),
`test_dashboard_data_provider.py`(4), `test_quick_company_scan.py`(12),
`test_investment_review.py`(14) + 기존 파일 확장(`test_providers.py` +4,
`test_dashboard_widgets.py` +4, `test_knowledge_quality.py` +1, `test_cost_tracking.py`
키 변경, `test_source_health.py` +4 병합)

**자체 발견·수정한 버그**: `scripts/knowledge_quality.py`가 4줄 분리 메타데이터 서식
(`LX_HAUSYS_COMPANY_DNA.md` 등)을 지원하지 않아 실제 값이 있어도 항상 "메타데이터 없음"으로
오판정하던 문제를 `scripts/knowledge_engine.py`의 통합 파서로 교체하며 함께 고쳤다
(`test_four_line_metadata_format_is_parsed_correctly` 회귀 테스트 추가).

**Technical Debt 정리**: `claude_client.call_claude_mocked()`/`ClaudeUsage`/
`ClaudeCallResult` 제거(MockProvider로 완전 대체), `model_pricing.yaml` 키를
`model_registry.yaml` tier 키와 통일(TIER_TO_PRICING_KEY 매핑 제거),
`dashboard_widgets.py`의 `RegulationWidget` 3회 반복 생성을 설정 목록으로 정리,
`scripts/health_tracking.py`를 `scripts/source_health_check.py`로 병합(파일명은
`03_BUILD_SPECIFICATION.md` 원문 기준 유지).

## 알려진 설계 결정 이력 (전체, 상세는 docs/04_DATA_AND_CONFIG_SCHEMA.md §1/§5, 각 ADR)

- ADR-006/007/008/009: 문서 우선순위 / n8n 통합 / Workflow ID 정책 / Workflow 생명주기
- Round 2~5의 각 Q 항목·추가 지시: `CHANGELOG.md`에 라운드별 상세 기록

## 남은 사용자 작업

`TODO.md` 참고 — 구조/테스트는 Mock 기반으로 전부 완료됐다. 실제 "동작"으로 전환하려면
Claude API Key/모델 ID 3종, Google/n8n 계정, Gmail/Telegram 계정을 사용자가 준비해야
한다. Quick Company Scan 대상 회사를 추가하려면 `config/company_registry.yaml`에 등록해야
한다(임의 등록 금지). Knowledge Base 실제 리서치도 여전히 남아 있다.
