# Project Status

최종 갱신: 2026-08-07 (Architect Review Round 7 반영)

## 요약

TASK-001~007 → Round 2/3/4(Knowledge Layer, Provider/Adapter/Pipeline/Widget) →
Round 5(Storage/Knowledge Retrieval/Prompt Engine/Dashboard Data Provider + Quick
Company Scan 실제 서비스 + Investment Review Engine) → Round 6(Knowledge Population/
Company·Source Registry/Feature Flag/Provider Factory/데모 통합/Quality Gate) →
**Round 7("Registry 통합 + Coverage 전환 + Scenario화 + Connection Readiness 준비")
반영** 완료. 최종 목표는 **Pilot Release Candidate(RC1)**이며, Architect는 이번
라운드를 "지금까지 중 가장 품질이 높았다"고 평가(Architecture A+/Scalability A+)했다.
Round 7은 (1) Company/Source/Model/Prompt/Workflow/Config/Storage 7개 Registry를
동일 Interface로 묶는 RegistryManager를 신설하고, (2) Knowledge Quality를 "문서 개수"
에서 "8개 도메인 Coverage"로 전환하고, (3) Company Registry를 14→30개사로 확장하고,
(4) Source Registry에 Estimated Update Delay/Typical Reliability/Historical Stability
필드를 추가하고, (5) "하나의 통합 데모"를 5개 독립 Scenario로 전환하고, (6) Quality
Gate에 Registry/Report/Evidence/Reasoning Quality·Maintainability 5개 지표(100점
만점)를 추가하고, (7) 실제 API 연결 없이 Connection Readiness(Credential/환경변수/
Test Plan/Rollback Plan)를 문서화했다. 외부 API 실제 호출은 Round 7에서도 없다.

## Task 진행 상태

| Task | 상태 | 비고 |
|---|---|---|
| TASK-001~007, TASK-004A~E | ✅ 완료·동결 | 변경 없음 |
| TASK-009~017 (Round 4), Round 5 엔진 4종 | ✅ 완료 | 변경 없음(아키텍처 동결) |
| Round 6(TASK-K01/K02/K03, Feature Flag, Provider Factory, Quality Gate) | ✅ 완료 | 변경 없음 |
| **RegistryManager** | ✅ 완료 (신규) | `scripts/registries/` — 7개 Registry, 동일 Interface |
| **Knowledge Coverage** | ✅ 완료 (신규) | `scripts/knowledge_coverage.py` — 8개 도메인, 전체 평균 90.6% |
| **Company Registry 14→30개사** | ✅ 완료 (신규) | `config/company_registry.yaml` |
| **Source Registry 필드 3종** | ✅ 완료 (신규) | Estimated Update Delay/Typical Reliability/Historical Stability |
| **Scenario 5종** | ✅ 완료 (신규) | `scripts/scenarios/` — `demo_pilot.py` 삭제·대체 |
| **Quality Gate 5종 지표 추가** | ✅ 완료 (신규) | Registry/Report/Evidence/Reasoning Quality, Maintainability |
| **Connection Readiness 문서화** | ✅ 완료 (신규) | `docs/CONNECTION_READINESS.md`, 실제 호출 없음 |
| TASK-016 Natural Language Admin | ⏸ 보류 | 유지 |
| TASK-008 n8n API Deployment | ⏸ 대기 (마지막 순위) | 위 항목 전부 완성 후 진행 |
| TASK-018 | ⏸ 대기 | 변경 없음 |

## 테스트 결과

```text
$ pytest tests/ -q                                    -> 전부 PASS (335개 테스트, Round 6: 284개 → +51개)
$ python scripts/validate_config.py                   -> PASS
$ python scripts/secret_scan.py                        -> PASS
$ python scripts/bootstrap_project.py --dry-run         -> PASS
$ python scripts/scenarios/scenario_1_news_analysis.py  -> PASS (뉴스수집→...→Dashboard)
$ python scripts/scenarios/scenario_2_quick_company_scan.py -> PASS
$ python scripts/scenarios/scenario_3_investment_review.py  -> PASS (Scenario 2 자동 실행 포함)
$ python scripts/scenarios/scenario_4_policy_impact.py       -> PASS (신규 analyze_policy_impact)
$ python scripts/scenarios/scenario_5_competitor_change_detection.py -> PASS (스냅샷 diff)
$ python scripts/quality_gate.py                        -> Pilot Operational Readiness 100%, Round 7 신규 5개 지표 병행 출력
$ python scripts/knowledge_coverage.py                  -> 전체 평균 90.6%(Investment Coverage만 25% — STRATEGY_PLAYBOOK.md 미착수)
```

## Round 7에서 새로 생성/수정된 파일

**신규 모듈**
- `scripts/registries/` — `base.py`(Registry ABC), `yaml_list_registry.py`(Company/
  Source/Workflow), `model_registry_adapter.py`, `prompt_registry_adapter.py`,
  `config_registry_adapter.py`, `storage_registry_adapter.py`, `manager.py`
  (`RegistryManager`)
- `scripts/knowledge_coverage.py` — 8개 도메인 Coverage(명시적 (파일, Section) 매핑)
- `scripts/scenarios/` — `scenario_1_news_analysis.py`, `scenario_2_quick_company_scan.py`,
  `scenario_3_investment_review.py`, `scenario_4_policy_impact.py`,
  `scenario_5_competitor_change_detection.py`
- `docs/CONNECTION_READINESS.md` — Credential 체크리스트/Connection Test Plan/Rollback
  Plan(실제 호출 없음)

**중대 수정**: `scripts/providers/base.py`/`mock_provider.py`/`claude_provider.py`/
`future_providers.py`에 `analyze_policy_impact()` 신규 추상 메서드 추가(Scenario 4).
`schemas/claude_output.schema.json`에 `policy_analysis_output` 정의 추가(기존
`prompts/policy_analysis.md`를 처음으로 실제 연결). `scripts/quality_gate.py`에
Registry/Report/Evidence/Reasoning Quality/Maintainability 5개 지표 추가. `scripts/
demo_pilot.py` 삭제(Scenario 5종으로 대체). `.env.example`에 `NAVER_CLIENT_ID`/
`NAVER_CLIENT_SECRET`/`LCIP_TEST_EMAIL_RECIPIENT`/모델 3종 환경변수 보강(이미 코드가
참조하지만 예시 파일에는 없던 것들).

**Company/Source Registry 확장**: `config/company_registry.yaml` 14→30개사(LG전자/
LG화학/Saint-Gobain/AGC/NSG Group/Guardian Industries/Vitro/Schüco/REHAU/Deceuninck/
Andersen/Pella/Marvin/PPG + Claude가 30개사 목표 달성을 위해 추가 선정한 Corning/
Owens Corning, 티커는 WebSearch로 재확인). `config/sources.yaml` 11개 Source 전부에
`estimated_update_delay`/`typical_reliability`/`historical_stability` 필드 추가.

**신규 테스트**: `test_registries.py`(17), `test_knowledge_coverage.py`(8),
`test_scenarios.py`(9) + 기존 파일 확장(`test_quick_company_scan.py` +4,
`test_source_registry.py` +2, `test_providers.py` +5, `test_quality_gate.py` +13)

## 알려진 설계 결정 이력 (전체, 상세는 docs/04_DATA_AND_CONFIG_SCHEMA.md §1/§5, 각 ADR)

- ADR-006/007/008/009: 문서 우선순위 / n8n 통합 / Workflow ID 정책 / Workflow 생명주기
- Round 2~7의 각 Q 항목·추가 지시: `CHANGELOG.md`에 라운드별 상세 기록

## 남은 사용자 작업

`TODO.md` 참고 — Round 7도 여전히 Mock/dry-run 기반이다. `docs/CONNECTION_READINESS.md`의
Credential 체크리스트대로 Claude API Key/모델 ID 3종/Google/n8n/Gmail/Telegram 계정을
준비하고 `config/feature_flags.yaml`을 켜야 "실제 동작"으로 전환된다. Company Registry의
여러 TODO 필드(products/value_chain/official_website 등)와 `STRATEGY_PLAYBOOK.md`
(Investment Coverage가 25%로 낮은 주된 원인)도 다음 라운드 리서치 대상이다.
