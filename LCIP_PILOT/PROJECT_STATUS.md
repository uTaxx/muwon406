# Project Status

최종 갱신: 2026-08-07 (Architect Review Round 8 반영)

## 요약

TASK-001~007 → Round 2/3/4(Knowledge Layer, Provider/Adapter/Pipeline/Widget) →
Round 5(Storage/Knowledge Retrieval/Prompt Engine/Dashboard Data Provider + Quick
Company Scan 실제 서비스 + Investment Review Engine) → Round 6(Knowledge Population/
Company·Source Registry/Feature Flag/Provider Factory/데모 통합/Quality Gate) →
Round 7(Registry 통합/Coverage 전환/Scenario화/Connection Readiness 준비) →
**Round 8("Architecture 중심에서 Product 중심으로 전환 완료 — Pilot RC1을 향한 마지막
다듬기") 반영** 완료. Architect는 Round 7을 승인하며 이번 라운드부터 "전략팀 시연
관점에서만 개발한다. 새 기능보다 사용성/품질/완성도를 우선한다. 실제 API 호출은 계속
금지한다"고 지시했다. Round 8은 (1) RC1 정의를 ADR-010으로 고정하고("실제 API 없이도
전략팀 데모가 가능한 수준" = Mock+Feature Flag+실제 Pipeline+실제 Registry+실제
Dashboard), (2) Quick Company Scan을 Architect가 지정한 8단계 전체 파이프라인(Input→
Company Registry→Knowledge Retrieval→Source Selection→Financial Provider(Mock)→
Analysis Pipeline→Investment Review→Dashboard Widget→Export)으로 완성하고, (3) Company
Intelligence Score(7개 하위 점수, 100점 만점)를 신설하고, (4) Dashboard를 "HTML
Viewer"에서 Architect 지정 6개 Widget 우선순위(Today's Intelligence→Critical Risk→
Future Opportunity→Quick Company Scan→Investment Review→Source Health)의 Executive
Dashboard로 재구성하고, (5) Knowledge Coverage에 Company/Country/Industry 3개 지표를
추가하고, (6) RegistryManager에 Validation/Integrity Check/Dependency Check를 추가해
Project Boot(`bootstrap_project.py`) 시 8개 Registry 전체를 검증하게 하고, (7) Technical
Debt Registry를 신설(Severity/Priority/Estimated Time/Owner)하고, (8) Quality Gate에
Architectural Stability/Operational Simplicity/Executive Usability/AI Reasoning
Readiness 4개 지표를 추가했다. "새로운 Framework는 더 이상 만들지 않는다"는 지시에 따라
모든 추가는 기존 패턴(Provider/Registry/Widget Layer) 재사용이며, 외부 API 실제 호출은
Round 8에서도 없다.

## Task 진행 상태

| Task | 상태 | 비고 |
|---|---|---|
| TASK-001~007, TASK-004A~E | ✅ 완료·동결 | 변경 없음 |
| TASK-009~017 (Round 4), Round 5 엔진 4종 | ✅ 완료 | 변경 없음(아키텍처 동결) |
| Round 6/7 전체 | ✅ 완료 | 변경 없음(아키텍처 동결) |
| **ADR-010 Release Policy (RC1 정의)** | ✅ 완료 (신규) | `docs/decisions/ADR-010-release-policy.md` |
| **Quick Company Scan 8단계 파이프라인 완성** | ✅ 완료 (신규) | Knowledge Retrieval/Financial Provider(Mock)/Export 단계 추가 |
| **Company Intelligence Score** | ✅ 완료 (신규) | `scripts/company_intelligence_score.py` — 7개 하위 점수 |
| **Executive Dashboard 6개 Widget 재구성** | ✅ 완료 (신규) | `scripts/dashboard_widgets.py` 전면 재작성 |
| **Knowledge Coverage 3종 추가** | ✅ 완료 (신규) | Company/Country/Industry Coverage |
| **RegistryManager Validation/Integrity/Dependency Check** | ✅ 완료 (신규) | Project Boot 시 8개 Registry 전체 검증 |
| **Technical Debt Registry** | ✅ 완료 (신규) | `config/technical_debt_registry.yaml`, 8번째 Registry |
| **Quality Gate 4종 지표 추가** | ✅ 완료 (신규) | Architectural Stability/Operational Simplicity/Executive Usability/AI Reasoning Readiness |
| TASK-016 Natural Language Admin | ⏸ 보류 | 유지 |
| TASK-008 n8n API Deployment | ⏸ 대기 (마지막 순위) | 위 항목 전부 완성 후 진행 |
| TASK-018 | ⏸ 대기 | 변경 없음 |

## 테스트 결과

```text
$ pytest tests/ -q                                    -> 전부 PASS (387개 테스트, Round 7: 335개 → +52개)
$ python scripts/validate_config.py                   -> PASS
$ python scripts/secret_scan.py                        -> PASS
$ python scripts/bootstrap_project.py --dry-run         -> PASS (Registry 8개 전체 검증 통과, Round 8 신규)
$ python scripts/scenarios/scenario_1_news_analysis.py  -> PASS
$ python scripts/scenarios/scenario_2_quick_company_scan.py -> PASS (Knowledge Retrieval 단계 추가)
$ python scripts/scenarios/scenario_3_investment_review.py  -> PASS (Financial Provider(Mock)+Company Intelligence Score+Export 추가)
$ python scripts/scenarios/scenario_4_policy_impact.py       -> PASS
$ python scripts/scenarios/scenario_5_competitor_change_detection.py -> PASS
$ python scripts/quality_gate.py                        -> Pilot Operational Readiness 100%, Round 7/8 신규 9개 지표 병행 출력(Round 8 4종 전부 100.0)
$ python scripts/knowledge_coverage.py                  -> 도메인 8종 평균 90.6% + Registry Coverage 3종(Company 3.3%/Country 22.2%/Industry 3.6%, 정직한 실측치)
```

## Round 8에서 새로 생성/수정된 파일

**신규 모듈**
- `docs/decisions/ADR-010-release-policy.md` — RC1 정의 고정
- `scripts/company_intelligence_score.py` — Company Intelligence Score(7개 하위 점수)
- `scripts/financial_provider.py` — `FinancialDataProvider`(ABC)/`MockFinancialDataProvider`
  (기존 Provider Layer 패턴 재적용, 새 Framework 아님 — ADR-010에 근거 명시)
- `scripts/registries/validation.py` — Validation/Integrity Check/Dependency Check
  순수 함수(`RegistryManager.validate()`/`check_integrity()`/`check_dependencies()`/
  `validate_all()`이 위임)
- `config/technical_debt_registry.yaml` — Technical Debt Registry(7건, Severity/
  Priority/Estimated Time/Owner/Status 필드), `TechnicalDebtRegistry`(기존
  `YAMLListRegistry` 재사용)로 RegistryManager의 8번째 Registry로 등록

**중대 수정**
- `scripts/quick_company_scan.py`: `retrieve_knowledge_for_company()`,
  `export_quick_scan_report()` 신규. `generate_company_intelligence()`에
  `knowledge_excerpt` 파라미터 추가(하위호환 기본값 `""`).
- `scripts/providers/{base,mock_provider,claude_provider,future_providers}.py`:
  `quick_company_scan()`에 `knowledge_excerpt` 파라미터 추가.
- `scripts/scenarios/scenario_2_quick_company_scan.py`: Knowledge Retrieval 단계
  추가(4단계→5단계).
- `scripts/scenarios/scenario_3_investment_review.py`: Financial Provider(Mock)→
  Company Intelligence Score→Dashboard Widget 저장→Export까지 전체 재작성(6~8단계
  추가). Scenario 1과 동일한 `output/pilot_data/` 디렉터리를 공유하도록 변경(Executive
  Dashboard가 두 Scenario 산출물을 함께 읽기 위함).
- `scripts/dashboard_widgets.py`/`scripts/pipeline/dashboard_feed.py`/
  `scripts/dashboard_data_provider.py`/`scripts/build_dashboard.py`/
  `dashboard/{template.html,app.js,sample_data.json}`: 기존 소송·규제 특화 Widget
  6종을 전부 제거하고 Architect 지정 6개 Widget(Today's Intelligence/Critical Risk/
  Future Opportunity/Quick Company Scan/Investment Review/Source Health)으로 재구성.
- `scripts/knowledge_coverage.py`: `company_coverage()`/`country_coverage()`/
  `industry_coverage()`/`registry_coverage()` 추가(기존 8개 도메인 Coverage는 그대로,
  Quality Gate의 Evidence Quality 계산식은 변경하지 않음).
- `scripts/registries/{manager,yaml_list_registry,__init__}.py`: `TechnicalDebtRegistry`
  추가(7→8개 Registry), `RegistryManager.validate()`/`check_integrity()`/
  `check_dependencies()`/`validate_all()` 추가.
- `scripts/bootstrap_project.py`: Project Boot 시 `RegistryManager.validate_all()` 호출.
- `scripts/quality_gate.py`: Architectural Stability(패키지 집합 회귀 감시)/Operational
  Simplicity(5개 Scenario 서브프로세스 실행 실측)/Executive Usability(6개 Widget 섹션
  렌더링 실측)/AI Reasoning Readiness(ClaudeProvider 구조적 구현 확인) 4개 지표 추가.

**신규 테스트**: `test_company_intelligence_score.py`(10), `test_financial_provider.py`(4)
+ 기존 파일 확장(`test_registries.py` +13, `test_knowledge_coverage.py` +6,
`test_quick_company_scan.py` +5, `test_scenarios.py` +4, `test_dashboard*.py` 전면
재작성, `test_quality_gate.py` +8, `test_config.py` +1)

## 알려진 설계 결정 이력 (전체, 상세는 docs/04_DATA_AND_CONFIG_SCHEMA.md §1/§5, 각 ADR)

- ADR-006/007/008/009/010: 문서 우선순위 / n8n 통합 / Workflow ID 정책 / Workflow
  생명주기 / Release Policy(RC1 정의)
- Round 2~8의 각 Q 항목·추가 지시: `CHANGELOG.md`에 라운드별 상세 기록

## 남은 사용자 작업

`TODO.md` 참고 — Round 8도 여전히 Mock/dry-run 기반이다. `docs/CONNECTION_READINESS.md`의
Credential 체크리스트대로 Claude API Key/모델 ID 3종/Google/n8n/Gmail/Telegram 계정을
준비하고 `config/feature_flags.yaml`을 켜야 "실제 동작"(RC2)으로 전환된다. Company
Registry의 여러 TODO 필드(products/value_chain/official_website 등), Company/Industry
Coverage가 아직 낮은 것(LX_HAUSYS 1개사만 Knowledge 보유), `STRATEGY_PLAYBOOK.md`
(Investment Coverage 25%)도 다음 라운드 리서치 대상이다 — 전부
`config/technical_debt_registry.yaml`에 실제 항목으로 등록되어 있다.
