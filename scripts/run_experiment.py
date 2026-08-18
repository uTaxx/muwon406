"""전략 실험 실행기 — 가설을 손으로 스크립트 짜지 않고 돌려 본다.

시세는 한 번만 받아 모든 변형이 공유한다. 그래서 변형을 여러 개 돌려도
데이터 수집 시간은 한 번뿐이고, 무엇보다 **모든 변형이 정확히 같은 데이터를
본다** — 이게 어긋나면 비교 자체가 성립하지 않는다.

사용 예:
    # Factor를 하나씩 꺼 보고 기여도 측정 (인수인계서 28항)
    python scripts/run_experiment.py contribution --from-year 2021 --to-year 2025

    # 한 Factor의 가중치만 바꿔 가며
    python scripts/run_experiment.py sweep --factor relative_strength --weights 0,10,20,40

    # 등록된 전략들을 같은 조건에서 비교
    python scripts/run_experiment.py strategies --keys volume_surge_5d,factor_score_v1
"""

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from muwon.analysis.experiment import (
    WARMUP_DAYS,
    blend_sleeves,
    correlation_matrix,
    daily_returns_by_strategy,
    factor_contribution,
    format_comparison,
    format_correlation,
    param_sweep,
    run_experiment,
    run_header,
    sleeve_curves,
    slice_for_year,
    slippage_sweep,
    take_profit_sweep,
    weight_sweep,
)
from muwon.analysis.holding_path import format_paths, trace
from muwon.analysis.market_data import load_histories
from muwon.backtest.engine import BacktestEngine
from muwon.config import bootstrap_settings
from muwon.data.price_cache import PriceCache
from muwon.data.universe import UNIVERSE
from muwon.data.universe_builder import KIND_MARKET_CAP, active_universe
from muwon.data.yahoo_client import YahooFinanceDataSource
from muwon.db.session import make_session_factory
from muwon.risk.manager import RiskManager
from muwon.scoring.config import StrategyConfig
from muwon.settings.schema import RiskPolicy
from muwon.strategy.registry import build_strategy


def load_universe_histories(
    years: list[int], kind: str = KIND_MARKET_CAP, use_cache: bool = True
):
    session_factory = make_session_factory(bootstrap_settings.database_url)
    universe = active_universe(session_factory, list(UNIVERSE), kind=kind)
    return load_histories(
        YahooFinanceDataSource(),
        universe,
        date(min(years), 1, 1) - timedelta(days=WARMUP_DAYS),
        date(max(years), 12, 31),
        cache=PriceCache() if use_cache else None,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="전략 실험 실행기")
    parser.add_argument(
        "mode",
        choices=[
            "contribution",
            "sweep",
            "param",
            "strategies",
            "correlation",
            "blend",
            "slippage",
            "takeprofit",
            "holding",
        ],
    )
    parser.add_argument(
        "--universe",
        choices=["market_cap", "volume"],
        default="market_cap",
        help="어느 유니버스로 돌릴지. volume은 거래대금 상위(update_universe.py --kind volume)",
    )
    parser.add_argument(
        "--out",
        default="",
        help="결과를 남길 파일 경로. 로그는 만료되므로 나중에 비교하려면 필요하다.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="시세 캐시를 쓰지 않고 매번 새로 받는다",
    )
    parser.add_argument("--from-year", type=int, default=2021)
    parser.add_argument("--to-year", type=int, default=2025)
    parser.add_argument("--factor", default="relative_strength", help="sweep/param 대상 Factor")
    parser.add_argument("--weights", default="0,10,20,30,40", help="sweep에 쓸 가중치들")
    parser.add_argument("--keys", default="", help="strategies 모드에서 비교할 전략 키")
    parser.add_argument("--param", default="uptrend_ma", help="param 모드에서 바꿀 파라미터")
    parser.add_argument("--values", default="0,120,200", help="param 모드에서 쓸 값들")
    parser.add_argument(
        "--base-params", default="", help="param 모드에서 함께 고정할 파라미터 (JSON)"
    )
    args = parser.parse_args()

    years = list(range(args.from_year, args.to_year + 1))
    histories = load_universe_histories(years, args.universe, use_cache=not args.no_cache)
    config = StrategyConfig()

    written: list[str] = []

    def emit(text: str) -> None:
        """화면과 파일에 같은 내용을 남긴다."""
        print(text)
        written.append(text)

    def save(extra: dict | None = None) -> None:
        if not args.out:
            return
        header = run_header(args.mode, args.universe, sorted(histories), years, extra)
        # 표는 자리를 맞춘 고정폭 텍스트라 코드 블록으로 감싸야 안 깨진다
        body = "```\n" + "\n".join(written) + "\n```\n"
        Path(args.out).write_text(header + body, encoding="utf-8")
        print(f"\n결과를 {args.out}에 남겼습니다.", file=sys.stderr)

    if args.mode == "contribution":
        emit("■ Factor 기여도 — 하나씩 껐을 때 성과가 어떻게 변하는가")
        emit("  껐는데 성과가 그대로면 그 Factor는 가중치만 차지하고 있는 것이고,")
        emit("  껐더니 좋아지면 해를 끼치고 있는 것이다.\n")
        results = factor_contribution(config, histories, years)

    elif args.mode == "sweep":
        weights = [float(w) for w in args.weights.split(",")]
        emit(f"■ 가중치 스윕 — {args.factor}의 비중만 바꾼다\n")
        results = weight_sweep(config, args.factor, weights, histories, years)

    elif args.mode == "param":
        values = [int(v) for v in args.values.split(",")]
        emit(f"■ 파라미터 스윕 — {args.factor}.{args.param}만 바꾼다\n")
        base = json.loads(args.base_params) if args.base_params else {}
        results = param_sweep(
            config, args.factor, args.param, values, histories, years, base_params=base
        )

    elif args.mode == "slippage":
        keys = [k.strip() for k in args.keys.split(",") if k.strip()]
        if not keys:
            raise SystemExit("--keys에 전략을 지정하세요")
        rates = [float(v) / 100 for v in args.values.split(",")]
        emit("■ 슬리피지 민감도 — 종가에 체결됐다는 가정을 얼마나 믿을 수 있는가")
        emit("  회전율이 높은 전략일수록 이 가정이 결과를 부풀린다.")
        emit("  0.1%에서 결론이 뒤집히면 그 결론은 원래 없던 것이다.\n")
        results = []
        for key in keys:
            results.extend(
                slippage_sweep(
                    key, (lambda k=key: build_strategy(k)), rates, histories, years
                )
            )
        emit(format_comparison(results, years))
        save({"슬리피지(%)": args.values})
        return

    elif args.mode == "takeprofit":
        keys = [k.strip() for k in args.keys.split(",") if k.strip()]
        if not keys:
            raise SystemExit("--keys에 전략을 지정하세요")
        levels = [float(v) / 100 for v in args.values.split(",")]
        emit("■ 익절선 민감도 — 목표 수익률에서 파는 것이 나은가")
        emit("  지금은 익절이 아예 없다. 오르는 중이면 손절이나 보유 기간에")
        emit("  걸릴 때까지 그대로 들고 간다.")
        emit("  익절은 공짜가 아니다 — 크게 먹을 꼬리를 자른다. 어디까지")
        emit("  좋아지고 어디부터 나빠지는지를 본다.\n")
        results = []
        for key in keys:
            results.extend(
                take_profit_sweep(
                    key, (lambda k=key: build_strategy(k)), levels, histories, years
                )
            )
        emit(format_comparison(results, years))
        save({"익절선(%)": args.values})
        return

    elif args.mode == "holding":
        keys = [k.strip() for k in args.keys.split(",") if k.strip()]
        if not keys:
            raise SystemExit("--keys에 전략을 지정하세요")
        emit("■ 보유 구간 되짚기 — 익절선을 논하기 전에 볼 숫자\n")
        for key in keys:
            paths = []
            for year in years:
                sliced = slice_for_year(histories, year)
                if not sliced:
                    continue
                result = BacktestEngine(
                    strategy=build_strategy(key),
                    risk_manager=RiskManager(policy_provider=RiskPolicy),
                ).run(sliced, trade_from=date(year, 1, 1))
                paths.extend(trace(result.closed_trades, sliced))
            emit(format_paths(paths, key))
            emit("")
        save()
        return

    elif args.mode == "blend":
        pairs = [k.strip() for k in args.keys.split(",") if k.strip()]
        shares = [float(w) for w in args.weights.split(",")]
        if len(pairs) != len(shares):
            raise SystemExit("--keys와 --weights의 개수가 같아야 합니다")
        emit("■ 갈래 배분 — 나눠서 굴렸을 때 합친 계좌가 어떻게 되는가")
        emit("  비중은 연 단위로만 맞춘다. 연중에 갈래끼리 자금을 옮기지 않는다 —")
        emit("  매일 맞추면 깨진 쪽에 계속 돈을 부어 주는 셈이라 결과가 부풀려진다.\n")
        curves, trades = sleeve_curves(
            {key: (lambda k=key: build_strategy(k)) for key in pairs}, histories, years
        )
        results = [blend_sleeves(curves, {key: 100.0}, years, trades) for key in pairs]
        results.append(
            blend_sleeves(curves, dict(zip(pairs, shares, strict=True)), years, trades)
        )
        emit(format_comparison(results, years))
        save()
        return

    elif args.mode == "correlation":
        keys = [k.strip() for k in args.keys.split(",") if k.strip()]
        if not keys:
            raise SystemExit("--keys에 비교할 전략을 지정하세요")
        emit("■ 전략 간 상관 — 자금을 갈래로 나눌 가치가 있는가")
        emit("  같은 날 같이 움직이면 나눠도 분산 효과가 없다. 낮을수록 좋다.\n")
        series, exposure = daily_returns_by_strategy(
            {key: (lambda k=key: build_strategy(k)) for key in keys}, histories, years
        )
        emit(format_correlation(correlation_matrix(series), exposure))
        save()
        return

    else:
        keys = [k.strip() for k in args.keys.split(",") if k.strip()]
        if not keys:
            raise SystemExit("--keys에 비교할 전략을 지정하세요")
        emit("■ 전략 비교 — 같은 데이터·같은 예열 조건\n")
        results = [
            run_experiment(key, lambda k=key: build_strategy(k), histories, years) for key in keys
        ]

    emit(format_comparison(results, years))
    save()


if __name__ == "__main__":
    main()
