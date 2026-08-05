# 01. Project Context — Claude Code Handover 요약

> 원본: Google Drive `00_INITIAL_CLAUDE_CODE_HANDOVER.md`. 이 문서는 Claude Code(구현
> 담당 개발 에이전트)에게 프로젝트 역할과 절대 원칙을 전달하기 위한 최초 핸드오버 문서다.
> 절대 원칙은 `CLAUDE.md`에도 요약되어 있으며 그쪽이 실행 시 1차 참조 대상이다.

## 1. 역할

당신은 LCIP Pilot의 구현 담당 개발 에이전트다. 본 프로젝트는 LX홀딩스 전략팀 관점의 공개정보 기반 Corporate Intelligence Pilot이다. 일반 뉴스봇으로 축소 해석하지 말고, 모든 기능은 미래준비·리스크 관리와 LX 관련성 판단에 연결해야 한다.

## 2. 절대 원칙

1. 외부 공개정보만 사용한다.
2. 내부 보고서·비공개 정보·미공개 거래정보를 요구하거나 추정하지 않는다.
3. 모든 핵심 사실에 원문 URL을 저장한다.
4. 사실·AI 해석·추론·제안을 구분한다.
5. 모든 분석은 LX홀딩스와 관련 계열사 관점에서 수행한다.
6. AI가 필요 없는 작업에는 Claude API를 사용하지 않는다.
7. 월 Claude API 목표 15달러, 절대 상한 20달러를 준수한다.
8. 비밀키를 코드·문서·Git에 저장하지 않는다.
9. n8n 워크플로우는 모듈형 Sub-workflow로 작성한다.
10. 변경 사항은 CHANGELOG와 설계 문서에 반영한다.

## 3. 기술 스택

n8n Cloud Starter · Google Drive · Google Sheets · Anthropic API · Gmail · Telegram Bot API · Claude Code · Git · HTML/CSS/Vanilla JavaScript · n8n Code Node JavaScript

별도 DB·서버·React 앱은 Pilot 범위에서 기본적으로 사용하지 않는다.

## 4. 개발 우선순위 (Sprint 참고 — 실제 실행 단위는 03_BUILD_SPECIFICATION.md의 TASK-001~018)

- **Sprint 1 — 기반**: Drive 폴더 생성, Master Sheet Schema, CONFIG_MASTER·TOPIC_CONFIG·SOURCE_REGISTRY, WF-P01, Cost Guard 기본 함수
- **Sprint 2 — 수집**: Google News RSS, URL 정규화, 중복 제거, ARTICLE_DB, Source Health
- **Sprint 3 — AI 분석**: Relevance Classifier, Risk Analysis, JSON Schema 검증, COST_LOG
- **Sprint 4 — 산출물**: HTML Dashboard, Gmail Card, Telegram, SENT_HISTORY
- **Sprint 5 — 관리자**: CHANGE_REQUEST Sheet, 자연어 변경 Parsing, Diff·Impact 생성, 승인 후 Config Version 생성
- **Sprint 6 — 확장**: DART, 정부 보도자료, Quick Scan Prototype

## 5. 코딩 규칙

- 함수는 작고 명확하게 유지한다.
- 날짜는 ISO 8601로 저장한다.
- 금액은 원통화 값과 통화코드를 함께 저장한다.
- URL은 canonical URL과 original URL을 모두 보존한다.
- 모든 외부 요청에는 timeout과 retry를 둔다.
- 오류를 삼키지 말고 ERROR_LOG에 기록한다.
- n8n Code Node에서 대량 데이터는 batch 처리한다.
- Sheet Write는 가능하면 append/batch update를 사용한다.
- HTML은 외부 웹폰트 의존을 최소화한다.

## 6. Claude API 규칙

- 전체 Knowledge Base를 매번 보내지 않는다. 관련 문단만 로드한다.
- 입력 최대 8,000 tokens, 출력 최대 1,200 tokens를 기본값으로 한다.
- 모델명은 하드코딩하지 않는다.
- 응답은 JSON Schema로 검증한다.
- 파싱 실패 시 동일 요청을 무한 재시도하지 않는다. 1회 교정 재호출 후 실패하면 검토 대기로 보낸다.
- Usage를 반드시 COST_LOG에 기록한다.

## 7. Pilot 기본 Topic (config/topics.yaml에 반영됨)

```yaml
topic_id: TOP-0001
topic_name: engineered_stone_silicosis
mission: risk_management
related_company: LX_HAUSYS
countries: [US, AU, CA, GB, EU]
languages: [en, ko]
include_keywords:
  - silicosis
  - engineered stone
  - artificial stone
  - quartz countertop
  - respirable crystalline silica
  - silica lawsuit
  - 규폐증
  - 엔지니어드스톤
  - 인조대리석
exclude_keywords:
  - sports
  - unrelated natural stone
collection_schedule: hourly
deep_analysis_rule: new_material_change_only
alert_rule: material_change_only
```

키워드는 운영 중 관리자가 (자연어 관리자 기능을 통해, 승인 후) 수정할 수 있어야 한다.

## 8. 하지 말아야 할 것

- 과도한 프레임워크 도입
- 별도 DB를 먼저 구축
- 모든 소스를 한 번에 연결
- 기사 전부를 Claude에 전달
- Prompt를 n8n 노드 안에만 숨겨두기
- API Key 하드코딩
- 회사 내부정보를 요구
- 근거 없는 LX 영향 단정
- Pilot에서 Enterprise 기능까지 무리하게 구현
