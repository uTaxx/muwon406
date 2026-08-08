#!/usr/bin/env python3
"""LCIP Pilot — Google OAuth 최초 1회 승인용 로컬 실행 스크립트.

Claude Code는 브라우저/localhost가 없는 원격 샌드박스에서 실행되기 때문에
`google_auth.py`의 OAuth Desktop 흐름(InstalledAppFlow.run_local_server)을
그 환경에서 직접 실행할 수 없다. 이 스크립트는 사용자의 로컬 PC에서 실행해
브라우저 승인을 1회 완료하고, 그 결과(token.json)를 만들기 위한 것이다.

이 저장소(LCIP_PILOT)에 의존하지 않는 독립 실행 파일이다 — 로컬 PC에 이
저장소가 없어도 이 파일 하나만 다운로드해 실행할 수 있다.

사용법:
    pip install google-auth google-auth-oauthlib
    export GOOGLE_OAUTH_CLIENT_ID=...      # .env의 값과 동일하게 입력(직접 입력해도 됨)
    export GOOGLE_OAUTH_CLIENT_SECRET=...
    python3 local_oauth_setup.py

브라우저가 열리고 Google 계정 승인을 마치면, 이 스크립트가 있는 위치에
`token.json`이 생성된다. 그 파일 "내용 전체"를 Claude에게 붙여넣어 주면
`credentials/token.json`에 저장하고 이후 Drive/Sheets 실제 연동에 사용한다.

Client ID/Secret은 코드에 하드코딩하지 않는다(CLAUDE.md 절대 원칙 #7) —
환경변수로 없으면 실행 시 직접 입력받는다.
"""
from __future__ import annotations

import os
import sys

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]


def main() -> int:
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print(
            "필요한 패키지가 없다. 먼저 실행: pip install google-auth google-auth-oauthlib",
            file=sys.stderr,
        )
        return 1

    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID") or input("GOOGLE_OAUTH_CLIENT_ID: ").strip()
    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET") or input(
        "GOOGLE_OAUTH_CLIENT_SECRET: "
    ).strip()

    if not client_id or not client_secret:
        print("Client ID/Secret이 필요하다.", file=sys.stderr)
        return 1

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0)

    out_path = "token.json"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(creds.to_json())

    print(f"\n완료 — {out_path} 생성됨.")
    print("이 파일의 전체 내용을 복사해 Claude에게 붙여넣어 주세요.")
    print("(이 파일 자체를 다른 곳에 커밋하거나 공유하지 마세요 — Google 계정 접근 토큰입니다.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
