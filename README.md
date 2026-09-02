# LX Group MI

LX홀딩스 경영전략팀용 뉴스·공시 모니터링 대시보드입니다.
수집과 발송은 n8n(`sondullab.app.n8n.cloud`)이 하고, 이 저장소는 **화면만** 담습니다.

## 주소

<https://utaxx.github.io/muwon406/lxgroup-mi/hub.html>

## 구성

| 파일 | 역할 |
|---|---|
| `public/lxgroup-mi/hub.html` | 본체. 전체 기사 조회 / 키워드 신청·변경 / 특정 키워드 검색 / 실리코시스 리스크 / AI 학습 데이터 6개 탭과 관리자용 비용 화면 |
| `public/lxgroup-mi/manual.html` | 사용설명서 |
| `public/lxgroup-mi/index.html`<br>`public/lxgroup-mi/articles.html` | 통합 전 옛 주소로 들어와도 열리도록 hub.html로 넘겨주는 스텁 |
| `public/index.html` | 사이트 첫 화면 → hub.html |
| `docs/silicosis-case-routine.md` | 실리코시스 사건 조사 루틴 절차 |

## 배포

`main`에 푸시하면 `.github/workflows/deploy.yml`이 `public/`을 그대로 GitHub Pages에 올립니다.
빌드 단계가 없습니다 — 의존성 없는 정적 HTML이라 빌드할 것이 없고, 단계를 두면
그 단계가 깨질 때 대시보드까지 같이 멈추기 때문입니다.

## 화면이 부르는 것

hub.html은 n8n 웹훅을 직접 호출합니다(`lxgroup-articles`, `lxgroup-intake`,
`lxgroup-lookup`, `lxgroup-instant`, `lxgroup-adhoc-search`, `lxgroup-feedback`,
`lxgroup-cases`, `lxgroup-case-status`, `lxgroup-knowledge`,
`lxgroup-delete-articles`, `lxgroup-api-cost`).

**이 저장소는 공개입니다.** 비밀값은 두지 않습니다 — 비용 조회와 기사 삭제의
관리자 비밀번호는 설정 시트에 있고 확인은 웹훅(서버)에서 합니다.

## 운영 — 실패했을 때

수집·발송 워크플로가 실패하면 **`LXGroup_실패알림`**(n8n)이 관리자 텔레그램으로
바로 알립니다. 어느 워크플로가 어느 노드에서 왜 멈췄는지와 실행 링크를 보냅니다.
`LXGroup_MI` · `LXGroup_지표수집` · `LXGroup_신청접수` · `LXGroup_콜백처리`의
'오류 워크플로'로 걸려 있습니다.

`LXGroup_MI_Sub`에는 일부러 걸지 않았습니다. 하위에서 죽어도 그 노드 이름이
마스터 오류에 실려 올라오므로, 양쪽에 걸면 같은 실패로 알림이 두 번 옵니다.

외부를 부르는 노드에는 재시도가 걸려 있습니다(조회·RSS·네이버·DART·Claude 호출·
시트 저장). **이메일과 텔레그램 발송에는 일부러 걸지 않았습니다** — 재시도하다
중복 발송되면 같은 다이제스트가 수신자 전원에게 두 번 갑니다. 늦게 오는 것보다
나쁩니다.

### 발송 시각을 바꿀 때

시각은 **설정 시트의 `발송시각`이 근거**입니다. 그런데 `LXGroup_MI`의 스케줄
트리거에도 같은 시각이 적혀 있어, **두 곳을 같이 고쳐야 합니다.** 한쪽만 고치면
트리거가 안 깨우거나(수집 자체가 없음) 깨워도 그냥 지나갑니다.

2026-09-03에 이걸로 11시 수집이 하루 빠졌습니다. 실행 기록만 보고 "실제로 도는
건 07시·16시뿐"이라고 판단해 트리거에서 11시를 뺐는데, 시트에는 처음부터
`07:00, 11:00, 16:00` 세 번이었습니다. **실행 기록은 그 시각에 무슨 일이
있었는지만 말해 줍니다. 무슨 시각이어야 하는지는 시트가 말합니다.**
