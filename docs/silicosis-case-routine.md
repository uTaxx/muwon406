# 실리코시스 소송 사건 조사 루틴

매일 아침 07:00(KST) Claude 루틴이 이 절차를 수행한다.
목적은 **새로 보도된 미국 엔지니어드스톤 실리코시스 평결을 사건 원장에 올리는 것**이다.

전에는 n8n이 Claude API를 직접 호출했으나(건당 약 $0.15), 지금은 루틴 세션이
직접 조사한다. n8n은 조회·저장만 담당하며 AI 호출을 하지 않는다.

## 도구

n8n MCP 커넥터를 쓴다. 웹훅이나 Google Sheets API는 이 환경에서 직접 호출할 수
없으므로(프록시 403), 반드시 아래 두 워크플로우를 통해서만 시트에 접근한다.

| 용도 | 워크플로우 ID | 호출 방법 |
|---|---|---|
| 후보 조회 | `Ex5xjPkmBjqVopuB` | `execute_workflow` (executionMode: `manual`, inputs 없음) |
| 사건 등록 | `VOV4X1Y9xf2yY98N` | `execute_workflow` (executionMode: `manual`, inputs: form) |

`execute_workflow`는 executionId만 즉시 돌려준다. 결과는
`get_workflow_execution`에 `includeData: true`로 읽는다.
후보 조회는 `nodeNames: ["후보선별"]`, 등록은 `nodeNames: ["등록결과"]`를 지정하면
필요한 부분만 나온다.

## 절차

### 1단계 — 후보 조회

`Ex5xjPkmBjqVopuB`를 실행하고 `후보선별` 노드의 출력을 읽는다.

```
{
  candidateCount: 0,
  candidates: [{ title, link, group, importance, date }],
  existingCases: [{ id, caseName, caseNumber, plaintiff, verdictDate, status }]
}
```

`candidateCount`가 0이면 **여기서 끝낸다.** 아무것도 하지 말고 조용히 종료한다.
매일 아침 "오늘은 없습니다" 같은 보고를 남기지 않는다.

### 2단계 — 이미 아는 사건 걸러내기

후보 제목을 `existingCases`와 대조한다. 같은 평결로 보이면 **조사하지 않고 뺀다.**

기사 링크는 대개 Google News 리다이렉트라 원장의 출처링크와 문자열이 다르다.
그래서 링크가 아니라 **내용**으로 판단해야 한다. 예를 들어 후보 제목이
"$7.1 Million Plaintiff's Verdict in the Fifth Artificial Stone ... Trial"이고
`existingCases`에 평결일 2026-08-19, 원고 Ramirez-Soriano 건이 있으면 같은 평결이다.

판단 근거:
- 평결 금액이 같은가
- 평결일이 비슷한가 (후속 보도는 며칠 늦다)
- 피고 기업이 겹치는가

애매하면 조사한다. 등록 단계에서 사건번호·사건명·원고+평결일로 한 번 더 걸러진다.

### 3단계 — 조사

남은 후보마다 웹 검색으로 사실을 확인한다. 기사 제목만으로 채우지 말고,
반드시 검색해서 **원 보도(로펌 보도자료, 법률 전문지, 주요 일간지)**를 근거로 삼는다.

확인할 것:
- 정식 사건명과 사건번호, 관할 법원
- 평결일, 원고(사망 사건이면 유족 관계까지)
- 총 평결액과 경제적/비경제적 손해 내역
- **당사자별 책임 배분** — 이게 이 원장의 핵심이다
- 고용주 책임비율, 피해 노동자 과실비율

책임 배분에서 역할(`role`)은 넷 중 하나로 분류한다.
- `제조사` — 슬래브를 만든 회사
- `유통사` — 만들지 않고 팔기만 한 회사
- `가공업체` — 재단·설치하는 업체 (대개 피해자의 고용주)
- `기타` — 위에 안 들어가거나 특정되지 않은 당사자

같은 기업집단이라도 제조 법인과 유통 법인이 **따로 피고인 경우 각각 다르게**
분류한다. 예: `Dal-Tile, LLC` = 제조사 / `Dal-Tile Distribution, LLC` = 유통사.

확인되지 않은 값은 **지어내지 말고 비운다.** 빈 문자열이나 필드 생략 둘 다 좋다.
특히 금액과 비율은 추정치를 넣지 않는다 — 이 숫자들이 대시보드 집계에 그대로 들어간다.

### 4단계 — 등록

`VOV4X1Y9xf2yY98N`을 form 입력으로 실행한다.

```
inputs: {
  type: "form",
  formData: { payload: "<사건 객체 JSON 배열 문자열>" }
}
```

사건 객체 필드:

| 필드 | 타입 | 설명 |
|---|---|---|
| `caseName` | string | 정식 사건명 (필수에 가까움) |
| `caseNumber` | string | 사건번호 |
| `court` | string | 관할 법원 |
| `verdictDate` | string | `YYYY-MM-DD` |
| `plaintiff` | string | 원고 |
| `totalUsd` | number | 총 평결액 (USD, 숫자만) |
| `economicUsd` | number | 경제적 손해 |
| `nonEconomicUsd` | number | 비경제적 손해 |
| `employerPct` | number | 고용주 책임비율 (%) |
| `plaintiffFaultPct` | number | 피해 노동자 과실비율 (%) |
| `allocation` | array | `[{ party, pct, role }]` |
| `summary` | string | 한국어 요약. 평결 경위와 책임 배분 근거를 3~5문장 |
| `sourceUrl` | string | 근거 원문 URL (Google News 리다이렉트 말고 원 기사) |

`caseName`과 `caseNumber`가 **둘 다** 없으면 등록되지 않는다.

`등록결과` 노드가 `{ saved, savedCases, skipped, errors }`를 돌려준다.
`skipped`에 "이미 등록된 사건"이 있으면 정상이다 — 2단계에서 못 거른 중복을
등록 단계가 잡아준 것이다.

### 5단계 — 마무리

등록된 사건은 **`검토대기`** 상태로 들어가며, 담당자가 대시보드에서 승인하기
전까지 지표·표·평균 책임 배분 어디에도 반영되지 않는다. 이게 의도된 동작이다.
루틴이 승인까지 하지 않는다.

새로 등록한 건이 있으면 무엇을 넣었는지 한 줄로 남긴다. 없으면 아무것도 남기지 않는다.

## 하지 말 것

- 사건 원장 시트를 직접 수정하지 말 것. 반드시 `LXGroup_사건등록`을 거친다.
- 이미 등록된 사건의 숫자를 갱신하려 하지 말 것. 사람이 확인한 값을 덮어쓰게 된다.
- 확인 안 된 금액·비율을 채워 넣지 말 것.
- 승인(`확인완료`) 처리를 하지 말 것. 담당자 몫이다.
- 후보가 없는 날 굳이 보고를 만들지 말 것.
