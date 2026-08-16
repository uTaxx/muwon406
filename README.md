# muwon406 — 코스피/코스닥 자동매매 시스템

한국투자증권(KIS) API 기반, 규칙기반 전략에서 시작해 ML 신호로 고도화하는
자동매매 시스템. 백테스트 → 모의투자 → 소액 실거래 순으로 검증하며 진행합니다.

## 구조

```
src/muwon/
├── config.py       # 부트스트랩 설정 (.env: DB URL, 암호화 키만)
├── settings/       # 런타임 설정 (KIS 인증정보/텔레그램/리스크 정책, DB 저장)
├── domain/         # 공통 타입/인터페이스 (Strategy, MarketDataSource, OrderExecutor)
├── data/           # KIS API 클라이언트 — 시세 수집
├── strategy/       # 규칙기반 → ML 전략 (Phase 1~3)
├── risk/           # 리스크 매니저 — 주문 실행 전 최종 검증
├── execution/       # 주문 실행기 (모의/실전 전환, Phase 2)
├── backtest/       # 백테스트 엔진 (Phase 1)
├── notify/         # 텔레그램 알림
├── dashboard/      # 설정 관리 웹 대시보드 (Streamlit)
└── db/             # 시세/신호/주문/설정 저장 (SQLite → 운영 시 Postgres 전환 가능)

scripts/
├── configure.py       # 대시보드와 동일한 SettingsService를 쓰는 설정 CLI
├── run_backtest.py    # 과거 데이터로 전략 백테스트
├── run_dry_run.py     # KIS 없이 신호→리스크→체결→알림→기록 파이프라인 검증(가짜 체결)
└── run_paper_trading.py  # KIS 모의투자 계좌로 실제 매매 (KIS 네트워크 접근 필요)
```

KIS 인증정보·텔레그램 토큰·리스크 정책은 `.env`가 아니라 DB에 저장되어,
재시작 없이 CLI나 웹 대시보드에서 값을 바꿀 수 있습니다. 설계 배경은
[`docs/config_architecture.md`](docs/config_architecture.md) 참고.

## 설정 대시보드

```bash
pip install -e ".[dashboard]"
streamlit run src/muwon/dashboard/app.py
```

한 화면에서 설정 조회/수정, 변경 이력, 개발 로그(git 커밋)까지 다 보이는
통합 도구입니다. `scripts/configure.py`와 동일한 `SettingsService`를
거치므로 저장 위치·형식은 CLI와 완전히 같습니다.

- **자동매매 킬스위치**: 화면 상단 토글로 즉시 on/off — 끄면 `RiskManager`가
  신규 진입 신호를 전부 거부합니다.
- **실시간 갱신**: 변경 이력(5초)·개발 로그(20초)는 `st.fragment(run_every=...)`로
  자동 새로고침되어, 다른 프로세스(CLI, 봇)가 값을 바꿔도 클릭 없이 반영됩니다.
- **변경 이력**: 설정값이 바뀔 때마다 이전값→새값이 자동 기록됩니다. 비밀값은
  `MUWON_MASTER_KEY`가 있을 때만 마스킹 표시됩니다.

비밀값(앱시크릿, 봇토큰 등)을 저장/조회하려면 `MUWON_MASTER_KEY`가 `.env`에
설정되어 있어야 합니다. 대시보드 하단 "보유 종목 & 최근 주문"에서 실제
매매 파이프라인(아래 참고)이 만든 포지션·주문을 5초마다 자동 갱신되는
표로 볼 수 있습니다.

## 매매 파이프라인 (Phase 2)

`src/muwon/execution/engine.py`의 `TradingEngine`이 신호 생성 → 리스크
매니저 승인 → 주문 체결 → 텔레그램 알림 → DB 기록을 한 번에 처리합니다.
매일 장 마감 후 1회(`run_once()`) 도는 걸 전제로 설계했습니다.

시세 소스와 주문 실행기를 무엇으로 주입하느냐에 따라 두 가지 경로가 있습니다.

- **`scripts/run_dry_run.py`** — 시세는 Yahoo Finance, 체결은
  `SimulatedOrderExecutor`(KIS 서버를 거치지 않고 로컬에서 체결됐다고
  가정)로 처리합니다. KIS 네트워크 접근이 안 되는 환경에서도 파이프라인
  전체(리스크 검증·텔레그램 알림 문구·DB 기록)를 오늘 바로 검증할 수
  있습니다. **KIS 모의투자가 아닙니다** — 진짜 매매 파이프라인 배관을
  테스트하는 용도입니다.
- **`scripts/run_paper_trading.py`** — 시세·체결 모두 `KISClient`를 거쳐
  KIS 모의투자 서버로 실제 주문을 넣습니다. KIS API가 비표준 포트
  (9443/29443)를 쓰기 때문에 egress 정책에 따라 접근이 막혀 있을 수
  있습니다 — 이 저장소를 개발한 환경은 실제로 막혀 있어 이 스크립트
  자체는 검증하지 못했습니다. KIS 네트워크 접근이 되는 환경(운영 서버
  등)에서, KIS 모의투자 앱키를 먼저 넣고 실행하세요.

두 경로 모두 같은 `TradingEngine`·`RiskManager`·`TelegramNotifier`를
쓰므로, KIS 접근이 열리면 데이터소스/실행기만 바꿔 끼우면 됩니다.

매수/매도가 체결되면 텔레그램으로 `🟢 매수 체결` / `🔴 매도 체결` 메시지가
갑니다(봇토큰 미설정 시엔 로그로만 남습니다). 리스크 매니저가 거부한
신호는 알림을 보내지 않고 실행 결과에만 남습니다.

## 로드맵

1. **Phase 0**: 저장소 구조, 리스크 매니저 기본 로직, KIS API 신청 가이드
2. **Phase 1**: 데이터 수집 파이프라인 + 규칙기반 전략 + 백테스트 엔진
3. **Phase 2** (진행 중): 매매 파이프라인(신호→리스크→체결→알림→기록) +
   설정 대시보드 — KIS 실제 연동은 네트워크 접근이 되는 환경에서 검증 필요
4. **Phase 3**: ML 신호 고도화
5. **Phase 4**: 소액 실거래 전환

## 시작하기

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env  # DB URL, 암호화 키 채워넣기 (docs/kis_api_setup.md 참고)

pytest
```

## KIS API 신청 및 설정

아직 앱키를 발급받지 않았다면 [`docs/kis_api_setup.md`](docs/kis_api_setup.md)를
따라 진행하세요. 발급 후에는 `python scripts/configure.py kis ...`로
저장합니다.

## 리스크 정책

기본 리스크 규칙은 [`docs/risk_policy.md`](docs/risk_policy.md)에 정리되어
있으며, `python scripts/configure.py risk ...`로 조정할 수 있습니다.
