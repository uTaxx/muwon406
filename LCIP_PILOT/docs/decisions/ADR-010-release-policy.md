# ADR-010 — Release Policy (RC1 / RC2 정의)

- **상태**: Accepted
- **날짜**: 2026-08-07
- **결정 주체**: Architect Review Round 8 (ChatGPT 검토, 사용자 승인)

## 맥락

Round 5~7에 걸쳐 "Pilot Release Candidate(RC1)"라는 목표가 반복 언급됐지만, "무엇이
갖춰지면 RC1인가"는 명시적으로 정의된 적이 없었다 — Round 7 보고서 §55는 이 질문을
그대로 Architect에게 넘겼다. Round 8은 이 질문에 답하고, 동시에 "이번 Round부터는
새로운 Framework를 더 이상 만들지 않는다"는 제약을 건다.

## 결정

### RC1의 정의

> **RC1 = 실제 외부 API를 하나도 호출하지 않아도 LX 전략팀에게 데모 가능한 수준.**

RC1이 되기 위한 5가지 필수 요소:

1. **Mock 기반** — `MockProvider`가 모든 AI 호출을 결정론적으로 대체한다.
2. **Feature Flag** — `config/feature_flags.yaml`의 4개 스위치로 실제 호출 경로를
   안전하게 차단한다(이미 Round 6에서 완성).
3. **실제 Pipeline** — Collect→Normalize→Rule Filter→Classify→Knowledge Retrieve→
   Analyze→Validate→Generate Intelligence→Store의 각 단계가 Mock이 아니라 실제 로직
   으로 동작한다(입출력 변환·검증·저장은 진짜로 일어난다 — "가짜"인 것은 AI 응답
   내용뿐이다).
4. **실제 Registry** — Company/Source/Model/Prompt/Workflow/Config/Storage Registry가
   실제 데이터를 담고 있고, `RegistryManager`가 구조적으로 검증 가능하다.
5. **실제 Dashboard** — 정적 HTML을 단순히 보여주는 Viewer가 아니라, Widget이 실제
   Pipeline 산출물(ARTICLE_DB/INTELLIGENCE_DB, Quick Company Scan 결과 등)을 반영하는
   Executive Dashboard여야 한다(Round 8 §4).

### RC2와의 경계선

**실제 API 연결(Anthropic/Google/Naver/DART/Gmail/Telegram/n8n)은 전부 RC2 범위다.**
RC1 완성 시점에도 `config/feature_flags.yaml`의 4개 스위치는 계속 `false`로 유지한다.
`docs/CONNECTION_READINESS.md`가 이미 RC2 착수를 위한 준비(Credential 체크리스트/
Connection Test Plan/Rollback Plan)를 다루고 있다 — RC1은 그 준비를 실행하지 않는다.

### 새 Framework 금지 원칙과의 관계

RC1을 향한 남은 작업(Quick Company Scan 완성, Executive Dashboard, Registry 검증 등)은
**기존 아키텍처 패턴(Provider Layer/Adapter Layer/Pipeline/Widget/Registry) 안에서
기능을 채우는 것**이지 새 계층을 추가하는 것이 아니다. 예를 들어 Quick Company Scan에
추가되는 "Financial Provider"는 새 Framework가 아니라 기존 Provider Layer 패턴
(추상 클래스 + Mock 구현체)을 한 번 더 적용한 것이다 — `OpenAIProvider`/`GeminiProvider`
확장 지점을 만들 때와 동일한 방식이다.

## 이유

- "RC1"이라는 단어가 라운드마다 다르게 해석될 위험이 있었다(구조 완성만으로 충분한지,
  실제 연결까지 필요한지). 명시적 정의가 없으면 "RC1 도달"을 주장할 근거도, 반박할
  근거도 없다.
- Mock 기반으로도 데모가 가능하다는 것은 이미 Round 4~7에서 실증됐다(Scenario 5종,
  Quality Gate, `demo_pilot.py`의 전신들) — RC1을 이 지점에 고정하는 것은 이미 달성한
  것을 공식화하는 것에 가깝고, 남은 작업(Quick Company Scan/Dashboard/Registry
  검증)에 집중하도록 범위를 좁혀준다.
- 실제 API 연결을 RC1에서 분리하면, 비용·Rate Limit·Credential 발급처럼 Claude Code가
  단독으로 통제할 수 없는 외부 요인이 RC1 일정에 영향을 주지 않는다.

## 트레이드오프

- RC1을 "실제로 작동하는 최종 제품"으로 기대하는 이해관계자에게는 "Mock 기반"이라는
  말이 실망스럽게 들릴 수 있다 → 데모 시점에 "이 결과는 Mock 응답"이라는 점을 항상
  명시한다(이미 각 Scenario 출력에 이 표시가 있다).
- RC1과 RC2 사이에 실제 연결 테스트라는 큰 단계가 남아 있어, RC1 도달이 "거의 다
  끝났다"는 착각을 줄 수 있다 → Round 8 보고서 §63(RC1 예상 완료일)에서 RC2까지
  포함한 전체 일정을 분리해서 제시한다.

## 원복 가능성

가능. 이 ADR은 "RC1"이라는 이름에 대한 정의일 뿐 코드 구조를 바꾸지 않는다 — 되돌려도
기존 Feature Flag/Mock/Registry/Pipeline/Dashboard 구현에는 영향이 없다.
