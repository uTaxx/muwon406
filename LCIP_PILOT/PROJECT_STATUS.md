# Project Status

최종 갱신: 2026-08-05 (Architect Review Round 6 반영)

## 요약

TASK-001~007 → Round 2/3/4(Knowledge Layer, Provider/Adapter/Pipeline/Widget) →
Round 5(Storage/Knowledge Retrieval/Prompt Engine/Dashboard Data Provider + Quick
Company Scan 실제 서비스 + Investment Review Engine) → **Round 6("Engine Development"에서
"Working Product"로 전환) 반영** 완료. Round 6는 새 Engine/Framework/Layer 추가를
절대 금지하고, 대신 (1) Knowledge Base 5개 문서에 실제 공개정보 기반 내용을 채우고,
(2) Company Registry(14개사)/Source Registry(11개 Source)를 Pilot 수준으로 구축하고,
(3) News Adapter/Claude Provider를 "구조만"에서 "실제 코드 존재, Feature Flag로 차단"으로
전환하고, (4) 데모를 2개에서 1개(`scripts/demo_pilot.py`)로 통합하고, (5) Coverage 대신
품질을 측정하는 Quality Gate(`scripts/quality_gate.py`)를 신설하고, (6) 중복 구조·데드
코드를 감사·정리했다. 외부 API 실제 호출은 여전히 없다 — Feature Flag(`config/
feature_flags.yaml`)가 전부 `false`로 유지되는 한 실제 네트워크 호출에 도달하지 않는다.

## Task 진행 상태

| Task | 상태 | 비고 |
|---|---|---|
| TASK-001~007, TASK-004A~E | ✅ 완료·동결 | 변경 없음 |
| TASK-009~017 (Round 4), Round 5 엔진 4종 | ✅ 완료 | 변경 없음(아키텍처 동결) |
| **TASK-K01 Knowledge Population** | ✅ 완료 (신규) | Knowledge Quality Score 평균 **95.8%**(Round 5: 25%) |
| **TASK-K02 Company Registry** | ✅ 완료 (신규) | `config/company_registry.yaml` 14개사, K02 필수 필드 구조 |
| **TASK-K03 Source Registry** | ✅ 완료 (신규) | `config/sources.yaml` 11개 Source, authentication/rate_limit 필드 |
| **TASK-010 실제 RSS Parser + Feature Flag** | ✅ 완료 (신규) | `config/feature_flags.yaml`, `scripts/feature_flags.py` |
| **TASK-009 실제 ClaudeProvider + Provider Factory** | ✅ 완료 (신규) | `_call_anthropic()` 실제 코드 존재(2중 게이트로 차단), `scripts/providers/factory.py` |
| **TASK-017 데모 통합(2→1)** | ✅ 완료 (신규) | `scripts/demo_pilot.py` — `demo_mvp.py`/`demo_quick_scan.py` 삭제·통합 |
| **Quality Gate 모듈** | ✅ 완료 (신규) | `scripts/quality_gate.py` — 6개 지표 |
| **데드코드/중복 구조 감사** | ✅ 완료 (신규) | `pipeline/store.py` 삭제, `claude_client.build_cached_messages()` 삭제, `build_dashboard.py` 중복 JSON 로딩 제거 |
| TASK-016 Natural Language Admin | ⏸ 보류 | 유지 |
| TASK-008 n8n API Deployment | ⏸ 대기 (마지막 순위) | 위 항목 전부 완성 후 진행 |
| TASK-018 | ⏸ 대기 | 변경 없음 |

## 테스트 결과

```text
$ pytest tests/ -q                                    -> 전부 PASS (284개 테스트, Round 5: 265개 → +19개, 데드코드 정리로 -3건 삭제 포함)
$ python scripts/validate_config.py                   -> PASS
$ python scripts/secret_scan.py                        -> PASS
$ python scripts/bootstrap_project.py --dry-run         -> PASS
$ python scripts/demo_pilot.py                          -> PASS (통합 데모 10단계: 뉴스수집→...→Telegram Preview)
$ python scripts/quality_gate.py                        -> Pilot Operational Readiness 100%(7개 구조적 점검 항목 전부 통과)
```

## Round 6에서 새로 생성/수정된 파일

**신규 모듈**
- `scripts/feature_flags.py` + `config/feature_flags.yaml` — 전역 안전장치(4개 플래그, 전부 `false`)
- `scripts/providers/factory.py` — `get_default_provider()`(API Key + Flag 둘 다 참일 때만 ClaudeProvider)
- `scripts/demo_pilot.py` — 통합 데모(기존 `demo_mvp.py`+`demo_quick_scan.py` 대체)
- `scripts/quality_gate.py` — Knowledge Quality/Registry Completion/Public Source Coverage/
  Source Freshness/Mock Dependency/Pilot Operational Readiness 6개 지표

**중대 수정**: `scripts/providers/claude_provider.py:_call_anthropic()` — 실제 `anthropic`
SDK 호출 코드로 교체(모델은 여전히 `claude_client.get_model_name()`으로 조회, 하드코딩
없음). `feature_flags.claude_api_enabled=False`인 한 SDK import조차 하지 않고
`NotImplementedError`로 멈춘다. `scripts/adapters/google_rss_adapter.py`의 `enabled`
기본값이 하드코딩 `False`에서 `feature_flags.is_enabled("real_network_calls")`로 전환.

**Knowledge Base 실제 내용 작성(TASK-K01)**: `knowledge/LX_HAUSYS_COMPANY_DNA.md`,
`LX_HAUSYS_VALUE_CHAIN.md`, `LX_HOLDINGS_CONTEXT.md`, `GROUP_RISK_MAP.md`,
`GROUP_OPPORTUNITY_MAP.md` 5개 문서 전면 리라이트(WebSearch로 확인된 사실만, 미확인
항목은 `draft`/TODO 유지) — Knowledge Quality Score 평균 25% → **95.8%**.

**Registry 구축**: `config/company_registry.yaml`(1개사 → 14개사, K02 필드),
`config/sources.yaml`(4개 → 11개 Source, authentication/rate_limit 필드).

**신규 테스트**: `test_feature_flags.py`(5), `test_source_registry.py`(6),
`test_quality_gate.py`(14) + 기존 파일 확장(`test_adapters.py` +2, `test_providers.py`
+8, `test_quick_company_scan.py` +5)

**데드코드/중복 구조 정리**: `scripts/pipeline/store.py`(하위호환 wrapper, 실제 호출자가
자기 테스트뿐이었음) 삭제 + `tests/test_pipeline.py`의 관련 테스트 2건 제거(대체 커버리지는
`tests/test_storage.py`에 이미 존재). `claude_client.build_cached_messages()`(Round 5부터
`prompt_engine.PromptBuilder`로 완전히 대체되어 미사용) 삭제. `build_dashboard.py`가
JSON 파일을 직접 `json.loads()`하던 것을 `StaticJSONDataProvider`로 교체(중복 구현 제거).
`future_providers.py`/`future_adapters.py`/`future_storage.py`(Round 4/5가 승인한 확장
지점 stub)에는 "Pilot 데모가 호출하지 않는다"는 감사 표시를 추가했다 — 삭제 후보 아님.

## 알려진 설계 결정 이력 (전체, 상세는 docs/04_DATA_AND_CONFIG_SCHEMA.md §1/§5, 각 ADR)

- ADR-006/007/008/009: 문서 우선순위 / n8n 통합 / Workflow ID 정책 / Workflow 생명주기
- Round 2~6의 각 Q 항목·추가 지시: `CHANGELOG.md`에 라운드별 상세 기록

## 남은 사용자 작업

`TODO.md` 참고 — Round 6은 여전히 Mock/dry-run 기반이다. `config/feature_flags.yaml`의
4개 플래그를 켜고 Claude API Key/모델 ID 3종, Google/n8n 계정, Gmail/Telegram 계정을
준비해야 "실제 동작"으로 전환된다. Company Registry의 여러 TODO 필드(ticker/products/
value_chain/official_website 등)도 다음 라운드 리서치 대상이다.
