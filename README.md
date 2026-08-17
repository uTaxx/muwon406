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
├── analysis/       # 전략 가설 비교(스윕/일일 리뷰) 공용 로직
├── notify/         # 텔레그램 알림
├── dashboard/      # 설정 관리 웹 대시보드 (Streamlit, 폰/PC 상시 접속 가능)
├── cloud/          # 상태 DB 구글드라이브 동기화 (GitHub Actions·대시보드 공용)
└── db/             # 시세/신호/주문/설정 저장 (SQLite → 운영 시 Postgres 전환 가능)

scripts/
├── configure.py           # 대시보드와 동일한 SettingsService를 쓰는 설정 CLI
├── run_backtest.py        # 과거 데이터로 전략 백테스트
├── run_dry_run.py         # KIS 없이 신호→리스크→체결→알림→기록 파이프라인 검증(가짜 체결)
├── run_paper_trading.py   # KIS 모의투자 — 하루 1회 배치 모드 (GitHub Actions용)
├── run_realtime_trading.py  # KIS 모의투자 — 장중 실시간 모드 (VPS용, KIS 웹소켓)
├── run_hypothesis_sweep.py  # 등록된 전략 가설을 과거 데이터로 일괄 백테스트·비교
├── run_daily_review.py    # 매일 자동매매 직후, "다른 전략이었다면?" 비교 리포트를 텔레그램으로 발송
└── gdrive_sync.py         # GitHub Actions용 상태 DB 구글드라이브 업/다운로드

.github/workflows/
├── paper-trading.yml            # 평일 장마감 후 자동으로 run_paper_trading.py 실행
└── check-kis-connectivity.yml   # KIS 접속 가능 여부만 확인하는 진단용 (비밀값 불필요)
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
- **활성 전략**: `strategy/registry.py`에 등록된 전략 목록과 지금 실거래에
  쓰는 키를 보여주고, 화면에서 바로 다른 전략으로 전환할 수 있습니다
  (`scripts/configure.py strategy --active-key`와 동일한 동작).
- **매매 기록**: 청산까지 끝난 매매를 전략별로 보여줍니다(진입가·청산가·
  손익·진입/청산 사유) — `trades` 테이블을 그대로 읽습니다.
- **전략 리뷰 결과**: `scripts/run_daily_review.py`가 매일 쌓아 둔 "다른
  전략이었다면?" 비교 결과를 표로 보여줍니다.

비밀값(앱시크릿, 봇토큰 등)을 저장/조회하려면 `MUWON_MASTER_KEY`가 `.env`에
설정되어 있어야 합니다. 대시보드 하단 "보유 종목 & 최근 주문"에서 실제
매매 파이프라인(아래 참고)이 만든 포지션·주문을 5초마다 자동 갱신되는
표로 볼 수 있습니다.

### 폰/PC 어디서든 상시 접속 (Streamlit Community Cloud)

매번 `streamlit run`을 직접 실행하는 대신, 무료로 상시 호스팅되는 웹 주소
하나를 만들어 둘 수 있습니다. `GDRIVE_SA_KEY_JSON`/`GDRIVE_FOLDER_ID`가
설정되어 있으면 대시보드가 뜰 때·30초마다 구글드라이브에서 최신 `muwon.db`를
받아오고, 화면에서 설정을 바꾸면 즉시 다시 올립니다(`src/muwon/cloud/gdrive_sync.py`) —
GitHub Actions가 매일 만드는 매매 기록과 대시보드에서 바꾼 설정이 같은
구글드라이브 폴더를 통해 서로에게 반영됩니다. 배포 방법은
[`docs/deploy_streamlit_cloud.md`](docs/deploy_streamlit_cloud.md) 참고.

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
  있습니다 — 이 저장소를 개발한 로컬 환경은 실제로 막혀 있었지만,
  **GitHub Actions 러너에서는 모의투자 포트(29443) 접속이 확인됐습니다**
  (`check-kis-connectivity.yml` 참고).

두 경로 모두 같은 `TradingEngine`·`RiskManager`·`TelegramNotifier`를
쓰므로, KIS 접근이 열리면 데이터소스/실행기만 바꿔 끼우면 됩니다.

매수/매도가 체결되면 텔레그램으로 `🟢 매수 체결` / `🔴 매도 체결` 메시지가
갑니다(봇토큰 미설정 시엔 로그로만 남습니다). 리스크 매니저가 거부한
신호는 알림을 보내지 않고 실행 결과에만 남습니다.

## 매일 자동 실행 (GitHub Actions)

PC를 계속 켜둘 필요 없이, GitHub Actions가 평일 장마감 후 자동으로
`run_paper_trading.py`를 실행하도록 구성되어 있습니다
(`.github/workflows/paper-trading.yml`). GitHub Actions는 매번 새
가상머신이라 로컬 상태가 안 남기 때문에, 보유 종목·가상현금 상태(`muwon.db`)를
구글드라이브에 두고 실행마다 내려받고/올립니다.

설정 방법(구글 서비스 계정 만들기, GitHub Secrets 등록 등)은
[`docs/deploy_github_actions.md`](docs/deploy_github_actions.md)에
순서대로 정리되어 있습니다.

**PC 없이 폰/브라우저로 할 수 있는 것**: 저장소 Actions 탭 →
"KIS 모의투자 일일 자동매매" → Run workflow로 수동 실행할 수 있습니다.
이때 `trading_enabled` 입력값을 `true`/`false`로 지정하면 다른 리스크
설정은 그대로 두고 자동매매 킬스위치만 즉시 전환됩니다(`scripts/configure.py
kill-switch`) — 이상 징후가 보일 때 PC 앞이 아니어도 바로 멈출 수 있게 만든
용도입니다. 값을 "유지"로 두면 지금 저장된 설정 그대로 실행됩니다.

## 장중 실시간 매매 (VPS 또는 상시 켜진 PC)

하루 1회 배치 대신, 장중(09:00~15:30 KST) 체결이 들어올 때마다 반응하는
운영 모드도 있습니다. `src/muwon/execution/realtime_engine.py`의
`RealtimeTradingEngine`이 KIS 웹소켓으로 받은 틱을 분봉(기본 1분,
`src/muwon/data/tick_aggregator.py`)으로 묶고, 봉이 마감될 때마다 신호를
평가합니다 — 판단 로직(`Strategy`)과 리스크 검증(`RiskManager`)은 배치
모드와 완전히 동일하게 재사용하고, "언제 판단하느냐"만 다릅니다.

`src/muwon/execution/realtime_runner.py`가 웹소켓 연결이 끊기면 지수
백오프로 자동 재연결합니다 — 장중 몇 시간을 붙잡고 있어야 하는 연결이라
네트워크 순단은 예외가 아니라 전제로 설계했습니다. 재연결해도 봉 히스토리
(sma60 계산용 최근 60개 분량)는 메모리에 그대로 남아 있어 지표가 다시
채워질 때까지 기다릴 필요가 없습니다.

이건 장중 내내 떠 있어야 하는 상시 프로세스라 GitHub Actions로는 안 되고
**VPS 또는 계속 켜져 있는 PC가 필요합니다** — 두 운영 모드(배치/실시간)는
같은 계좌에 동시에 쓰는 게 아니라 둘 중 하나를 고르는 대안입니다.

```bash
pip install -e ".[realtime]"
python scripts/run_realtime_trading.py
```

KIS 웹소켓 연동은 이 저장소를 개발한 환경에서 실제 접속 검증을 못 했습니다
(KIS 포트 자체가 막혀 있음) — 공식 문서 기준으로 작성했으니 실제 배포 후
첫 실행에서 재검증이 필요합니다. 설정 방법:

- VPS(리눅스, systemd)에 배포 → [`docs/deploy_vps_realtime.md`](docs/deploy_vps_realtime.md)
- 집 윈도우 PC를 상시 서버로 활용 → [`docs/deploy_windows_pc.md`](docs/deploy_windows_pc.md)

## 전략 가설 검증 & 진화

"단타 가설을 세우고 → 과거 데이터로 검증하고 → 실전에 반영한다"를
코드 배포 없이 반복할 수 있도록 만든 구조입니다.

- **`src/muwon/strategy/registry.py`** — 전략을 파라미터 조합(`StrategyDefinition`)으로
  등록하는 곳. 같은 `MovingAverageRsiStrategy` 코드라도 이동평균 기간·RSI
  기간·거래량 급증 배수 같은 파라미터만 바꿔서 서로 다른 "가설"을 여러 개
  등록할 수 있습니다. 각 항목은 `status="live"`(실거래 중) 또는
  `"hypothesis"`(검증 중)로 표시됩니다.
- **`scripts/run_hypothesis_sweep.py`** — 등록된 가설 전체(또는 `--keys`로
  고른 일부)를 같은 기간·같은 종목 유니버스로 백테스트하고 수익률/MDD/승률/거래수를
  비교표로 출력합니다. 결과는 `backtest_runs` 테이블에 파라미터 스냅샷과
  함께 누적 저장되므로, 나중에 다시 돌려도 시간에 따른 비교가 가능합니다.

  ```bash
  python scripts/run_hypothesis_sweep.py --start 2023-01-01 --end 2024-12-31
  ```

- **`scripts/configure.py strategy`** — 가설이 마음에 들면 코드를 고치거나
  다시 배포할 필요 없이 설정값 하나로 실거래 전략을 바꿉니다. 이 변경도
  기존 설정 변경 이력에 자동으로 남습니다.

  ```bash
  python scripts/configure.py strategy --list                    # 등록된 가설 + 현재 활성 전략 확인
  python scripts/configure.py strategy --active-key ma_rsi_fast5_20  # 실거래 전략 교체
  ```

- **`scripts/run_daily_review.py`** — 매일 자동매매(GitHub Actions)가 끝날
  때마다 자동으로 붙는 리뷰 단계입니다(`.github/workflows/paper-trading.yml`에
  `run_paper_trading.py` 다음 스텝으로 추가돼 있음). 기준일(오늘)에서
  `--lookback-days`(기본 90일)만큼 거슬러 올라간 최근 구간을 등록된 전략
  전체로 다시 채점해서, "오늘 만약 다른 매수 전략이었다면 수익률이 더
  좋았을지 나빴을지"를 지금 실거래 중인 전략 대비 %p 차이로 텔레그램에
  보내줍니다. 결과는 `backtest_runs`에 `notes="daily_review"`로 쌓여서
  수동 스윕(`notes="manual_sweep"`) 기록과 구분되고, 매일 쌓이므로 어느
  전략이 꾸준히 앞서는지 시간에 따른 추세로도 볼 수 있습니다 — 사람이 손대지
  않아도 매일 "지금이 최선인가"를 다시 묻는 루프입니다.
- **매매 결과 학습 기반 (`TradeRow`)** — 실전/모의 매매에서 포지션이 청산될
  때마다 진입가·청산가·손익·진입 사유·청산 사유가 `strategy_key`와 함께
  `trades` 테이블에 기록됩니다(`src/muwon/execution/state_repository.py`의
  `record_trade`). 지금은 이 데이터를 사람이 조회하는 용도지만, 어떤 전략이
  어떤 조건에서 이기고 지는지가 이미 구조화되어 쌓이고 있어서, 향후 AI가
  이 로그를 읽고 전략 파라미터 수정이나 새 가설을 제안하는 단계로 자연스럽게
  이어질 수 있도록 설계했습니다(아직 AI 연동 자체는 구현 전 — 데이터 기반만
  마련된 상태).

## 로드맵

1. **Phase 0**: 저장소 구조, 리스크 매니저 기본 로직, KIS API 신청 가이드
2. **Phase 1**: 데이터 수집 파이프라인 + 규칙기반 전략 + 백테스트 엔진
3. **Phase 2** (진행 중): 매매 파이프라인(신호→리스크→체결→알림→기록) +
   설정 대시보드 + 배치(GitHub Actions)/실시간(VPS 웹소켓) 두 실행 모드 —
   KIS 모의투자 계좌로 실제 체결 확인이 다음 단계
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
