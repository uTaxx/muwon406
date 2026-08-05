---
information_class: public
document_type: knowledge
company: LX Holdings (플랫폼 자체 규정)
source_types: []
reference_date:
last_reviewed: 2026-08-05
source_urls: []
confidence: draft
version: 0.2
owner: user
---

# Platform Constitution — LCIP Pilot 운영 헌법

> 이 문서는 회사 사실이 아니라 **LCIP Pilot 자체의 운영 원칙**을 정의한다. `CLAUDE.md`의
> "절대 원칙"과 동일한 내용을 Knowledge Base 형태로도 제공하여 Claude API 분석 시 Context로
> 함께 로드할 수 있게 한다.

## 1. 정보 사용 원칙

- 외부 **공개정보만** 사용한다.
- 내부 보고서, 비공개 실적, 미공개 투자안, 사내 이메일·회의록은 요구하거나 추정하지 않는다.
- 모든 핵심 사실에는 원문 URL을 저장한다.

## 2. 분석 출력 원칙

- 확인된 사실(verified_facts) / AI 해석(ai_interpretation) / AI 추론(ai_inference) / 제안
  (recommended_actions)을 항상 구분하여 출력한다.
- 모든 분석은 LX홀딩스와 관련 계열사 관점에서 수행한다.
- 근거 없는 LX 영향 단정을 하지 않는다. 불확실하면 `unknowns`에 기록한다.

## 3. 비용 원칙

- AI가 필요 없는 작업(정규화, 중복제거, 날짜필터, 단순 계산)에는 Claude API를 호출하지 않는다.
- Claude API 월 사용액: 목표 $15, 절대 상한 $20.

## 4. 보안 원칙

- API Key, OAuth Secret, Telegram Token, Chat ID는 `.env` 또는 n8n Credential에만 저장한다.
- Secret을 코드, Markdown, JSON, Google Sheets, Git에 평문 저장하지 않는다.
- 실제 외부 쓰기(Drive/Sheets 생성, n8n 배포, 이메일·Telegram 발송)는 사용자 승인 전까지
  금지한다.

## 5. 미션 정의

상세 서브카테고리 및 판단 규칙은 `knowledge/MISSION_FRAMEWORK.md`를 따른다 (요약):

- **미래준비**: 산업·정책·기술·자본시장 변화 탐지, M&A/Carve-out/Bolt-on/JV/Venture 기회
  탐색, 기업 Quick Scan (`knowledge/INVESTMENT_FRAMEWORK.md` 참고).
- **리스크 관리**: 소송·제품책임·산업안전·환경·통상·공급망·정책·ESG 리스크 조기 감지,
  계열사·사업·Value Chain 영향 경로 분석 (`knowledge/ANALYSIS_FRAMEWORK.md` 참고).

## 6. Knowledge 작성 원칙

Knowledge Base(`knowledge/*.md`)는 `knowledge/KNOWLEDGE_POLICY.md`의 16계층 Taxonomy와
`knowledge/SOURCE_PRIORITY.md`의 출처 우선순위를 따라 작성한다.

TODO: source required — 이 문서는 규정 문서이므로 외부 출처가 필요하지 않으나, 향후 LX홀딩스
공식 거버넌스 문서와 연계할 경우 해당 출처를 여기에 추가한다.
