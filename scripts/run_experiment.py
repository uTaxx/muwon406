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
    sleeve_curves,
    weight_sweep,
)
from muwon.analysis.market_data import load_histories
from muwon.config import bootstrap_settings
from muwon.data.universe import UNIVERSE
from muwon.data.universe_builder import active_universe
from muwon.data.yahoo_client import YahooFinanceDataSource
from muwon.db.session import make_session_factory
from muwon.scoring.config import StrategyConfig
from muwon.strategy.registry import build_strategy


def load_universe_histories(years: list[int]):
    session_factory = make_session_factory(bootstrap_settings.database_url)
    universe = active_universe(session_factory, list(UNIVERSE))
    return load_histories(
        YahooFinanceDataSource(),
        universe,
        date(min(years), 1, 1) - timedelta(days=WARMUP_DAYS),
        date(max(years), 12, 31),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="전략 실험 실행기")
    parser.add_argument(
        "mode", choices=["contribution", "sweep", "param", "strategies", "correlation", "blend"]
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
    histories = load_universe_histories(years)
    config = StrategyConfig()

    if args.mode == "contribution":
        print("■ Factor 기여도 — 하나씩 껐을 때 성과가 어떻게 변하는가")
        print("  껐는데 성과가 그대로면 그 Factor는 가중치만 차지하고 있는 것이고,")
        print("  껐더니 좋아지면 해를 끼치고 있는 것이다.\n")
        results = factor_contribution(config, histories, years)

    elif args.mode == "sweep":
        weights = [float(w) for w in args.weights.split(",")]
        print(f"■ 가중치 스윕 — {args.factor}의 비중만 바꾼다\n")
        results = weight_sweep(config, args.factor, weights, histories, years)

    elif args.mode == "param":
        values = [int(v) for v in args.values.split(",")]
        print(f"■ 파라미터 스윕 — {args.factor}.{args.param}만 바꾼다\n")
        base = json.loads(args.base_params) if args.base_params else {}
        results = param_sweep(
            config, args.factor, args.param, values, histories, years, base_params=base
        )

    elif args.mode == "blend":
        pairs = [k.strip() for k in args.keys.split(",") if k.strip()]
        shares = [float(w) for w in args.weights.split(",")]
        if len(pairs) != len(shares):
            raise SystemExit("--keys와 --weights의 개수가 같아야 합니다")
        print("■ 갈래 배분 — 나눠서 굴렸을 때 합친 계좌가 어떻게 되는가")
        print("  비중은 연 단위로만 맞춘다. 연중에 갈래끼리 자금을 옮기지 않는다 —")
        print("  매일 맞추면 깨진 쪽에 계속 돈을 부어 주는 셈이라 결과가 부풀려진다.\n")
        curves, trades = sleeve_curves(
            {key: (lambda k=key: build_strategy(k)) for key in pairs}, histories, years
        )
        results = [blend_sleeves(curves, {key: 100.0}, years, trades) for key in pairs]
        results.append(
            blend_sleeves(curves, dict(zip(pairs, shares, strict=True)), years, trades)
        )
        print(format_comparison(results, years))
        return

    elif args.mode == "correlation":
        keys = [k.strip() for k in args.keys.split(",") if k.strip()]
        if not keys:
            raise SystemExit("--keys에 비교할 전략을 지정하세요")
        print("■ 전략 간 상관 — 자금을 갈래로 나눌 가치가 있는가")
        print("  같은 날 같이 움직이면 나눠도 분산 효과가 없다. 낮을수록 좋다.\n")
        series, exposure = daily_returns_by_strategy(
            {key: (lambda k=key: build_strategy(k)) for key in keys}, histories, years
        )
        print(format_correlation(correlation_matrix(series), exposure))
        return

    else:
        keys = [k.strip() for k in args.keys.split(",") if k.strip()]
        if not keys:
            raise SystemExit("--keys에 비교할 전략을 지정하세요")
        print("■ 전략 비교 — 같은 데이터·같은 예열 조건\n")
        results = [
            run_experiment(key, lambda k=key: build_strategy(k), histories, years) for key in keys
        ]

    print(format_comparison(results, years))


if __name__ == "__main__":
    main()
