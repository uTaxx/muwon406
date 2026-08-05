# LCIP Pilot Build Specification v1.0

> **문서 목적**
> 본 문서는 Claude Code가 `LCIP Pilot`의 로컬 프로젝트 구조, Google Drive·Google Sheets 생성 도구, n8n 워크플로우 JSON, Claude API 모듈, HTML 대시보드, Gmail·Telegram 발송, Source Health 및 Cost Guard를 최대한 자동으로 구현하도록 지시하는 실행 명세서다.

---

## 0. 프로젝트 목표

LCIP Pilot은 전 세계 **외부 공개정보**를 수집·정리·분석하여 LX홀딩스 전략팀 관점의 다음 두 가지 미션을 지원하는 개인용 Corporate Intelligence Pilot이다.

1. **미래준비**
   - 산업·정책·기술·자본시장 변화 탐지
   - M&A, Carve-out, Bolt-on, Venture 기회 탐색
   - 기업 Quick Scan 및 투자검토 기초자료 생성

2. **리스크 관리**
   - 소송, 제품책임, 산업안전, 환경, 통상, 환율, 원자재, 공급망 리스크 조기 감지
   - 계열사·사업·제품·Value Chain 영향경로 분석
   - 중요 변동 발생 시 대시보드와 알림 갱신

Pilot의 첫 번째 완성 주제는 **엔지니어드스톤·실리코시스 리스크 모니터링**이다.

---

## 1. Pilot 제약조건

### 1.1 기술 스택

- Local Development: Claude Code
- Primary Storage: Google Drive
- Pilot Registry / DB: Google Sheets
- Workflow Orchestrator: n8n Cloud Starter
- AI Analysis: Claude API
- Dashboard: Static HTML/CSS/Vanilla JavaScript
- Notification: Gmail + Telegram
- Optional Version Control: Git / private GitHub repository

### 1.2 비용 제약

- 기존 구독 포함 개인 월 총비용: **10만원 이하**
- Claude API 월 목표: **USD 15**
- Claude API 절대 상한: **USD 20**
- n8n Starter 실행량을 고려해 워크플로우 실행 횟수 최소화
- AI가 필요 없는 작업은 Code Node, Python, Google Sheets 수식으로 처리

### 1.3 보안 제약

- 회사 내부정보, 사내 문서, 미공개 실적, 미공개 투자안, 내부 이메일·회의록은 사용 금지
- 공개정보만 사용
- API Key, OAuth Secret, Telegram Token, Chat ID는 `.env` 또는 n8n Credential에만 저장
- Secret은 코드, Markdown, JSON, Google Sheets, Git에 평문 저장 금지
- 실제 외부 쓰기·발송·배포는 사용자 승인 전까지 금지

### 1.4 Pilot 제외범위

- 전용 웹 관리자 포털
- PostgreSQL·별도 서버 운영
- 다중 사용자 권한·SSO
- 전체 LX 계열사 완전 자동화
- 투자위원회 전체 프로세스
- AI DD·PMI 고도화
- 모든 국가의 해외 공시 자동화
- 무제한 자연어 Workflow 생성

---

## 2. Claude Code 실행 원칙

Claude Code는 아래 절차를 준수한다.

1. 프로젝트 루트의 `CLAUDE.md` 및 연결 문서를 모두 읽는다.
2. 수정 전 현재 폴더 구조와 기존 파일을 검사한다.
3. 기존 파일이 있으면 덮어쓰지 말고 diff와 migration 계획을 제시한다.
4. 각 Task는 순서대로 실행한다.
5. 외부 계정에 영향을 주는 작업은 기본적으로 `dry-run`으로 구현한다.
6. 실제 Google Drive·Sheets 생성, n8n 배포, 이메일·Telegram 발송 전 사용자 승인을 요청한다.
7. Task 완료 후 Acceptance Test를 수행한다.
8. 실패 시 다음 Task로 넘어가지 않는다.
9. 각 완료 시 `PROJECT_STATUS.md`, `TODO.md`, `CHANGELOG.md`를 갱신한다.
10. 완료 주장은 생성 파일·테스트 결과·남은 사용자 작업을 제시한 뒤에만 가능하다.

---

## 3. 최종 프로젝트 구조

Claude Code는 아래 프로젝트 구조를 생성한다.

```text
LCIP_PILOT/
├─ CLAUDE.md
├─ README.md
├─ PROJECT_STATUS.md
├─ TODO.md
├─ CHANGELOG.md
├─ .env.example
├─ .gitignore
│
├─ docs/
│ ├─ 01_PROJECT_CONTEXT.md
│ ├─ 02_SYSTEM_BLUEPRINT.md
│ ├─ 03_BUILD_SPECIFICATION.md
│ ├─ 04_DATA_AND_CONFIG_SCHEMA.md
│ ├─ 05_ACCEPTANCE_TESTS.md
│ ├─ GOOGLE_DRIVE_SETUP.md
│ ├─ GOOGLE_SHEETS_SETUP.md
│ ├─ N8N_API_SETUP.md
│ ├─ ANTHROPIC_SETUP.md
│ ├─ TELEGRAM_SETUP.md
│ ├─ GMAIL_SETUP.md
│ ├─ DEPLOYMENT_GUIDE.md
│ ├─ OPERATIONS_GUIDE.md
│ └─ decisions/
│   ├─ ADR-001-google-drive.md
│   ├─ ADR-002-google-sheets.md
│   ├─ ADR-003-n8n-starter.md
│   ├─ ADR-004-no-postgresql-in-pilot.md
│   └─ ADR-005-ai-cost-control.md
│
├─ config/
│ ├─ project.yaml
│ ├─ topics.yaml
│ ├─ sources.yaml
│ ├─ cost_policy.yaml
│ ├─ notification.yaml
│ ├─ drive_structure.yaml
│ ├─ sheet_structure.yaml
│ └─ workflow_registry.yaml
│
├─ schemas/
│ ├─ article.schema.json
│ ├─ intelligence.schema.json
│ ├─ source_health.schema.json
│ ├─ change_request.schema.json
│ ├─ claude_output.schema.json
│ └─ google_sheets_columns.json
│
├─ knowledge/
│ ├─ PLATFORM_CONSTITUTION.md
│ ├─ LX_HOLDINGS_CONTEXT.md
│ ├─ LX_HAUSYS_COMPANY_DNA.md
│ ├─ LX_HAUSYS_VALUE_CHAIN.md
│ ├─ GROUP_RISK_MAP.md
│ ├─ GROUP_OPPORTUNITY_MAP.md
│ └─ STRATEGY_PLAYBOOK.md
│
├─ prompts/
│ ├─ relevance_filter.md
│ ├─ risk_analysis.md
│ ├─ daily_change.md
│ ├─ policy_analysis.md
│ ├─ quick_scan.md
│ └─ natural_language_admin.md
│
├─ dashboard/
│ ├─ template.html
│ ├─ styles.css
│ ├─ app.js
│ ├─ sample_data.json
│ └─ current/
│
├─ scripts/
│ ├─ bootstrap_project.py
│ ├─ validate_config.py
│ ├─ create_drive_structure.py
│ ├─ create_google_sheets.py
│ ├─ claude_client.py
│ ├─ build_dashboard.py
│ ├─ n8n_deploy.py
│ ├─ n8n_backup.py
│ ├─ n8n_list_workflows.py
│ ├─ source_health_check.py
│ ├─ cost_guard.py
│ └─ secret_scan.py
│
├─ n8n/
│ ├─ workflows/
│ │ ├─ WF-P01-config-loader.json
│ │ ├─ WF-P02-news-collector.json
│ │ ├─ WF-P03-public-source-collector.json
│ │ ├─ WF-P04-relevance-classifier.json
│ │ ├─ WF-P05-risk-analysis.json
│ │ ├─ WF-P06-dashboard-builder.json
│ │ ├─ WF-P07-notification.json
│ │ ├─ WF-P08-source-health.json
│ │ ├─ WF-P09-cost-guard.json
│ │ ├─ WF-P10-natural-language-admin.json
│ │ └─ WF-P99-error-handler.json
│ └─ backups/
│
├─ tests/
│ ├─ fixtures/
│ ├─ test_config.py
│ ├─ test_schema.py
│ ├─ test_dashboard.py
│ ├─ test_cost_guard.py
│ ├─ test_source_health.py
│ ├─ test_n8n_json.py
│ └─ test_secret_scan.py
│
├─ output/
├─ logs/
└─ archive/
```

---

# 4. Build Task Index

| Task | 이름 | 선행 Task | 외부 쓰기 | 기본 상태 |
|---|---|---|---|---|
| TASK-001 | Project Scaffold | 없음 | 없음 | 자동 실행 |
| TASK-002 | Core Configuration | 001 | 없음 | 자동 실행 |
| TASK-003 | Data Schemas | 002 | 없음 | 자동 실행 |
| TASK-004 | Knowledge Templates | 001 | 없음 | 자동 실행 |
| TASK-005 | Google Drive Tooling | 002 | 승인 필요 | Dry-run |
| TASK-006 | Google Sheets Tooling | 002,003 | 승인 필요 | Dry-run |
| TASK-007 | n8n Workflow Scaffold | 002,003 | 없음 | JSON 생성 |
| TASK-008 | n8n API Deployment Tooling | 007 | 승인 필요 | Dry-run |
| TASK-009 | Claude API Client & Prompts | 002,003,004 | API 호출 승인 | Local test |
| TASK-010 | News Collection Logic | 007 | 없음 | Workflow JSON |
| TASK-011 | Relevance & Deep Analysis | 009,010 | API 호출 승인 | Mock first |
| TASK-012 | Dashboard | 003,011 | 없음 | Local build |
| TASK-013 | Gmail & Telegram | 012 | 승인 필요 | Disabled |
| TASK-014 | Source Health | 005,006,007 | 제한적 | Dry-run |
| TASK-015 | Cost Guard | 009 | 없음 | Local test |
| TASK-016 | Natural Language Admin | 002,003,007 | 승인 필요 | Proposal only |
| TASK-017 | Integration Test | 005~016 | 승인 필요 | Staged |
| TASK-018 | Pilot Deployment | 017 | 승인 필요 | Manual gate |

---

# 5. TASK-001 — Project Scaffold

## 목적

규정된 로컬 프로젝트 구조와 기본 관리파일을 생성한다.

## 입력

- 빈 폴더 또는 기존 프로젝트 폴더
- 본 Build Specification

## 수행

1. 최종 프로젝트 구조에 정의된 폴더 생성
2. 누락된 기본 파일 생성
3. `.gitignore` 생성
4. `.env.example` 생성
5. `README.md`, `PROJECT_STATUS.md`, `TODO.md`, `CHANGELOG.md` 초기화
6. Python 실행환경 파일 생성
   - `requirements.txt`
   - 선택적으로 `pyproject.toml`

## `.gitignore` 필수 항목

```gitignore
.env
.env.*
!.env.example
__pycache__/
*.pyc
.venv/
venv/
logs/
output/
archive/
n8n/backups/
*.key
*.pem
credentials*.json
token*.json
```

## 완료조건

- 모든 폴더 존재
- Secret 파일 추적 방지
- README에 기본 실행순서 포함
- 재실행해도 기존 파일을 파괴하지 않음
- `python scripts/bootstrap_project.py --dry-run` 성공

## 실패·Rollback

- 생성 실패 시 이미 생성한 빈 폴더만 제거 가능
- 기존 사용자 파일 삭제 금지
- 충돌 파일은 `.generated` 접미사로 별도 생성 후 보고

---

# 6. TASK-002 — Core Configuration

## 생성파일

- `config/project.yaml`
- `config/topics.yaml`
- `config/sources.yaml`
- `config/cost_policy.yaml`
- `config/notification.yaml`
- `config/drive_structure.yaml`
- `config/sheet_structure.yaml`
- `config/workflow_registry.yaml`

## 핵심 기본값

### project.yaml

```yaml
project:
  id: LCIP-PILOT
  name: LCIP Pilot
  timezone: Asia/Seoul
  pilot_mode: true
  information_class: public_only
  default_output_language: ko
  preserve_original_language: true
```

### topics.yaml

```yaml
topics:
  - topic_id: TOP-0001
    name: engineered_stone_silicosis
    display_name: 엔지니어드스톤·실리코시스
    mission: risk_management
    related_lx_companies:
      - LX_HAUSYS
    countries:
      - US
      - AU
      - CA
      - GB
      - EU
    languages:
      - en
      - ko
    include_keywords:
      - silicosis
      - engineered stone
      - artificial stone
      - quartz countertop
      - respirable crystalline silica
      - silica lawsuit
      - silica litigation
      - 규폐증
      - 엔지니어드스톤
      - 인조대리석
    exclude_keywords:
      - sports
    collection_interval_hours: 1
    send_only_on_change: true
    enabled: true
```

### cost_policy.yaml

```yaml
cost:
  monthly_budget_usd: 20
  target_budget_usd: 15
  warning_rate: 0.70
  restrict_rate: 0.90
  hard_stop_rate: 1.00
  daily_deep_analysis_limit: 5
  max_input_tokens_per_call: 8000
  max_output_tokens_per_call: 1200
  classify_without_ai_first: true
  use_prompt_cache_when_available: true
```

### notification.yaml

```yaml
notifications:
  timezone: Asia/Seoul
  active_send_start: "08:00"
  active_send_end: "20:00"
  night_queue_send_time: "08:00"
  send_only_on_change: true
  email_enabled: true
  telegram_enabled: true
  test_mode: true
```

## 규칙

- Secret 금지
- 모델명·Sheet ID·Folder ID는 환경변수 또는 Registry 참조
- 모든 값은 YAML validation 대상
- Config 변경은 향후 자연어 관리자 기능과 호환

## 완료조건

- YAML 문법 검증 통과
- 필수값 누락 검사
- 중복 `topic_id`, `source_id`, `workflow_id` 검사
- `python scripts/validate_config.py` 성공

---

# 7. TASK-003 — Data Schemas

## Article Schema 필수필드

```text
article_id
topic_id
title_original
title_ko
source_name
source_type
source_url
canonical_url
published_at
collected_at
language
country
summary_ko
litigation_amount_total
litigation_currency
litigation_amount_total_usd
claimant_count
average_amount_per_person_usd
related_companies
related_lx_companies
event_type
confidence_score
source_reliability_grade
duplicate_group_id
is_new_change
status
```

## Intelligence Schema 필수필드

```text
intelligence_id
article_ids
mission
fact_summary
verified_facts
ai_interpretation
ai_inference
lx_impact
recommended_actions
unknowns
confidence_score
evidence
created_at
prompt_version
knowledge_version
```

## Source Health Schema 필수필드

```text
source_id
checked_at
last_success_at
http_status
response_ms
record_count
latest_reference_date
health_status
consecutive_failures
error_type
error_message
recovery_action
```

## 완료조건

- JSON Schema Draft 2020-12 또는 호환 버전 사용
- 샘플 정상·비정상 fixture 검증
- 숫자·날짜·nullable 필드 명확화
- `pytest tests/test_schema.py` 성공

---

# 8. TASK-004 — Knowledge Templates

## 생성문서

- `PLATFORM_CONSTITUTION.md`
- `LX_HOLDINGS_CONTEXT.md`
- `LX_HAUSYS_COMPANY_DNA.md`
- `LX_HAUSYS_VALUE_CHAIN.md`
- `GROUP_RISK_MAP.md`
- `GROUP_OPPORTUNITY_MAP.md`
- `STRATEGY_PLAYBOOK.md`

## 문서 상단 공통 메타데이터

```yaml
---
information_class: public
document_type: knowledge
company:
source_types: []
reference_date:
last_reviewed:
source_urls: []
confidence: draft
version: 0.1
owner: user
---
```

## 작성 규칙

- 공개정보로 확인되지 않은 사실 작성 금지
- 미확인 내용은 `TODO: source required`
- 각 핵심 문장에 source ID 또는 URL 연결
- 사실·추론 분리
- LX홀딩스 관점, 미래준비·리스크관리 두 축 반영

## 완료조건

- 템플릿 구조 생성
- 임의의 회사 내부사실 없음
- Source placeholder 명확
- Claude API Context로 부분 로드 가능한 heading 구조

---

# 9. TASK-005 — Google Drive Tooling

## 생성파일

- `scripts/create_drive_structure.py`
- `config/drive_structure.yaml`
- `docs/GOOGLE_DRIVE_SETUP.md`

## 생성 대상

```text
LCIP_PILOT/
├─ 00_Project/
├─ 01_Knowledge/
├─ 02_Data/
├─ 03_Dashboard/
├─ 04_Reports/
├─ 05_Archive/
└─ 06_Admin/
```

## 기능요구

- `--dry-run`
- `--apply`
- 동일 이름 폴더 중복생성 금지
- 생성된 Folder ID 출력
- Folder ID Registry JSON 저장
- 부분 실패 시 이미 생성된 폴더 목록 기록
- 기존 폴더 삭제 금지

## 인증방식

Pilot에서는 아래 중 하나를 선택 가능하게 구현한다.

1. Google OAuth Desktop App
2. Service Account + 공유폴더 권한
3. n8n Google Drive Credential만 사용하고 로컬 Script는 구조 계획만 생성

Claude Code는 사용자 인증정보를 생성하거나 추정하지 않는다.

## 완료조건

- Dry-run 성공
- Mock API 테스트 성공
- 실제 생성 전 사용자 승인
- Secret 로그 미출력

---

# 10. TASK-006 — Google Sheets Tooling

## 생성파일

- `scripts/create_google_sheets.py`
- `config/sheet_structure.yaml`
- `schemas/google_sheets_columns.json`
- `docs/GOOGLE_SHEETS_SETUP.md`

## 생성 탭

1. CONFIG_MASTER
2. TOPIC_CONFIG
3. SOURCE_REGISTRY
4. ARTICLE_DB
5. INTELLIGENCE_DB
6. SOURCE_HEALTH
7. COST_LOG
8. SENT_HISTORY
9. ERROR_LOG
10. CHANGE_REQUEST
11. CHANGE_LOG

## 요구사항

- 기존 Spreadsheet ID가 있으면 탭 누락분만 생성
- 기존 탭 데이터 삭제 금지
- 헤더 버전 관리
- `dry-run`에서 생성 예정 탭과 컬럼 출력
- `apply`는 사용자 승인 후 수행
- Freeze row, 기본 필터, 날짜·금액 형식 설정
- Sheet ID를 코드에 하드코딩하지 않음

## 완료조건

- Mock 테스트
- 중복실행 안전성
- 컬럼 Schema와 일치
- 실제 생성 전 사용자 승인

---

# 11. TASK-007 — n8n Workflow Scaffold

## 생성 워크플로우

### WF-P01-config-loader

역할:
- Google Sheets 또는 Config 파일에서 Topic, Source, Cost, Notification 설정 로드

입력:
```json
{"topic_id":"TOP-0001","workflow_id":"WF-P02"}
```

출력:
```json
{
  "topic": {},
  "sources": [],
  "cost_policy": {},
  "notification_policy": {},
  "prompt_paths": [],
  "knowledge_paths": []
}
```

### WF-P02-news-collector

역할:
- 한국어·영어 Google News RSS 수집
- 게시일 필터
- URL 정규화
- 제목·URL 중복 제거
- ARTICLE_DB 저장
- AI 호출 금지

### WF-P03-public-source-collector

역할:
- DART
- 정부기관 RSS/API
- 공식 기업자료
- 향후 SEC·EDINET 확장 가능한 sub-workflow 구조

### WF-P04-relevance-classifier

역할:
- 규칙기반 1차 필터
- 애매한 건만 Claude API
- 관련성·미션·심층분석 여부 반환

### WF-P05-risk-analysis

역할:
- 신규 중요사건만 심층분석
- 사실, 금액, 인원, 규제단계, LX 영향, 추가조사 추출
- JSON Schema 검증

### WF-P06-dashboard-builder

역할:
- Tracker, 해외 현황, 규제 현황, 세이프가드 기사 생성
- 금액 추이 데이터 집계
- HTML 빌드·Drive 업로드

### WF-P07-notification

역할:
- Gmail 카드
- Telegram 요약
- 08:00~20:00 즉시
- 야간 변화는 08:00 큐 발송
- 변동 없으면 미발송

### WF-P08-source-health

역할:
- HTTP, API, RSS, Schema, Freshness 검사
- 오류 3회 연속 시 알림

### WF-P09-cost-guard

역할:
- Claude usage 집계
- 70%, 90%, 100% 단계 통제

### WF-P10-natural-language-admin

역할:
- 자연어 요청을 Change Request 초안으로 변환
- 직접 적용 금지
- Diff·영향·비용·승인 필요여부 생성

### WF-P99-error-handler

역할:
- 공통 오류 로깅
- 재시도
- 관리자 알림
- 민감정보 마스킹

## n8n JSON 공통규칙

- Import 가능한 JSON
- Workflow 기본 inactive
- Credential ID 하드코딩 금지
- Placeholder credential name 사용
- Manual Trigger 포함
- Error branch 포함
- Workflow 이름과 ID 규칙 준수
- 노드명은 목적이 명확한 한글 또는 영문
- n8n Starter 실행량을 줄이기 위해 sub-workflow 과도한 분할 금지

## 완료조건

- JSON parse 성공
- 필수 노드 구조 검사
- Secret scan 성공
- 가능하면 n8n schema lint
- 실제 n8n Import는 사용자 승인 후

---

# 12. TASK-008 — n8n API Deployment Tooling

## 생성파일

- `scripts/n8n_deploy.py`
- `scripts/n8n_backup.py`
- `scripts/n8n_list_workflows.py`
- `docs/N8N_API_SETUP.md`

## 환경변수

```env
N8N_BASE_URL=
N8N_API_KEY=
N8N_PROJECT_ID=
```

## 기능

- API 연결 테스트
- Workflow 목록 조회
- 이름 기반 중복검사
- 기존 Workflow JSON 백업
- 신규 생성
- 업데이트 전 diff 출력
- 기본 inactive 배포
- 배포 결과 Workflow ID 기록
- API Key 마스킹

## 안전장치

- 기본은 `--dry-run`
- `--apply`와 사용자 명시적 승인 없이는 쓰기 금지
- 기존 Workflow 삭제 금지
- 업데이트 실패 시 기존 버전 유지
- 활성화는 별도 명령

---

# 13. TASK-009 — Claude API Client & Prompts

## 생성파일

- `scripts/claude_client.py`
- `prompts/relevance_filter.md`
- `prompts/risk_analysis.md`
- `prompts/daily_change.md`
- `prompts/policy_analysis.md`
- `prompts/quick_scan.md`
- `prompts/natural_language_admin.md`

## API Client 요구

- 모델명 Config 참조
- API Key 환경변수
- timeout
- 제한적 retry
- usage 기록
- JSON Schema validation
- 입력 context clipping
- 전체 Knowledge Base 반복 전송 금지
- Prompt version 기록
- 1회 JSON repair 후 실패 시 검토대기

## 분석 출력 원칙

- 한국어 출력
- 원문 제목·URL·게시일 보존
- 확인된 사실
- AI 해석
- AI 추론
- 제안
- 미확인 사항
- 근거 링크
- confidence score

## 비용통제

- 키워드·출처·중복 필터 후에만 AI 호출
- 단순 계산은 AI 금지
- 신규 중요 변화만 심층분석
- 일간 심층분석 상한 5건 기본
- 월 예산 100% 도달 시 중단

---

# 14. TASK-010 — News Collection Logic

## 기본 검색 언어

- 영어: Primary global source
- 한국어: 국내 보완
- 일본어·중국어: Enterprise backlog

## 기본 검색축

### 실리코시스

```text
silicosis
engineered stone
artificial stone
quartz countertop
respirable crystalline silica
silica lawsuit
silica litigation
규폐증
엔지니어드스톤
인조대리석
```

### 세이프가드

```text
engineered stone safeguard
artificial stone safeguard
quartz surface safeguard
engineered stone tariffs
```

## 정규화

- Google News redirect URL에서 원문 URL 추출 시도
- original_url과 canonical_url 모두 저장
- 실패 시 Google News URL이라도 보존
- 제목 HTML entity 해제
- timezone UTC 저장 + 표시 KST
- 제목 유사도·canonical URL·게시일로 중복그룹 생성

## 완료조건

- 샘플 RSS fixture 수집
- 필수필드 저장
- AI 호출 없음
- 중복테스트 통과

---

# 15. TASK-011 — Relevance & Deep Analysis

## 1차 규칙기반 필터

- 포함·제외키워드
- 관련 기업·브랜드
- 출처 신뢰등급
- 게시일
- 국가
- 기존 중복사건

## Claude 분류 사용조건

- 규칙 점수가 중간구간
- 산업적 관련성은 있으나 명시 키워드가 부족
- 규제·소송 금액·원고 수 추출이 필요한 경우
- LX 영향 분석이 필요한 신규 중요 건

## 심층분석 필수 추출

- 사건명
- 국가·주
- 법원·기관
- 판결·합의·소송 상태
- 총 배상액
- 원고 수
- 인당 평균배상액
- 관련 기업·브랜드
- 제품유형
- 규제·입법 단계
- LX하우시스 관련성
- 사실·추론 구분
- 대응·추가조사
- 원문 링크

## 계산규칙

```text
인당 평균배상액 = 총 배상액 ÷ 원고 수
```

총액 또는 원고 수가 없으면 `null`. AI가 임의 추정 금지.

---

# 16. TASK-012 — HTML Dashboard

## 필수 구조

1. **실리코시스 소송 Tracker**
2. **미국 외 실리코시스 이슈 현황**
3. **미국 주별 규제·입법 현황**
4. **글로벌 규제·생산금지 현황**
5. **세이프가드 관련 소식**

## Tracker 필수열

- 게시일
- 지역
- 사건·기사명
- 피고·관련기업
- 사건유형
- 총 배상액
- 원고 수
- 인당 평균배상액
- 상태
- 원문 링크
- 비고

## 디자인 요구

- LX홀딩스 공시 홈페이지 및 지속가능보고서 인상 참고
- 한글 중심
- 과도한 장식 금지
- 표 셀 단어 비정상 분리 금지
- 모바일 대응
- 열 너비 고정·최소폭·가로스크롤 허용
- `>>` 대신 이상·초과·이하·미만
- 원문 보기 버튼
- 금액 추이 그래프
- 지도는 Pilot에서는 기본 제외하고 표 우선
- 오버롤 리스크는 강조 카드
- Executive Summary·우선순위·LX영향도 열은 제외

## 오늘의 주요변화

- 실제 신규 생성·변경된 이슈만
- 변동 없으면 "신규 주요 변화 없음"
- 기존 최대사건·종합위험도 반복표시 금지

---

# 17. TASK-013 — Gmail & Telegram

## Gmail 제목

```text
미국 엔지니어드스톤 리스크 알리미
```

## Gmail 본문

- 카드형 요약
- 오늘의 주요변화
- 신규 이슈 개수
- 핵심 변화 3건 이내
- 버튼 문구: `자세히 보기`
- 전체 HTML 본문을 이메일에 그대로 삽입하지 않음

## Telegram

- 3~6줄
- 신규 변화만
- 대표 원문 또는 Dashboard 링크
- HTML 전체 전송 금지

## 발송시간

- 08:00~20:00: 중요 신규 변화 즉시
- 20:00~08:00: 큐 적재 후 08:00 발송
- 변동 없으면 미발송

## 안전장치

- 기본 `test_mode: true`
- 실제 수신자 Config/환경변수
- 테스트 발송 승인
- SENT_HISTORY 기록
- 동일 이슈 중복발송 금지

---

# 18. TASK-014 — Source Health

## 검사영역

- HTTP status
- Redirect
- Response time
- Content type
- RSS/JSON/XML parse
- 필수필드
- 최신성
- 수집건수 급감
- CAPTCHA·로그인·오류페이지
- 링크 유효성

## 상태

```text
HEALTHY
DEGRADED
STALE
BROKEN_LINK
SCHEMA_CHANGED
AUTH_ERROR
RATE_LIMITED
CONTENT_INVALID
ANOMALY
```

## 재시도

- 1회 실패: 5분 후
- 2회 실패: 15분 후
- 3회 연속: 관리자 알림
- 핵심소스 전체중단: 즉시 알림

## 완료조건

- Mock 정상·404·429·HTML 오류페이지 테스트
- 상태분류 정확
- Secret 로그 없음

---

# 19. TASK-015 — Cost Guard

## 추적값

- model
- input_tokens
- output_tokens
- estimated_cost_usd
- workflow_id
- topic_id
- call_type
- created_at

## 단계별 통제

- 70%: 관리자 경고
- 90%: 심층분석은 긴급건만
- 100%: Claude API 자동중지
- 비용로그 실패 시 신규 심층분석 차단 가능

## 비용산식

모델별 단가는 Config 또는 Pricing Registry로 관리하며 코드에 영구 하드코딩하지 않는다.

## 완료조건

- 가상 usage fixture로 70/90/100% 테스트
- API 중단 조건 테스트
- 월 전환 테스트

---

# 20. TASK-016 — Natural Language Admin

## 목적

관리자가 자연어로 검색어·국가·기준·수신자·발송시간·Peer 등을 추가·변경하도록 한다.

## 운영원칙

자연어 명령은 직접 운영설정을 변경하지 않는다.

### 출력 예시

```json
{
  "request_id": "CR-20260805-0001",
  "intent": "update_topic",
  "target": "TOP-0001",
  "changes": [
    {
      "field": "countries",
      "before": ["US", "AU"],
      "after": ["US", "AU", "CA"]
    }
  ],
  "affected_workflows": ["WF-P02", "WF-P04", "WF-P05"],
  "estimated_cost_impact": "low",
  "risks": [],
  "requires_approval": true,
  "status": "PENDING_APPROVAL"
}
```

## 승인흐름

```text
Natural Language Request
→ Parse
→ Validation
→ Diff
→ Impact
→ User Approval
→ Config Version
→ Test
→ Apply
→ Change Log
```

## Pilot 제한

- Config 값 변경까지만
- 새로운 n8n Workflow 완전자동 생성은 Backlog
- Prompt 변경은 Draft 생성 후 승인
- 핵심 비용·보안 변수는 2차 확인

---

# 21. TASK-017 — Integration Test

## 통합 시나리오

1. 샘플 RSS 수집
2. 중복 제거
3. 관련성 판단
4. Mock Claude 출력 검증
5. ARTICLE_DB·INTELLIGENCE_DB 구조화
6. Dashboard 생성
7. Mock Drive Upload
8. Test Email
9. Test Telegram
10. Source Health 오류 감지
11. Cost hard stop
12. 변경 없음 미발송
13. 야간 큐 08:00 발송

## 산출물

- `TEST_REPORT.md`
- `DEPLOYMENT_REPORT.md`
- 실패목록
- 사용자 수동작업목록
- 남은 리스크

---

# 22. TASK-018 — Pilot Deployment

## 배포 Gate

다음 모두 충족해야 한다.

- Unit tests pass
- Integration tests pass
- Secret scan pass
- n8n JSON import 검증
- Google OAuth 연결 확인
- Google Sheets 생성 확인
- Drive 폴더 생성 확인
- Test Gmail/Telegram 확인
- Cost Guard 확인
- Workflow 기본 inactive
- 사용자 활성화 승인

## 활성화 순서

1. WF-P01 Config Loader
2. WF-P09 Cost Guard
3. WF-P99 Error Handler
4. WF-P08 Source Health
5. WF-P02 News Collector
6. WF-P04 Relevance Classifier
7. WF-P05 Risk Analysis
8. WF-P06 Dashboard Builder
9. WF-P07 Notification
10. 기타 확장

## Rollback

- 활성화 중 오류 시 해당 Workflow 비활성화
- 이전 JSON 백업 복원
- 최근 정상 Dashboard 유지
- 데이터 삭제 금지
- 오류로그·원인·조치 기록

---

# 23. 공통 Definition of Done

모든 Task는 아래를 충족해야 완료다.

- 기능 구현
- 정상경로 테스트
- 오류경로 테스트
- 재실행 안전성
- Secret scan
- 문서화
- Config·Schema 일치
- `PROJECT_STATUS.md` 갱신
- `TODO.md` 갱신
- `CHANGELOG.md` 갱신
- 사용자 작업과 자동작업 분리 보고

---

# 24. Claude Code가 사용자에게 반드시 질문해야 하는 항목

아래는 추정하지 말고 질문한다.

1. Google OAuth 방식: Desktop OAuth / Service Account / n8n Credential only
2. 기존 Google Drive Root Folder ID 존재 여부
3. 기존 Master Spreadsheet ID 존재 여부
4. n8n Base URL과 API Key 준비 여부
5. n8n API 자동배포 사용 여부 또는 수동 Import 여부
6. Claude API Key 준비 여부
7. 사용할 Claude 모델명
8. Gmail OAuth 연결 계정
9. Telegram Bot Token·Chat ID 입력 완료 여부
10. 테스트 수신 이메일
11. 실제 운영 발송 승인
12. DART API Key 보유 여부
13. Git 사용 여부
14. Google Drive Desktop 동기화 여부

질문은 한 번에 과도하게 하지 말고, 현재 Task에 필요한 것만 묻는다.

---

# 25. Claude Code 최초 실행 명령

사용자는 Claude Code Plan Mode에서 아래를 입력한다.

```text
프로젝트 루트의 CLAUDE.md와 연결된 모든 문서를 읽어라.

아직 파일을 수정하거나 외부 API를 호출하지 말고 다음을 먼저 출력해라.

1. 이해한 프로젝트 목적
2. Pilot 범위와 제외범위
3. 생성할 폴더 및 파일
4. TASK-001부터 TASK-018까지의 실행 순서와 의존성
5. 사용자 인증 또는 의사결정이 필요한 항목
6. 설계문서 간 충돌·모호성
7. 월 10만원 이하 및 Claude API USD 20 상한을 지키는 구현방안
8. 예상 위험과 Rollback 계획

계획 승인 전에는 어떤 파일도 수정하지 마라.
```

---

# 26. Scaffold 승인 후 실행 명령

```text
계획을 승인한다.

03_BUILD_SPECIFICATION.md의 TASK-001부터 TASK-007까지 수행해라.

조건:
- 외부 API 실제 호출 금지
- Google Drive·Google Sheets 실제 생성 금지
- n8n 실제 배포 금지
- 이메일·Telegram 실제 발송 금지
- 모든 외부 기능은 dry-run 또는 mock으로 구현
- 각 Task마다 Acceptance Test 실행
- 기존 파일 덮어쓰기 금지
- PROJECT_STATUS.md, TODO.md, CHANGELOG.md 갱신
- 완료 후 생성 파일 목록, 테스트 결과, 남은 사용자 입력을 보고
```

---

# 27. 외부 연결 승인 후 실행 명령

```text
TASK-001부터 TASK-007의 로컬 구현과 테스트 결과를 승인한다.

이제 아래 순서로 외부 연결을 진행해라.

1. n8n API 연결 테스트
2. Google OAuth 연결 가이드 실행
3. Google Drive 구조 dry-run
4. Google Sheets 구조 dry-run
5. 사용자에게 생성·변경 예정사항 제시
6. 명시적 승인 후 apply
7. n8n Workflow를 비활성 상태로 배포
8. 테스트 데이터로 통합 테스트
9. 이메일·Telegram은 테스트 수신자에게만 발송
10. 운영 Workflow 활성화는 별도 승인 요청

각 외부 쓰기 단계 전 사용자 승인을 확인해라.
```

---

# 28. 최종 성공기준

LCIP Pilot은 다음 상태에서 성공으로 판단한다.

- Google News RSS 영어·한국어 수집
- 실리코시스·엔지니어드스톤 신규 이슈 추적
- 소송 총액·원고 수·인당 평균액 구조화
- 미국 외 국가 이슈 표
- 미국 주별·글로벌 규제 현황 표
- 세이프가드 관련 기사 목록
- 모든 항목 원문 링크
- 신규 중요 변화만 알림
- 08:00~20:00 즉시, 야간은 08:00 발송
- HTML Dashboard Drive 저장
- Gmail 카드·Telegram 요약
- Source Health 동작
- Claude API 예산 상한 동작
- 공개정보만 사용
- Claude Code가 생성·테스트·문서 갱신을 반복 수행할 수 있음
