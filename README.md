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
