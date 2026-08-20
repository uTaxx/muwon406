"""텔레그램에서 온 명령을 읽어 **기준을 고친다.**

폰에서 `/설정 max_position_weight 12` 라고 보내면 구글 시트의 그 줄이
바뀌고, 다음 실행부터 그 값으로 돈다.

## 서버 없이 어떻게 받나

웹훅을 걸지 않는다 — 받으려면 상시 도는 서버가 필요한데 이 저장소에는
그런 게 없다. 대신 워크플로가 주기적으로 `getUpdates`로 **물어보러 간다.**
늦어야 몇 분이고, 설정을 바꾸는 일에 몇 분은 늦어도 된다.

## 같은 명령을 두 번 실행하지 않는다

텔레그램은 "여기까지 읽었다"(offset)를 우리가 알려 줄 때까지 같은 메시지를
계속 준다. 그 표시를 DB에 남긴다. 안 남기면 **워크플로가 돌 때마다 어제
명령이 다시 실행된다.**

## 안전 규칙

- 저장된 chat_id에서 온 것만 듣는다 (봇 이름은 누구나 알 수 있다)
- **매매를 켜는 것은 여기서 못 한다.** 끄는 것만 된다
- 값 검증은 시트에서 읽을 때와 같은 규칙을 쓴다
- 모르는 말에는 안내만 한다 — 추측해서 실행하지 않는다

사용 예:
    python scripts/telegram_control.py
    python scripts/telegram_control.py --dry-run   # 읽기만, 아무것도 안 고침
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import requests

from muwon.cloud.approval import approve_in_sheet
from muwon.cloud.sector_sheet import DEFAULT_TITLE, find_or_create, read, update_setting
from muwon.config import bootstrap_settings
from muwon.db.session import ensure_schema
from muwon.notify.telegram import TelegramNotifier
from muwon.notify.telegram_control import parse_command, 도움말, 바꾼말
from muwon.settings.from_sheet import apply, describe, parse_settings, 기준표
from muwon.settings.service import build_settings_service

KST = ZoneInfo("Asia/Seoul")
API = "https://api.telegram.org/bot{token}/{method}"
#: 한 번에 몇 개까지 처리할 것인가. 밀려 있어도 한꺼번에 다 실행하면
#: 무슨 일이 일어났는지 따라갈 수가 없다.
MAX_PER_RUN = 20


def _받기(token: str, offset: int) -> list[dict]:
    r = requests.get(
        API.format(token=token, method="getUpdates"),
        params={"offset": offset, "timeout": 0, "allowed_updates": '["message"]'},
        timeout=30,
    )
    r.raise_for_status()
    몸통 = r.json()
    if not 몸통.get("ok"):
        raise RuntimeError(f"텔레그램이 거절했습니다: {몸통}")
    return 몸통.get("result", [])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet-id", default=os.environ.get("MUWON_SHEET_ID", ""))
    parser.add_argument("--folder-id", default=os.environ.get("GDRIVE_FOLDER_ID", ""))
    parser.add_argument("--dry-run", action="store_true", help="읽기만 하고 아무것도 안 고친다")
    args = parser.parse_args()

    ensure_schema(bootstrap_settings.database_url)
    service = build_settings_service()
    cfg = service.get_telegram_config()
    if not cfg.bot_token:
        print("텔레그램 봇 토큰이 없습니다 — 할 일이 없습니다.", file=sys.stderr)
        return 0
    if not cfg.chat_id:
        print("chat_id가 없습니다. **누구 말을 들을지 모르면 아무 말도 듣지 않습니다.**",
              file=sys.stderr)
        return 0

    sheet_id = args.sheet_id
    if not sheet_id:
        if not args.folder_id:
            raise SystemExit("MUWON_SHEET_ID도 GDRIVE_FOLDER_ID도 없습니다.")
        sheet_id, _ = find_or_create(args.folder_id, DEFAULT_TITLE)

    보내기 = TelegramNotifier(service).send
    offset = service.get_telegram_offset()
    업데이트 = _받기(cfg.bot_token, offset)
    print(f"■ 새 메시지 {len(업데이트)}개 (offset {offset})")

    처리수, 마지막 = 0, offset
    for u in 업데이트[:MAX_PER_RUN]:
        마지막 = max(마지막, int(u["update_id"]) + 1)
        메시지 = u.get("message") or {}
        보낸이 = str((메시지.get("chat") or {}).get("id", ""))
        글 = (메시지.get("text") or "").strip()
        if not 글:
            continue

        # **정해 둔 사람만.** 봇 이름은 누구나 알 수 있다.
        if 보낸이 != str(cfg.chat_id):
            print(f"  모르는 chat_id({보낸이})에서 온 말은 버립니다: {글[:40]!r}")
            continue

        print(f"  받음: {글!r}")
        처리수 += 1
        if args.dry_run:
            print(f"    → {parse_command(글).종류} (--dry-run이라 실행 안 함)")
            continue
        try:
            보내기(_처리(글, sheet_id, service))
        except Exception as e:  # noqa: BLE001 — 한 명령이 터져도 나머지는 처리한다
            print(f"    터짐: {type(e).__name__}: {e}", file=sys.stderr)
            보내기(f"⚠️ 그 명령을 처리하다 문제가 생겼습니다.\n{type(e).__name__}: {e}")

    if not args.dry_run and 마지막 != offset:
        # **여기까지 읽었다고 남긴다.** 안 남기면 다음 실행에서 또 실행된다.
        service.set_telegram_offset(마지막)
    print(f"■ 처리 {처리수}건 · 다음 offset {마지막}")
    return 0


def _처리(글: str, sheet_id: str, service) -> str:
    c = parse_command(글)

    if c.종류 == "도움":
        return 도움말()

    if c.종류 == "모름":
        return f"❓ {c.말}"

    if c.종류 == "켜기":
        return (
            "🔒 **매매를 켜는 것은 텔레그램에서 안 됩니다.**\n\n"
            "구글 시트 `설정` 탭의 `trading_enabled`을 true로 바꾸거나 대시보드에서 켜세요.\n"
            "화면을 보면서 켜야 하는 일이라 일부러 막아 뒀습니다.\n\n"
            "끄는 것은 /끄기 로 언제든 됩니다."
        )

    if c.종류 == "끄기":
        옛것 = update_setting(sheet_id, "trading_enabled", "false")
        return (
            f"🛑 **매매를 껐습니다.** (시트 값 {옛것 or '(빈칸)'} → false)\n\n"
            "이미 들고 있는 종목의 손절은 그대로 작동합니다 — '더 안 산다'이지 "
            "'방치한다'가 아닙니다."
        )

    if c.종류 == "상태":
        내용 = read(sheet_id)
        시트 = parse_settings(내용.설정)
        정책, 출처 = apply(service.get_risk_policy(), 시트)
        섹터수 = sum(1 for s in 내용.섹터 if s.활성)
        종목수 = sum(len(s.활성종목) for s in 내용.섹터 if s.활성)
        return (
            describe(정책, 출처, 시트)
            + f"\n\n  유니버스: 섹터 {섹터수}개 · 종목 {종목수}개"
            + "\n\n바꾸려면: /설정 <이름> <값>"
        )

    if c.종류 == "설정":
        b = 기준표[c.이름]
        옛글자 = update_setting(sheet_id, c.이름, c.글자)
        옛것 = _옛값(b, 옛글자)
        return 바꾼말(c.이름, 옛것, c.값)

    if c.종류 == "승인":
        오늘 = datetime.now(KST).date()
        찾음, 못찾음 = approve_in_sheet(sheet_id, 오늘, c.종목들)
        줄 = []
        if 찾음:
            줄.append(f"✅ 승인 {len(찾음)}종목: {', '.join(찾음)}")
        if 못찾음:
            줄.append(
                f"❓ 오늘 후보에 없어서 못 한 것: {', '.join(못찾음)}\n"
                "   승인은 제안된 것 중에 고르는 일이라, 목록에 없는 종목은 사지 않습니다."
            )
        return "\n\n".join(줄) or "오늘 후보가 없습니다."

    return f"❓ 아직 처리하지 못하는 명령입니다: {c.종류}"


def _옛값(b, 글자: str):
    """바뀌기 전 값. 시트가 비어 있었으면 기본값을 보여 준다."""
    from muwon.settings.from_sheet import SettingsError, 기본값, 해석값

    if not 글자:
        return 기본값(b)
    try:
        return 해석값(b, 글자)
    except SettingsError:
        return 글자


if __name__ == "__main__":
    raise SystemExit(main())
