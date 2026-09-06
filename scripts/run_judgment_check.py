"""판단 지침을 전략과 같은 방식으로 검증한다.

    python scripts/run_judgment_check.py
    python scripts/run_judgment_check.py --상한 5 --돌아볼구간 12

**주문은 나가지 않습니다.** 과거 시세로 계산만 하고 상태 DB도 시트도
고치지 않습니다. 여기 1위로 나온 지침이 저절로 걸리지도 않습니다.

지침을 바꾸면 저녁 검토가 내는 후보가 바뀌고 그 후보가 텔레그램 버튼으로
나갑니다. 실제 주문에 영향을 주는 결정이라 사람이 정합니다.
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from muwon.analysis import judgment_check as 검증
from muwon.analysis.market_data import load_histories
from muwon.data.price_cache import PriceCache
from muwon.data.universe import UNIVERSE, Ticker
from muwon.data.yahoo_client import YahooFinanceDataSource
from muwon.sector.catalog import CATALOG
from muwon.settings.schema import RiskPolicy
from muwon.strategy.registry import build_strategy, get_definition, list_definitions

서울 = ZoneInfo("Asia/Seoul")


def 매매대상() -> list[Ticker]:
    아는것 = {ㅌ.symbol: ㅌ for ㅌ in UNIVERSE}
    본것: dict[str, Ticker] = {}
    for 섹터 in CATALOG:
        for 종목 in 섹터.활성종목:
            if 종목.symbol in 본것:
                continue
            본것[종목.symbol] = 아는것.get(종목.symbol) or Ticker(
                종목.symbol, 종목.name, 종목.market,
                f"{종목.symbol}.{'KQ' if 종목.market == 'KOSDAQ' else 'KS'}")
    return list(본것.values())


def 이름(키: str) -> str:
    try:
        return get_definition(키).화면이름
    except Exception:  # noqa: BLE001
        return 키


def 인자들():
    ㄱ = argparse.ArgumentParser(description=__doc__)
    ㄱ.add_argument("--시작", default="2021-01-04")
    ㄱ.add_argument("--상한", type=int, default=5, help="보유 상한이자 구간 길이")
    ㄱ.add_argument("--돌아볼구간", type=int, default=검증.돌아볼구간)
    ㄱ.add_argument("--섹터당", type=int, default=3)
    ㄱ.add_argument("--동시보유", type=int, default=6)
    ㄱ.add_argument("--지금전략", default="volume_surge_3d_us60_2")
    return ㄱ.parse_args()


def main() -> int:
    인자 = 인자들()
    시작 = datetime.fromisoformat(인자.시작).date()
    끝 = datetime.now(tz=서울).date()
    종목들 = 매매대상()

    print(f"■ 판단 지침 검증 · {len(종목들)}종목 · 구간 {인자.상한}영업일 · "
          f"{시작} ~ {끝}")
    print(f"  판정할 때 앞의 {인자.돌아볼구간}구간만 봅니다. 미래는 안 봅니다.")

    histories = load_histories(
        YahooFinanceDataSource(), 종목들,
        시작 - timedelta(days=420), 끝, cache=PriceCache())
    if not histories:
        print("  시세를 하나도 못 받았습니다.")
        return 1

    정책 = RiskPolicy(max_holding_days=인자.상한,
                    max_concurrent_positions=인자.동시보유)
    전략들 = {ㄷ.key: (lambda k=ㄷ.key: build_strategy(k))
            for ㄷ in list_definitions()}
    섹터표 = {종목.symbol: 섹터.코드
           for 섹터 in CATALOG for 종목 in 섹터.활성종목}

    곡선들, 거래수, 진입일들 = 검증.전략곡선들(
        histories, 전략들, 정책, 시작, 섹터표=섹터표, 섹터상한=인자.섹터당)
    print(f"  전략 {len(곡선들)}개 (거래 0건 제외)")

    구간표 = 검증.구간표만들기(곡선들, 인자.상한, 진입일들)
    칸수 = min(len(v) for v in 구간표.values()) if 구간표 else 0
    판정수 = max(0, 칸수 - 인자.돌아볼구간)
    print(f"  구간 {칸수}개 · 판정 {판정수}번")
    print(f"  앞 {인자.돌아볼구간}구간에 {검증.최소매매}건도 안 산 전략은 "
          "후보에서 뺍니다.\n")
    if 판정수 < 10:
        print("  판정이 너무 적어 견줄 수 없습니다.")
        return 1

    성적들 = 검증.모두재기(구간표, 인자.돌아볼구간)
    print("■ 지침마다 고른 전략이 그다음 구간에서 낸 성적")
    print("  가장 나빴던 판정을 먼저 봅니다.\n")
    머리 = (f"  {'':>2} {'지침':22} {'최악':>7} {'중앙값':>7} "
          f"{'플러스':>7} {'바꾼 비율':>9}")
    print(머리)
    for 자리, ㅅ in enumerate(성적들, 1):
        붙임 = ㅅ.이름[:18]
        print(f"  {자리:>2} {붙임}{' ' * max(0, 20 - len(붙임) * 2)}"
              f" {ㅅ.최악:>7.1f} {ㅅ.중앙값:>7.2f} {ㅅ.플러스비율:>6.1f}%"
              f" {ㅅ.바꾼비율:>8.1f}%"
              + (f"  (판정 {ㅅ.판정수}번, 후보 없어 못 한 것 {ㅅ.못한판정}번)"
                 if ㅅ.못한판정 else f"  (판정 {ㅅ.판정수}번)"))

    print("\n■ 대조군")
    print("  지침이 이것을 못 이기면 아무것도 더하지 않은 것입니다.\n")
    대조들 = [ㄷ for ㄷ in (
        검증.무작위대조군(구간표, 인자.돌아볼구간),
        검증.전체평균대조군(구간표, 인자.돌아볼구간),
        검증.안바꾼대조군(구간표, 인자.지금전략, 인자.돌아볼구간),
    ) if ㄷ]
    for ㄷ in 대조들:
        붙임 = ㄷ.이름[:30]
        print(f"     {붙임:34} {ㄷ.최악:>7.1f} {ㄷ.중앙값:>7.2f} "
              f"{ㄷ.플러스비율:>6.1f}%")

    무작위 = next((ㄷ for ㄷ in 대조들 if ㄷ.이름.startswith("무작위")), None)
    if 무작위 and 성적들:
        이긴것 = [ㅅ for ㅅ in 성적들 if ㅅ.중앙값 > 무작위.중앙값]
        print(f"\n  무작위보다 중앙값이 높은 지침 {len(이긴것)}개 / {len(성적들)}개")
        진것 = [ㅅ.이름 for ㅅ in 성적들 if ㅅ.중앙값 <= 무작위.중앙값]
        if 진것:
            print(f"  못 이긴 것: {', '.join(진것)}")

    if 성적들:
        으뜸 = 성적들[0]
        고른것 = {}
        for ㅍ in 으뜸.판정들:
            고른것[ㅍ.고른키] = 고른것.get(ㅍ.고른키, 0) + 1
        print(f"\n■ 1위 지침({으뜸.이름})이 실제로 고른 전략")
        for ㅋ, 수 in sorted(고른것.items(), key=lambda ㄱ: -ㄱ[1])[:8]:
            print(f"     {이름(ㅋ)[:24]:26} {수:>3}번"
                  f" (거래 {거래수.get(ㅋ, 0)})")

    print("\n  이 결과로 지침이 바뀌지 않습니다. 바꾸는 것은 사람이 정합니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
