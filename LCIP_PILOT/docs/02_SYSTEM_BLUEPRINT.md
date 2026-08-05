# LCIP Pilot System Blueprint v1.0

> 원본: Google Drive `01_LCIP_Pilot_System_Blueprint.md` (원문 그대로 보존). 이 저장소에서는
> `03_BUILD_SPECIFICATION.md`가 실행 명세서로서 우선하며, 본 문서와 구조가 다른 부분(Google
> Drive 폴더 구조 등)은 `04_DATA_AND_CONFIG_SCHEMA.md`의 "설계문서 충돌 로그"를 참고할 것.

## 0. 문서 목적

본 문서는 개인 프로젝트 단계의 **LCIP Pilot** 구축 기준을 정의한다. Pilot은 회사 정식 시스템이 아니라, 공개정보 기반 전략 인텔리전스가 실제 업무에 유용한지 검증하는 최소 기능 제품이다.

- 운영비 목표: 기존 구독 포함 월 10만원 이하
- 핵심 플랫폼: Google Drive·Google Sheets·n8n Cloud·Claude API
- 개발 방식: Claude Code 중심, 필요 시 ChatGPT 설계·검토 지원
- 보안 원칙: 외부 공개정보만 사용
- 성공 기준: LX홀딩스 전략팀 업무에 실질적 활용 가능성을 증명

---

## 1. 플랫폼 정의

LCIP Pilot은 전 세계 공개정보를 수집하고, LX홀딩스 및 주요 계열사의 사업 구조를 이해한 상태에서 다음 두 가지 미션을 지원하는 AI 기반 Corporate Intelligence Pilot이다.

### 1.1 미래준비

- 산업·기술·정책 변화 탐지
- M&A·Carve-out·Bolt-on·PE/VC 딜 신호 탐지
- 기업 Quick Scan
- 투자 검토를 위한 기초자료 제공
- 향후 성장기회와 추가 조사 과제 제안

### 1.2 리스크 관리

- 소송·제품책임·산업안전·환경·통상 리스크 조기 감지
- 환율·원자재·정책 변화 영향 분석
- 계열사·사업·제품·Value Chain별 영향 연결
- 변동사항 발생 시 알림 및 대시보드 갱신

---

## 2. Pilot 범위

### 2.1 포함 범위

1. 실리코시스·엔지니어드스톤 리스크 모니터링
2. 국내외 Google News RSS 수집
3. Naver News API 또는 국내 뉴스 검색 연계
4. DART 공시·사업보고서 일부 연계
5. 정부기관 보도자료 일부 수집
6. LX홀딩스 및 LX하우시스 공개정보 Knowledge Base
7. Claude API 기반 관련성 분류·핵심 분석
8. HTML 대시보드
9. Gmail·Telegram 알림
10. Source Health·비용 모니터링
11. Configuration Registry
12. 기본형 자연어 관리자 변경 기능

### 2.2 제외 범위

- 전 계열사 완전 적용
- 사내 비공개정보 연계
- 별도 PostgreSQL 운영 DB
- 전용 관리자 웹 포털
- 다중 사용자 권한·SSO
- 완전 자동 투자위원회 시스템
- AI DD·PMI 고도화
- 전 국가 해외 공시 자동화
- 자연어만으로 n8n 워크플로우를 무제한 생성하는 기능

---

## 3. 최상위 설계 원칙

1. **LX 중심 사고**: 모든 분석은 LX홀딩스와 계열사 사업 관점에서 수행한다.
2. **공개정보 전용**: 내부 보고서·비공개 실적·사내 메신저·미공개 투자정보는 사용하지 않는다.
3. **Evidence First**: 모든 수치·사실·판단에는 원문 링크를 연결한다.
4. **사실·추론·제안 분리**: AI 출력에서 확인된 사실, 해석, 추론, 제안을 구분한다.
5. **비용 통제**: AI가 필요 없는 작업은 n8n Code·Google Sheets로 처리한다.
6. **모듈화**: 수집·정규화·분류·분석·저장·발송을 분리한다.
7. **변동 중심 운영**: 새로운 중요 변화가 있을 때만 고비용 분석과 알림을 수행한다.
8. **자연어 관리**: 관리자는 자연어로 설정 변경을 요청하고, AI가 변경 초안·영향·승인 단계를 제공한다.

---

## 4. 전체 아키텍처

```text
[External Public Sources]
Google News RSS · Naver News · DART · 정부 보도자료 · 기업 공식자료
 ↓
[n8n Collection & Orchestration]
수집 · 날짜필터 · 중복제거 · URL검증 · 스케줄 · 재시도
 ↓
[Google Sheets Registry & DB]
SOURCE_REGISTRY · TOPIC_CONFIG · ARTICLE_DB · RISK_DB · COST_LOG · HEALTH_LOG
 ↓
[Google Drive Knowledge Base]
LX Context · LX하우시스 Business Profile · Risk Map · Prompt · HTML Template
 ↓
[Claude API]
관련성 분류 · 핵심 사실 추출 · LX 영향 · 대응/추가조사 · 한국어 요약
 ↓
[Output]
HTML Dashboard · Gmail Card · Telegram · Google Drive Archive
 ↓
[Admin Control]
Configuration Registry · 자연어 변경 요청 · 영향검토 · 승인 · 배포
```

---

## 5. Google Drive 구조 (참고안 — 실행은 03_BUILD_SPECIFICATION.md TASK-005 기준)

```text
LCIP_PILOT/
├─ 00_GOVERNANCE/
│ ├─ PLATFORM_CONSTITUTION.md
│ ├─ SECURITY_POLICY.md
│ ├─ SOURCE_RELIABILITY.md
│ └─ CHANGE_LOG.md
├─ 01_KNOWLEDGE_BASE/
│ ├─ LX_HOLDINGS_CONTEXT.md
│ ├─ LX_HAUSYS_COMPANY_DNA.md
│ ├─ LX_HAUSYS_VALUE_CHAIN.md
│ ├─ GROUP_RISK_MAP.md
│ ├─ GROUP_OPPORTUNITY_MAP.md
│ └─ STRATEGY_PLAYBOOK.md
├─ 02_SOURCE_LIBRARY/
│ ├─ DART/
│ ├─ SUSTAINABILITY/
│ ├─ IR/
│ ├─ GOVERNMENT/
│ └─ OFFICIAL_WEBSITE/
├─ 03_PROMPTS/
│ ├─ CLASSIFIER.md
│ ├─ RISK_ANALYSIS.md
│ ├─ POLICY_ANALYSIS.md
│ ├─ QUICK_SCAN.md
│ └─ REPORT_WRITER.md
├─ 04_TEMPLATES/
│ ├─ DASHBOARD.html
│ ├─ EMAIL_CARD.html
│ └─ TELEGRAM_TEMPLATE.md
├─ 05_OUTPUT/
│ ├─ CURRENT/
│ └─ ARCHIVE/
├─ 06_LOGS/
└─ 07_HANDOVER/
```

---

## 6. Google Sheets 구조

### 6.1 CONFIG_MASTER

- variable_id
- category
- variable_name
- display_name
- current_value
- data_type
- scope
- allowed_values
- min_value
- max_value
- affected_workflows
- status
- version
- updated_by
- updated_at

### 6.2 TOPIC_CONFIG

- topic_id
- topic_name
- mission
- related_company
- countries
- languages
- include_keywords
- exclude_keywords
- source_list
- collection_schedule
- deep_analysis_rule
- alert_rule
- active

### 6.3 SOURCE_REGISTRY

- source_id
- source_name
- source_type
- endpoint_url
- access_method
- language
- country
- reliability_grade
- collection_schedule
- expected_freshness_hours
- active

### 6.4 ARTICLE_DB

- article_id
- topic_id
- title
- source
- source_url
- published_at
- collected_at
- language
- duplicate_key
- relevance_score
- analysis_status
- original_text_ref

### 6.5 INTELLIGENCE_DB

- intelligence_id
- article_id
- mission
- related_company
- related_business
- fact_summary
- significance
- lx_impact
- action
- confidence
- evidence_links
- created_at

### 6.6 SOURCE_HEALTH

- source_id
- last_checked_at
- last_success_at
- http_status
- response_ms
- record_count
- health_status
- consecutive_failures
- error_type
- recovery_action

### 6.7 COST_LOG

- execution_id
- workflow_id
- model
- input_tokens
- output_tokens
- estimated_cost_usd
- cumulative_monthly_cost
- created_at

---

## 7. Pilot 워크플로우

### WF-P01 Configuration Loader
승인된 설정값과 관련 Knowledge 파일 경로를 로드한다.

### WF-P02 News Collector
Google RSS·Naver 뉴스 수집, 날짜 필터, URL 정규화, 중복제거를 수행한다.

### WF-P03 Public Source Collector
DART·정부 보도자료·공식 홈페이지 데이터를 수집한다.

### WF-P04 Relevance Classifier
저비용 모델 또는 규칙 기반으로 LX 관련성·주제·계열사를 분류한다.

### WF-P05 Risk Analysis
중요 자료만 Claude에 전달하여 사실·중요성·LX 영향·대응을 분석한다.

### WF-P06 Dashboard Builder
누적 DB를 읽어 LX 디자인 가이드 기반 HTML 대시보드를 생성한다.

### WF-P07 Notification
신규 중요 이슈가 있을 때 Gmail·Telegram으로 카드형 요약을 발송한다.

### WF-P08 Source Health Monitor
링크·API·RSS·데이터 최신성·스키마 오류를 점검한다.

### WF-P09 Cost Guard
월 예산·일 호출량·토큰 사용량을 점검하고 제한한다.

### WF-P10 Natural Language Admin
관리자의 자연어 요청을 구조화된 변경안으로 변환하고 승인 후 CONFIG_MASTER에 반영한다.

### WF-P99 Error Handler
실패 로그, 자동 재시도, 관리자 알림, 수동 복구 대상을 관리한다.

---

## 8. Claude 사용 구조

### 8.1 AI 사용 전 처리

- 날짜 필터
- URL 중복
- 제목 유사도
- 출처 등급
- 키워드 일치
- 금액·날짜 정규화
- 링크 상태

위 작업은 AI를 사용하지 않는다.

### 8.2 AI 사용 대상

- 관련성 판단이 애매한 자료
- 중요 사건의 사실 구조화
- LX하우시스 영향 분석
- 정책·규제 단계 해석
- 대응 및 추가 조사 과제
- 한국어 보고 문장 작성

### 8.3 비용 기준

```text
MONTHLY_API_BUDGET_USD = 15
ABSOLUTE_MAX_BUDGET_USD = 20
DAILY_DEEP_ANALYSIS_LIMIT = 5
MAX_INPUT_TOKENS_PER_CALL = 8,000
MAX_OUTPUT_TOKENS_PER_CALL = 1,200
WARNING_AT_BUDGET_RATE = 0.70
RESTRICT_AT_BUDGET_RATE = 0.90
STOP_AT_BUDGET_RATE = 1.00
```

---

## 9. 자연어 관리자 구조

```text
관리자 요청
→ AI 의도 분석
→ 변경 대상 변수 식별
→ 변경 전/후 Diff
→ 예상 영향·비용·워크플로우 표시
→ 관리자 승인
→ CONFIG_MASTER 새 버전 생성
→ Sandbox Test
→ Production 적용
→ CHANGE_LOG 기록
```

예시:

- "실리코시스 검색에 캐나다를 추가해."
- "영문 기사 중 500만 달러 이상 판결은 즉시 알림으로 바꿔."
- "DART 수집은 평일 오전 7시 30분에 실행해."
- "Claude 월 예산이 12달러를 넘으면 심층분석을 긴급 건만 허용해."

AI는 직접 운영값을 변경하지 않고 반드시 변경안과 영향도를 제시한 뒤 승인을 받는다.

---

## 10. 디자인 기준

- LX홀딩스 홈페이지·지속가능경영보고서의 절제된 기업형 인상 반영
- 흰색 배경, 충분한 여백, 얇은 구분선, 카드 최소화
- 한글 중심, 영문 원문 링크 제공
- 웹: Pretendard → Noto Sans KR → Apple SD Gothic Neo → 맑은 고딕
- 이메일: Apple SD Gothic Neo → 맑은 고딕 → Arial
- PPT·Word: LG스마트 Regular 사용 가능 시 우선, 외부 공유 시 Pretendard/Noto Sans KR
- 과도한 색상·그림자·이모지 금지
- 표의 단어 중간 줄바꿈 방지

---

## 11. Pilot 성공 기준

1. 중요 신규 실리코시스 이슈의 누락이 허용 범위 내일 것
2. 불필요한 알림이 지속적으로 감소할 것
3. 모든 주요 사실에 원문 링크가 있을 것
4. 월 총 운영비가 10만원 이하일 것
5. Claude API 월 사용액이 15달러 목표, 20달러 절대 상한 내일 것
6. 대시보드·메일·Telegram이 안정적으로 동작할 것
7. LX홀딩스 전략팀 관점의 시사점이 업무에 실제로 활용될 것
8. 향후 DART·정부·투자검토로 확장 가능한 구조일 것

---

## 12. Enterprise 전환 조건

- Pilot 2~3개월 운영
- 실사용자 피드백 확보
- 반복 업무시간 절감 수치 확인
- 임원·팀 보고 활용 사례 확보
- 월 비용 대비 효용 확인
- 보안·권한·감사 요구사항 정의

Enterprise 단계에서는 전 계열사 Knowledge Base, 투자검토 엔진, 해외공시, 별도 DB, 관리자 포털, 권한·감사로그, 정식 운영지원 체계를 추가한다.
