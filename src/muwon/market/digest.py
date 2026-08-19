"""리포트 전문을 텔레그램에 보낼 짧은 요약으로 줄인다.

## 왜 줄이나

시장·섹터 리포트 전문은 200줄이 넘는다. 그걸 매일 아침 텔레그램으로
보내면 **아무도 안 읽는다.** 안 읽는 알림은 없는 것과 같고, 오히려
진짜 중요한 알림이 묻힌다.

## 무엇만 남기나

1. **오늘 상태 한 줄** — 지수가 추세 위인가 아래인가, 조용한가 요동치는가
2. **섹터별 한 줄씩** — 전망이 기준선보다 나은지, 그리고 표본이 충분한지
3. **못 낸 것** — 왜 못 냈는지까지

**숫자만 늘어놓지 않는다.** 이 저장소의 전망은 이미 되돌려 검증에서
기각됐다(설계안 §29). 그러니 요약에도 **"이 숫자는 아직 못 믿는다"**를
같이 적는다. 안 적으면 매일 아침 그럴듯한 숫자를 보게 되고, 그러다
어느 날 그걸 근거로 삼게 된다.
"""

from __future__ import annotations

#: 텔레그램 한 통의 안전한 길이.
MAX_LEN = 3500


def _화살표(값: float | None, 문턱: float = 0.5) -> str:
    if 값 is None:
        return "·"
    if 값 > 문턱:
        return "▲"
    if 값 < -문턱:
        return "▼"
    return "―"


def state_line(state) -> str:
    """오늘 장 상태를 한 줄로. z점수라 0이 평소다."""
    if len(state) == 0:
        return "장 상태: 아직 잴 수 없음"
    오늘 = state.iloc[-1]

    def _값(이름: str):
        return float(오늘[이름]) if 이름 in 오늘.index else None

    조각 = []
    if (추세 := _값("kospi_추세20")) is not None:
        조각.append(f"단기추세 {_화살표(추세)}{추세:+.1f}")
    if (낙폭 := _값("kospi_고점대비")) is not None:
        조각.append(f"고점대비 {낙폭:+.1f}")
    if (변동 := _값("kospi_변동성")) is not None:
        조각.append(f"변동성 {_화살표(변동)}{변동:+.1f}")
    return f"코스피 · {' | '.join(조각)}" if 조각 else "장 상태: 지표 없음"


def summarize(state, forecasts, 기준일, 렌즈: str = "") -> str:
    """텔레그램 한 통짜리 요약."""
    lines = [
        f"📊 {기준일} 시장·섹터",
        state_line(state),
        "",
    ]

    낸것 = [f for f in forecasts if f.낼수있나]
    못낸것 = [f for f in forecasts if not f.낼수있나]

    if 낸것:
        lines.append("섹터별 (전망 vs 그냥 찍었을 때)")
        for f in 낸것:
            더한것 = f.더한것_상승확률
            if 더한것 is None:
                lines.append(f"  {f.대상}  {f.상승확률:.0f}%")
                continue
            # 우연 폭을 못 넘으면 숫자를 강조하지 않는다 — 강조하면
            # 그게 곧 근거로 읽힌다.
            표시 = "★" if f.우연을_넘었나 else "·"
            lines.append(
                f"  {표시} {f.대상}  {f.상승확률:.0f}% "
                f"({더한것:+.0f}%p, 우연폭 ±{f.우연폭:.0f})"
            )

    if 못낸것:
        lines += ["", f"전망 못 냄 {len(못낸것)}개"]
        for f in 못낸것[:5]:
            lines.append(f"  · {f.대상}: {f.사유}")

    lines += [
        "",
        "⚠ 이 전망은 되돌려 검증에서 **기각**됐습니다(설계안 §29).",
        "  적중률 51.8% < 그냥 찍었을 때 56.3%.",
        "  매매 판단에 쓰지 마세요 — 기록으로만 봅니다.",
        "",
        f"※ 아무것도 사지 않았습니다. 렌즈 {렌즈}" if 렌즈 else "※ 아무것도 사지 않았습니다.",
    ]

    글 = "\n".join(lines)
    if len(글) > MAX_LEN:
        글 = 글[: MAX_LEN - 20] + "\n… (줄임)"
    return 글
