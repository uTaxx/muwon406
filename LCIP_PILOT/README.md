# LCIP Pilot — LX Corporate Intelligence Platform (Pilot)

LX홀딩스 전략팀 관점의 **공개정보 기반** 개인용 Corporate Intelligence Pilot.
첫 작동 주제: **엔지니어드스톤·실리코시스 리스크 모니터링** (`TOP-0001`).

> 상세 배경·제약조건·설계 원칙은 `CLAUDE.md`와 `docs/`를 참고할 것. 이 README는 실행 순서
> 요약본이다.

## 미션

1. **미래준비** — 산업·정책·기술·자본시장 변화 탐지, M&A/Carve-out/Bolt-on/Venture 기회 탐색
2. **리스크 관리** — 소송·제품책임·산업안전·환경·통상·공급망 리스크 조기 감지

## 기술 스택

Google Drive · Google Sheets · n8n Cloud Starter · Claude API · 정적 HTML/CSS/JS 대시보드 ·
Gmail · Telegram

## 비용 상한

- 개인 월 총비용(기존 구독 포함): **10만원 이하**
- Claude API 월 목표 **$15** / 절대 상한 **$20**

## 로컬 실행 순서

```bash
cd LCIP_PILOT
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 실제 값은 여기에만 채운다. 절대 커밋하지 않는다.

# 1. 프로젝트 구조/기본 파일 검증 (dry-run, 외부 호출 없음)
python scripts/bootstrap_project.py --dry-run

# 2. 설정 파일(config/*.yaml) 검증
python scripts/validate_config.py

# 3. Secret 평문 저장 여부 검사
python scripts/secret_scan.py

# 4. 단위 테스트
pytest tests/
```

## 외부 연결 (사용자 명시적 승인 후에만 --apply)

```bash
# Google Drive 폴더 구조 — 기본 dry-run, 실제 생성은 --apply 및 사용자 승인 필요
python scripts/create_drive_structure.py --dry-run

# Google Sheets 탭 구조 — 기본 dry-run
python scripts/create_google_sheets.py --dry-run

# n8n 워크플로우 배포 — 기본 dry-run, 배포해도 active:false 유지
python scripts/n8n_deploy.py --dry-run
```

## 디렉터리 구조

```
LCIP_PILOT/
├─ docs/        설계 문서 (Blueprint, Build Spec, Schema, Acceptance Tests, ADR)
├─ config/      운영 설정 (topics, sources, cost_policy, notification 등)
├─ schemas/     JSON Schema (article, intelligence, source_health, ...)
├─ knowledge/   LX 공개정보 Knowledge Base (템플릿, 임의 사실 없음)
├─ prompts/     Claude API 프롬프트 (버전관리 대상)
├─ dashboard/   정적 HTML 대시보드 템플릿
├─ scripts/     로컬 Python 도구 (bootstrap, validate, dry-run 커넥터 등)
├─ n8n/         n8n 워크플로우 JSON (import 가능, 기본 inactive)
├─ tests/       pytest 단위/통합 테스트
├─ output/ logs/ archive/   런타임 산출물 (gitignore 대상)
```

## 현재 진행 상태

`PROJECT_STATUS.md`와 `TODO.md`를 참고. 이번 라운드는 **TASK-001~007**(로컬 scaffold, config,
schema, knowledge 템플릿, Drive/Sheets/n8n dry-run 도구)까지만 구현되어 있으며, 실제 외부
계정 연결(TASK-008 이후)은 아직 수행되지 않았다.
