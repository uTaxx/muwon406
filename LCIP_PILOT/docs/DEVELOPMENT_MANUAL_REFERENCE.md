# LCIP Pilot Development Manual v1.0 (참고용)

> 원본: Google Drive `02_LCIP_Pilot_Development_Manual.md` (원문 그대로 보존). 실행 순서와
> Task 정의의 최종 근거는 `03_BUILD_SPECIFICATION.md`이며, 본 문서는 개발 관행·운영 점검·장애
> 대응 참고자료로만 사용한다. 폴더 구조·Sheets 탭 개수 등 `03_BUILD_SPECIFICATION.md`와 다른
> 부분은 `04_DATA_AND_CONFIG_SCHEMA.md`의 "설계문서 충돌 로그"를 따른다.

## 0. 개발 목표

Google Drive·Google Sheets·n8n Cloud·Claude API를 이용해 월 10만원 이하로 운영 가능한 LCIP Pilot을 구축한다. 첫 번째 작동 주제는 실리코시스·엔지니어드스톤 리스크이며, 이후 정부 정책과 DART 공시로 확장한다.

---

## 1. 준비물

### 필수 계정

- Google Workspace Starter
- n8n Cloud Starter
- Claude Pro
- Anthropic API Console 계정 및 API Key
- Telegram Bot
- Gmail 발신 계정

### 권장 도구

- Claude Code
- GitHub 비공개 저장소 또는 로컬 Git
- VS Code
- Node.js LTS
- Python 3.11 이상

### 비밀정보 관리

다음 값은 문서·코드·Google Sheet에 평문으로 저장하지 않는다.

- ANTHROPIC_API_KEY
- Telegram Bot Token
- Gmail OAuth Credential
- n8n API Key
- Google OAuth Client Secret

n8n Credentials 또는 로컬 `.env`에만 저장하고 Git에는 포함하지 않는다.

---

## 2. Git 기본 원칙

- `main`: 안정 버전
- `develop`: 통합 개발
- `feature/*`: 기능 단위
- `fix/*`: 오류 수정
- 모든 n8n JSON 변경은 커밋
- Prompt·Knowledge 변경도 코드와 동일하게 버전관리

---

## 3. Google Drive 구축

1. `LCIP_PILOT` 최상위 폴더 생성
2. 설계도에 정의된 하위 폴더 생성
3. 원본 파일과 AI용 Markdown을 분리
4. `CURRENT`와 `ARCHIVE` 폴더 분리
5. Drive 폴더 ID를 `CONFIG_MASTER`에 저장

### 문서 메타데이터 표준

```yaml
information_class: public
company: LX Hausys
source_type: DART
reference_date: 2025-12-31
last_reviewed: 2026-08-05
source_urls:
  - https://...
confidence: high
version: 1.0
```

---

## 4. Google Sheets 구축

하나의 Master Spreadsheet에 다음 탭을 생성한다.

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

각 시트의 첫 행은 고정 헤더로 유지하고, 컬럼명은 설계도 기준을 사용한다.

### 데이터 ID 규칙

- Topic: `TOP-0001`
- Source: `SRC-0001`
- Article: `ART-YYYYMMDD-XXXX`
- Intelligence: `INT-YYYYMMDD-XXXX`
- Change Request: `CR-YYYYMMDD-XXXX`

---

## 5. 초기 Knowledge Base 작성

Pilot에서는 아래 6개 문서를 우선 완성한다.

1. `PLATFORM_CONSTITUTION.md`
2. `LX_HOLDINGS_CONTEXT.md`
3. `LX_HAUSYS_COMPANY_DNA.md`
4. `LX_HAUSYS_VALUE_CHAIN.md`
5. `GROUP_RISK_MAP.md`
6. `STRATEGY_PLAYBOOK.md`

### LX하우시스 Company DNA 필수 항목

- 사업 포트폴리오
- 주요 제품
- 생산·판매 지역
- 고객 산업
- 주요 원재료
- 경쟁사
- 성장 Driver
- Risk Driver
- 미국 사업 및 엔지니어드스톤 관련 노출
- DART·지속가능보고서·IR·공식 홈페이지 원문 링크

---

## 6. Anthropic API 설정

1. Anthropic Console에서 API Key 발급
2. 자동 충전 OFF
3. 초기 선불 충전 10달러 권장
4. n8n Credential에 Key 저장
5. 테스트 호출 1회 수행
6. 응답의 `usage.input_tokens`, `usage.output_tokens`를 COST_LOG에 기록

### 모델 사용 원칙

- 사전 필터: AI 미사용
- 1차 분류: 저비용 모델 우선
- 심층 분석: Sonnet급 모델
- 최종 종합: 중요 건에만 Sonnet급 모델

모델명은 CONFIG_MASTER에서 변경 가능하도록 한다.

---

## 7. n8n 워크플로우 개발 순서

### Step 1. WF-P01 Configuration Loader

입력: `topic_id`, `workflow_id`

처리: CONFIG_MASTER 조회 → TOPIC_CONFIG 조회 → 관련 Source·Prompt·Knowledge 경로 반환

### Step 2. WF-P02 News Collector

- Schedule Trigger: 1시간
- Google News RSS Read
- 한국어·영어 Query 분리
- 게시일 필터
- URL canonicalization
- 제목 토큰 유사도 중복제거
- ARTICLE_DB 저장
- AI 호출 금지

### Step 3. WF-P03 Public Source Collector

- DART API
- 정부 보도자료 RSS/API
- 기업 공식 홈페이지 RSS/HTML
- Source별 Sub-workflow 사용

### Step 4. WF-P04 Relevance Classifier

1차 규칙: 포함·제외 키워드, 신뢰등급, 게시일, 관련 기업명. 애매한 건만 Claude 호출.

### Step 5. WF-P05 Risk Analysis

입력: 신규 원문, 관련 LX Context 일부, 기존 사건 Timeline 일부

### Step 6. WF-P06 Dashboard Builder

INTELLIGENCE_DB 조회 → Chart용 숫자 집계는 Code 노드 → HTML Template 변수 주입 → Drive CURRENT/ARCHIVE 저장

### Step 7. WF-P07 Notification

08:00~20:00 즉시, 그 외 시간은 08:00 예약. 제목: "미국 엔지니어드스톤 리스크 알리미"

### Step 8. WF-P08 Source Health

HTTP Status, Content-Type, 응답시간, 최소 레코드 수, 최신 게시일, 필수 필드, 3회 연속 실패 시 알림

### Step 9. WF-P09 Cost Guard

매 호출 후 COST_LOG 기록, 월 누적 비용 계산, 70% 경고/90% 제한/100% 중지

### Step 10. WF-P10 Natural Language Admin

변경 대상 식별 → 현재 값 조회 → 변경안 JSON 생성 → 영향 Workflow·예상 비용 표시 → CHANGE_REQUEST 저장 → 승인 대기 → 새 Config Version 생성

---

## 8. Prompt 개발 규칙

1. 모든 Prompt는 Markdown 파일로 관리
2. Prompt ID와 Version 명시
3. 출력 JSON Schema 강제
4. 사실·추론·제안 분리
5. 원문에 없는 내용을 단정하지 않음
6. LX 관련성 근거 명시
7. 미확인사항 표시
8. 한국어 출력, 원문 링크 유지

---

## 9. 테스트 전략

### 단위 테스트

URL 정규화, 중복제거, 날짜 필터, 금액 파싱, 비용 계산, Source Health 판정

### 통합 테스트

RSS → ARTICLE_DB, ARTICLE_DB → Claude → INTELLIGENCE_DB, DB → Dashboard, 신규 이슈 → Email/Telegram, Budget 90% → 분석 제한

### 회귀 테스트 데이터

최소 20건의 고정 기사 세트: 관련 높음 8건, 관련 낮음 6건, 중복 3건, 깨진 링크 2건, 접근 제한 1건

---

## 10. 배포 절차

```text
개발 Branch
→ 로컬/수동 테스트
→ n8n 비활성 Import
→ Test Credential 연결
→ 샘플 실행
→ 데이터 검증
→ Production Credential 연결
→ Workflow 활성화
→ 24시간 관찰
→ CHANGELOG 기록
```

---

## 11. 운영 점검

### 매일
수집 0건 Source 확인, Claude 비용 확인, 알림 실패 확인

### 매주
깨진 링크 점검, 오탐·누락 샘플 검토, 검색어 조정, Dashboard Archive 확인

### 매월
API 비용, n8n 실행량, Knowledge 기준일, Prompt 성능, 사용자 활용 사례, Pilot KPI

---

## 12. 장애 대응

### RSS 수집 0건
Feed URL 확인 → 직접 브라우저 접근 → Source Health 확인 → 검색 Query 인코딩 확인 → 대체 Source 전환

### Claude 오류
API 잔액 → Rate Limit → Model Name → Token Limit → JSON 파싱 실패 시 1회 재호출

### Google Sheets 오류
권한 → Row Limit → 컬럼명 변경 → Batch Write 적용

### 발송 오류
Gmail OAuth → Telegram Chat ID → HTML 크기 → 중복발송 Key

---

## 13. Pilot 종료 및 Enterprise 판단

2~3개월 운영 후 다음을 평가한다: 월 비용, 업무시간 절감, 주요 이슈 포착률, 사용자 만족도, 경영진 보고 활용 횟수, 보안·권한 요구사항, 전 계열사 확대 필요성.
