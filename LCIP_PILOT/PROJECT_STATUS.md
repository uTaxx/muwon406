# Project Status

최종 갱신: 2026-08-07 (Architect Review Round 9 반영)

## 요약

TASK-001~007 → Round 2~7(Knowledge Layer/Provider·Adapter·Pipeline·Widget/Storage·
Prompt Engine/Knowledge Population·Registry·Feature Flag·Quality Gate/Registry
Engine·Coverage·Scenario화) → Round 8(RC1 정의 고정·Quick Company Scan 8단계 완성·
Company Intelligence Score·Executive Dashboard 6 Widget·Registry 검증·Technical Debt
Registry·Quality Gate 9종) → **Round 9("사용 가능한 Pilot") 반영** 완료. Architect는
Round 8까지의 결과로 "Pilot Architecture는 충분히 안정되었다"고 판단하고, 이번 라운드부터
**Platform Architect가 아니라 Product Owner 관점**으로 전환한다고 선언했다 — "새로운 구조,
Framework, Registry, Layer를 추가하지 않는다. 더 이상 설계하지 않는다. 더 이상 확장하지
않는다. 실제 사용하는 입장에서 완성도를 높인다."

Sprint 우선순위 5개(Quick Company Scan → News Intelligence → Investment Review →
Executive Dashboard → Email Preview)만 다뤘고, 이 외 기능은 이번 Sprint에서 구현하지
않았다. 가장 큰 성과는 **MockProvider가 Round 6이 이미 리서치해 둔 LX Hausys 실제
Knowledge를 그동안 전혀 쓰지 않고 버리고 있었다는 사실을 발견하고 고친 것**이다 — 코드는
다 있었지만 실제로 연결되지 않고 있던 결함을, "직접 실행해서 결과물을 읽어보는" 이번
라운드의 사용자 검증 방식이 아니었다면 찾기 어려웠다. 새로운 구조/Framework/Registry/
Layer는 추가하지 않았고(지시 그대로), 외부 API 실제 호출도 Round 9에서 없다.

## Round 9에서 다룬 5개 우선순위

| 순위 | 기능 | 상태 | 핵심 변경 |
|---|---|---|---|
| 1 | Quick Company Scan | ✅ 완성도 개선 | MockProvider 실제 Knowledge 반영, Export 전체 재작성(Core 7 필드+Investment Review 세부) |
| 2 | News Intelligence | ✅ 완성 | Scenario 1에 Email Preview 단계 추가(6→7단계, 새 Notifier 구조 없음) |
| 3 | Investment Review | ✅ Backlog 재확인 | Comparable 기반 유지, DCF/LBO/Option/PMI 전부 Enterprise Backlog로 문서 재확인(코드 변경 없음) |
| 4 | Executive Dashboard | ✅ 가독성 개선 | Widget 추가 없음. Row 라벨 한글화 + 최신 10건 제한(중복 누적 문제 발견 및 수정) |
| 5 | Email Preview | ✅ (2번에 포함) | Round 4의 `EmailNotifier` 재사용, dry-run 유지 |

## 테스트 결과

```text
$ pytest tests/ -q                                    -> 전부 PASS (397개 테스트, Round 8: 387개 → +10개)
$ python scripts/validate_config.py                   -> PASS
$ python scripts/secret_scan.py                        -> PASS
$ python scripts/bootstrap_project.py --dry-run         -> PASS (Registry 8개 전체 검증 통과)
$ python scripts/scenarios/scenario_1_news_analysis.py  -> PASS (Email Preview 단계 포함, 7단계)
$ python scripts/scenarios/scenario_3_investment_review.py "LX Hausys" -> PASS (실제 Knowledge 반영된 Export 생성 확인)
$ python scripts/scenarios/scenario_3_investment_review.py "Caesarstone" -> PASS (Knowledge 미보유 회사는 정직하게 mock 유지 확인)
```

## Round 9에서 새로 생성/수정된 파일

**신규 파일**: `tests/test_dashboard_feed.py`(5개 테스트, `_most_recent()`/한글 라벨 검증).

**중대 수정**
- `scripts/providers/mock_provider.py`: `_real_knowledge_fields()`/`_is_usable_section()`
  신설. `company_id`가 등록되어 있고 그 회사의 1순위 Knowledge 문서에 신뢰 가능한 §1/2/3/7
  Section이 있으면 `quick_company_scan()`이 그 실제 내용을 반환한다(Claude 호출은 여전히
  하지 않음, confidence는 계속 "low"). `search_by_company()`가 이어붙이는 여러 파일 중
  1순위 문서만 따로 파싱해, 다른 회사/문서의 같은 Section 번호가 잘못 노출되는 버그를
  피했다.
- `scripts/quick_company_scan.py`: `_render_quick_scan_markdown()` 신설, `_bullets()`
  헬퍼 추가. Export Markdown이 Company Overview 한 줄만 보여주던 것을 Core 7 필드 전부 +
  Investment Review 세부(추천 사유/Peer 비교표)로 확장했다.
- `scripts/scenarios/scenario_1_news_analysis.py`: `notifiers.EmailNotifier`+
  `build_alert_message()`(Round 4)를 재사용해 [7/7] Email Preview 단계 추가. `run()`
  반환값에 `email_preview`(`NotifierResult`, dry-run) 추가.
- `scripts/investment_review.py`, `knowledge/INVESTMENT_FRAMEWORK.md`: DCF에 이어
  LBO/Option/PMI도 Enterprise Backlog로 명시(문서만 수정, 애초에 구현된 적 없음).
- `scripts/pipeline/dashboard_feed.py`: 6개 Widget이 쓰는 row dict의 key를 한글
  라벨(날짜/핵심 내용/신뢰도/출처/회사명/스캔일/종합 점수/추천 신호/검토일/Source/가동
  상태/안정성 참고)로 변경. `_most_recent()` 신설 — Today's Intelligence/Critical
  Risk/Future Opportunity/Quick Company Scan/Investment Review를 최신 10건으로 제한
  (Source Health는 로그가 아니라 목록이라 제한하지 않음). Storage 자체는 전체를 그대로
  보존한다.
- `dashboard/sample_data.json`: 위 한글 라벨 변경에 맞춰 갱신.
- `tests/test_dashboard_data_provider.py`, `tests/test_mvp_integration.py`,
  `tests/test_quality_gate.py`: 한글 라벨 변경에 맞춰 단언문 갱신.

## 알려진 설계 결정 이력 (전체, 상세는 docs/04_DATA_AND_CONFIG_SCHEMA.md §1/§5, 각 ADR)

- ADR-006/007/008/009/010: 문서 우선순위 / n8n 통합 / Workflow ID 정책 / Workflow
  생명주기 / Release Policy(RC1 정의)
- Round 2~9의 각 Q 항목·추가 지시: `CHANGELOG.md`에 라운드별 상세 기록

## 남은 사용자 작업 / 알려진 한계

`TODO.md` 참고 — Round 9도 여전히 Mock/dry-run 기반이다. 사용자 검증 결과 확인된 핵심
한계:
- **Company Registry 30개사 중 1개사(LX_HAUSYS)만 실제 Knowledge 보유** — 나머지는
  Quick Company Scan을 돌려도 여전히 "mock: ... 미확인"만 나온다. TOP-0001 핵심 비교군
  (Caesarstone/Cosentino/Wilsonart)조차 예외가 아니다(`config/technical_debt_registry.yaml`
  TD-005).
- **Investment Review의 Comparable Peer가 회사와 무관하게 항상 동일한 예시 데이터**
  (Peer A/B) — 실제 재무 Provider 연결(RC2) 전까지 숫자 자체는 참고용도 되지 않는다.
- **뉴스 분석(risk_analysis)은 실제 Claude 추론이 아니라 고정 mock 문구** — "사람이
  다시 읽지 않아도 될 정도"는 RC2(실제 API 연결) 이후에나 가능하다.
- `docs/CONNECTION_READINESS.md`의 Credential 체크리스트대로 Claude API Key/모델 ID
  3종/Google/n8n/Gmail/Telegram 계정을 준비하고 `config/feature_flags.yaml`을 켜야
  "실제 동작"(RC2)으로 전환된다.
