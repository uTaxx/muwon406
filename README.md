# muwon406 — 코스피/코스닥 자동매매 시스템

한국투자증권(KIS) API 기반, 규칙기반 전략에서 시작해 ML 신호로 고도화하는
자동매매 시스템. 백테스트 → 모의투자 → 소액 실거래 순으로 검증하며 진행합니다.

## 구조

```
src/muwon/
├── config.py       # 환경설정 (.env 로드), 리스크 파라미터 포함
├── domain/         # 공통 타입/인터페이스 (Strategy, MarketDataSource, OrderExecutor)
├── data/           # KIS API 클라이언트 — 시세 수집
├── strategy/       # 규칙기반 → ML 전략 (Phase 1~3)
├── risk/           # 리스크 매니저 — 주문 실행 전 최종 검증
├── execution/       # 주문 실행기 (모의/실전 전환, Phase 2)
├── backtest/       # 백테스트 엔진 (Phase 1)
├── notify/         # 텔레그램 알림
└── db/             # 시세/신호/주문 저장 (SQLite → 운영 시 Postgres 전환 가능)
```

## 로드맵

1. **Phase 0** (현재): 저장소 구조, 리스크 매니저 기본 로직, KIS API 신청 가이드
2. **Phase 1**: 데이터 수집 파이프라인 + 규칙기반 전략 + 백테스트 엔진
3. **Phase 2**: 모의투자 연동 + 텔레그램 알림 + 리스크 매니저 통합
4. **Phase 3**: ML 신호 고도화
5. **Phase 4**: 소액 실거래 전환

## 시작하기

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env  # KIS 앱키 등 채워넣기 (docs/kis_api_setup.md 참고)

pytest
```

## KIS API 신청

아직 앱키를 발급받지 않았다면 [`docs/kis_api_setup.md`](docs/kis_api_setup.md)를
따라 진행하세요.

## 리스크 정책

기본 리스크 규칙은 [`docs/risk_policy.md`](docs/risk_policy.md)에 정리되어
있습니다.
