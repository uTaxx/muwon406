# Project Status

최종 갱신: 2026-08-07 (Architect Review Round 10 반영)

## 요약

TASK-001~007 → Round 2~9(Knowledge/Provider/Registry/Coverage/Scenario화/RC1 정의/
Quick Company Scan·News Intelligence·Investment Review·Dashboard 완성도 개선) →
**Round 10("Data Sprint") 반영** 완료. Architect는 "이번 Round를 기점으로 개발
Sprint를 종료한다. 다음 Sprint는 Data Sprint다"라고 선언하며 **새로운 기능/구조/
Registry/Framework/추상화/Enterprise 기능을 절대 금지**하고, 대신 "Pilot에서 실제
사용할 데이터를 채운다"를 유일한 목표로 지정했다.

이번 Round는 코드 구조를 전혀 바꾸지 않고 **데이터만** 채웠다: Company Registry
TOP10(LX Hausys 외 9개사)에 실제 WebSearch 리서치 기반 Knowledge 문서를 신설하고,
Investment Review의 Comparable Peer를 회사마다 다른 실제 기업으로 교체했다(기존
"Peer A/B" 예시 삭제). 그 결과 Company Coverage가 3.3%→33.3%, Industry Coverage가
3.6%→35.7%로 실측 개선되었다 — 코드를 한 줄도 늘리지 않고 Quick Company Scan/
Investment Review의 실사용 품질이 가장 크게 좋아진 라운드다.

## Round 10 Priority 5개 처리 결과

| 순위 | 항목 | 상태 | 핵심 내용 |
|---|---|---|---|
| 1 | Knowledge Population | ✅ 완료 | TOP10 기업(LX Hausys 외 9개사) 실제 리서치 Knowledge 문서 9건 신설, `COMPANY_KNOWLEDGE_FILES` 매핑·`company_registry.yaml` products/value_chain 갱신 |
| 2 | Investment Review Peer 실제화 | ✅ 완료 | `financial_provider.py` 전면 재작성 — "Peer A/B" 삭제, 회사별 실제 Comparable(예: LX Hausys→KCC/한샘/LIXIL/YKK AP/Saint-Gobain) 등록. 배수는 확인된 값만, 미확인은 정직하게 `None` |
| 3 | Quick Company Scan Demo 5개사 | ✅ 검증 완료 | LX Hausys/KCC/Hanssem/Caesarstone/Cosentino 실제 품질 확인(Company Intelligence Score 42~45점, 이전 대비 상승). 나머지 20개사는 Mock 유지 확인(WILSONART로 회귀 테스트) |
| 4 | Scenario 5개 발표 순서 | ✅ 검증 완료 | 발표 순서(1=LX Hausys, 2=KCC, 3=Caesarstone Quick Company Scan/Investment Review, 4=정책, 5=뉴스) 전부 실행 검증. 기존 5개 Scenario 스크립트 구조는 변경 없음(새 구조 금지) |
| 5 | Dashboard 단순화 | ✅ 완료 | 죽은 CSS 5개 클래스 삭제(Technical Debt TD-001 해소), 6개 Widget 구조는 그대로 유지 |

## 테스트 결과

```text
$ pytest tests/ -q                                    -> 전부 PASS (402개 테스트, Round 9: 397개 → +5개)
$ python scripts/validate_config.py                   -> PASS
$ python scripts/secret_scan.py                        -> PASS
$ python scripts/bootstrap_project.py --dry-run         -> PASS (Registry 8개 전체 검증 통과)
$ python scripts/knowledge_coverage.py                  -> Company Coverage 33.3%(3.3%→), Industry Coverage 35.7%(3.6%→)
$ python scripts/scenarios/scenario_3_investment_review.py "LX Hausys"    -> PASS (Peer: KCC/한샘/LIXIL/YKK AP/Saint-Gobain, Score 42.3)
$ python scripts/scenarios/scenario_3_investment_review.py "KCC"         -> PASS (Score 45.0)
$ python scripts/scenarios/scenario_3_investment_review.py "Caesarstone" -> PASS (Score 43.1)
$ python scripts/scenarios/scenario_4_policy_impact.py                   -> PASS (예시 시나리오임을 명시)
$ python scripts/scenarios/scenario_1_news_analysis.py                   -> PASS
```

## Round 10에서 새로 생성/수정된 파일

**신규 Knowledge 문서(9건, `knowledge/`)**: `KCC_COMPANY_PROFILE.md`,
`HANSSEM_COMPANY_PROFILE.md`, `CAESARSTONE_COMPANY_PROFILE.md`,
`COSENTINO_COMPANY_PROFILE.md`, `SHAW_INDUSTRIES_COMPANY_PROFILE.md`,
`LIXIL_COMPANY_PROFILE.md`, `YKK_AP_COMPANY_PROFILE.md`, `SCHUCO_COMPANY_PROFILE.md`,
`SAINT_GOBAIN_COMPANY_PROFILE.md` — 전부 WebSearch로 확인한 실제 사실 + 원문 URL,
16계층 Taxonomy 준수, §10 Risk 항목에 TOP-0001(실리코시스) 소송 노출 여부를 "확인됨"/
"확인 안 됨(무혐의 확정 아님)"으로 정직하게 구분 기록.

**중대 수정**
- `scripts/pipeline/knowledge_retrieve.py`: `COMPANY_KNOWLEDGE_FILES`에 9개사 매핑
  추가(각 회사는 자기 프로필 문서 1개만 참조 — LX 그룹 맥락과 섞이지 않도록).
- `config/company_registry.yaml`: 9개사의 `products`/`value_chain`/일부
  `official_website` 필드를 TODO에서 실제 리서치 값으로 갱신(검증 못한 필드는 계속
  TODO/null 유지).
- `scripts/financial_provider.py`: `MockFinancialDataProvider`가 항상 반환하던
  고정 "Peer A/B (예시)"를 삭제하고, 회사별 실제 Comparable Peer 그룹(`_PEER_COMPANY_IDS`)
  + 실제 확인된 배수(`_KNOWN_MULTIPLES`, 미확인은 `None`)로 교체. 자기 자신은 자신의
  Peer 목록에서 제외.
- `scripts/quick_company_scan.py`: Export의 Comparable Peer 표에서 `None` 배수를
  "-"로 표시하도록 수정(가독성), "전부 예시 데이터" 문구를 "회사명은 실제 기업"으로
  정정.
- `dashboard/styles.css`: Technical Debt TD-001(죽은 CSS 5개 클래스,
  `.lcip-trend-chart`/`.lcip-stat-*`) 삭제 — Round 8 Widget 재구성 이후 미사용 상태였다.
- `config/technical_debt_registry.yaml`: TD-001 상태를 `resolved`로 갱신.
- 테스트: `test_financial_provider.py` 전면 재작성(9개), `test_knowledge_coverage.py`/
  `test_company_intelligence_score.py`/`test_quick_company_scan.py`의 "Knowledge
  없는 회사" 회귀 테스트 기준을 CAESARSTONE(이제 Knowledge 보유)에서 WILSONART(여전히
  미보유)로 교체.

## 알려진 설계 결정 이력 (전체, 상세는 docs/04_DATA_AND_CONFIG_SCHEMA.md §1/§5, 각 ADR)

- ADR-006/007/008/009/010: 문서 우선순위 / n8n 통합 / Workflow ID 정책 / Workflow
  생명주기 / Release Policy(RC1 정의)
- Round 2~10의 각 Q 항목·추가 지시: `CHANGELOG.md`에 라운드별 상세 기록

## 남은 사용자 작업 / 알려진 한계

`TODO.md` 참고 — Round 10도 여전히 Mock/dry-run 기반이며 코드 구조는 동결 상태다
(Architect 지시: "새로운 기능/구조는 구현하지 않는다"). 사용자 검증 결과 확인된 핵심
한계:
- **Company Registry 30개사 중 10개사만 실제 Knowledge 보유** — TOP10 완성 이후에도
  나머지 20개사(LG전자·LG화학, AGC·NSG·Guardian·Vitro, Rehau·Deceuninck·Andersen·
  Pella·Marvin, PPG·Corning·Owens Corning, Wilsonart 등)는 여전히 Mock이다. 다음
  Data Sprint의 후보군이다.
- **Investment Review 배수(EV/EBITDA·PER·PBR)가 부분적으로만 채워짐** — 비상장
  기업(Cosentino/YKK AP/Schüco/Shaw)은 공개 배수 자체가 없어 구조적으로 `None`이
  유지된다. 상장사도 일부 배수는 이번 세션 네트워크 제한으로 재무데이터 사이트 직접
  대조를 못해 검색 스니펫 기반 저신뢰 값으로 남아 있다(각 Knowledge 문서에 명시).
- **뉴스 분석(risk_analysis)/정책 분석은 여전히 고정 mock 문구** — "사람이 다시 읽지
  않아도 될 정도"는 RC2(실제 Claude 연동) 이후에나 가능하며, Round 10도 실제 API
  호출을 금지했다.
- `docs/CONNECTION_READINESS.md`의 Credential 체크리스트대로 Claude API Key/모델 ID
  3종/Google/n8n/Gmail/Telegram 계정을 준비하고 `config/feature_flags.yaml`을 켜야
  "실제 동작"(RC2)으로 전환된다.
