"""섹터·종목·설정을 구글 시트로 올리고, 시트에서 다시 읽어 검증한다.

대시보드를 걷어내고 **시트를 화면으로 쓰기로 했다**
(`docs/설계_스트림릿을_걷어낼까.md`). 이 스크립트가 그 첫 단계다.

## 두 가지 일만 한다

    --push      코드에 있는 초안을 시트에 **덮어쓴다** (첫 채움 전용)
    (기본)      시트를 읽어 검증하고 무엇이 들었는지 보여 준다

**--push는 시트 내용을 통째로 지운다.** 그래서 처음 한 번만 쓴다.
그 뒤로는 사람이 시트에서 고치고, 코드는 읽기만 한다.

## 왜 읽자마자 검증하나

반쯤 잘못된 목록으로 실거래를 도는 것이 최악이다. 종목코드 한 자리가
틀리면 엉뚱한 회사를 사고, 그건 주문이 나간 뒤에야 드러난다.

사용 예:
    python scripts/sync_sector_sheet.py --push     # 처음 한 번
    python scripts/sync_sector_sheet.py            # 읽고 검증
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from muwon.cloud.sector_sheet import (
    DEFAULT_TITLE,
    SheetError,
    catalog_rows,
    default_settings_rows,
    find_or_create,
    read,
    write_all,
)
from muwon.settings.from_sheet import SettingsError, apply, describe, parse_settings
from muwon.settings.schema import RiskPolicy


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--push", action="store_true", help="코드의 초안을 시트에 덮어쓴다 (첫 채움 전용)")
    parser.add_argument("--add-missing-settings", action="store_true",
                        help="설정 탭에 빠진 기준 줄만 채운다 (있는 값은 안 건드림)")
    parser.add_argument("--title", default=DEFAULT_TITLE)
    parser.add_argument("--folder-id", default=os.environ.get("GDRIVE_FOLDER_ID", ""))
    args = parser.parse_args()

    if not args.folder_id:
        raise SystemExit("GDRIVE_FOLDER_ID가 없습니다 (환경변수 또는 --folder-id).")

    sheet_id, 새로만듦 = find_or_create(args.folder_id, args.title)
    주소 = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
    print(f"시트: {주소}{'  (새로 만듦)' if 새로만듦 else ''}")

    if args.push:
        섹터행, 종목행 = catalog_rows()
        write_all(sheet_id, 섹터행, 종목행, default_settings_rows())
        print(f"올렸습니다 — 섹터 {len(섹터행) - 1}줄 · 종목 {len(종목행) - 1}줄 · 설정 {len(default_settings_rows()) - 1}줄")
        print("\n**이제부터는 시트에서 고치세요.** --push는 시트를 통째로 덮어씁니다.")

    # 기준을 새로 만들면 시트에는 그 줄이 없다. 없어도 기본값으로 돌지만,
    # **시트에 안 보이면 고칠 수가 없다.** 있는 값은 건드리지 않고 빠진
    # 줄만 채운다 — --push와 달리 사람이 고쳐 둔 값을 지우지 않는다.
    if args.add_missing_settings:
        from muwon.cloud.sector_sheet import append_settings
        from muwon.settings.from_sheet import 기준들

        있는것 = set(read(sheet_id).설정)
        빠진것 = [b for b in 기준들 if b.이름 not in 있는것]
        append_settings(sheet_id, [[b.이름, b.기본, b.설명] for b in 빠진것])
        print(f"\n빠져 있던 기준 {len(빠진것)}개를 채웠습니다"
              + (f": {', '.join(b.이름 for b in 빠진것)}" if 빠진것 else " (없음)"))

    try:
        내용 = read(sheet_id)
    except SheetError as e:
        print(f"\n❌ 시트를 매매에 쓸 수 없습니다\n   {e}", file=sys.stderr)
        print("\n고치기 전까지는 이 목록으로 아무것도 사지 않습니다.", file=sys.stderr)
        return 1

    print(f"\n■ 검증 통과 — 섹터 {len(내용.섹터)}개")
    print(f"  {'섹터':<8}{'이름':<16}{'활성':>5}{'상한':>7}{'전망출처':>10}{'종목':>6}{'활성종목':>8}")
    for s in 내용.섹터:
        print(
            f"  {s.코드:<8}{s.이름:<16}{'Y' if s.활성 else 'N':>5}"
            f"{s.비중상한:>6.0f}%{s.전망출처:>10}{len(s.종목):>6}{len(s.활성종목):>8}"
        )

    꺼진것 = [(s.코드, m) for s in 내용.섹터 for m in s.종목 if not m.활성]
    if 꺼진것:
        print(f"\n  꺼 둔 종목 {len(꺼진것)}개 — 지우지 않고 두는 이유는 '왜 뺐는지'를 남기기 위해서입니다")
        for 코드, m in 꺼진것:
            print(f"    {코드}/{m.symbol} {m.name}: {m.메모 or '(이유 없음)'}")

    print(f"\n■ 설정 {len(내용.설정)}개 — 시트에 적힌 그대로")
    for 이름, 값 in 내용.설정.items():
        print(f"  {이름:<28}{값}")

    # 적힌 것과 **실제로 걸리는 것**은 다르다. 단위가 바뀌고(15 → 0.15),
    # 시트에 없는 항목은 DB 값이 살고, 모르는 이름은 아무 효과가 없다.
    # 그 차이를 여기서 보여 주지 않으면 사람은 적은 대로 믿는다.
    try:
        시트설정값 = parse_settings(내용.설정)
    except SettingsError as e:
        print(f"\n❌ 설정 값을 매매에 쓸 수 없습니다\n   {e}", file=sys.stderr)
        print("\n고치기 전까지는 매매를 켜지 않습니다.", file=sys.stderr)
        return 1

    정책, 출처 = apply(RiskPolicy(), 시트설정값)
    print()
    print(describe(정책, 출처, 시트설정값))
    print("\n  ※ [DB]로 표시된 항목은 시트에 없어 저장된 값을 씁니다.")
    if 시트설정값.모르는이름:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
