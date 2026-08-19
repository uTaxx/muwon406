"""구글 시트의 `설정` 탭을 실제로 매매에 쓰이는 값으로 바꾼다.

`docs/설계_스트림릿을_걷어낼까.md`의 **2단계**다. 1단계에서 시트를 만들었고,
여기서 **파이썬이 그 값을 읽어 쓰게** 한다. DB는 백업으로 남는다.

## 순서: 시트 → DB → 기본값

시트에 적힌 것이 이깁니다. 시트에 없는 항목만 DB에 저장된 값을 쓰고,
그것도 없으면 코드 기본값을 씁니다. **한 항목이 어디서 왔는지 항상 말해
줍니다**(`출처`) — 값이 이상할 때 어디를 고쳐야 하는지 모르면 못 고칩니다.

## 두 가지 함정을 여기서 막는다

**① 단위.** 시트에는 사람이 읽는 단위(`15`, `-5`)로 적고, 코드는 소수
(`0.15`, `-0.05`)로 씁니다. 그대로 넘기면 **한 종목에 자금의 1,500%**를
넣으라는 뜻이 됩니다. 그래서 여기서 100으로 나누고, 범위를 확인합니다.

**② 킬스위치는 빈 칸이면 꺼진 것으로 본다.** 종목 탭에서는 반대입니다 —
거기서는 빈 칸이 '켜짐'입니다(줄을 추가할 때마다 Y를 적게 하면 빠뜨린
종목이 조용히 사라지므로). 하지만 **매매를 켜는 스위치는 반대여야
합니다.** 오타나 지워진 칸이 매매를 켜면 안 됩니다. 켜려면 명시적으로
적어야 합니다.

같은 저장소에서 규칙이 반대인 곳이 둘이라 헷갈리기 쉬워, 양쪽 모두에
왜 그런지 적어 뒀습니다.

## 시트를 못 읽으면 매매를 멈춘다

읽기에 실패했는데 DB 값으로 그냥 돌면, **사람이 시트에서 킬스위치를 껐는데
코드는 켜진 채로 도는** 상황이 생깁니다. 그건 이 시스템에서 제일 나쁜
고장입니다. 그래서 못 읽으면 `trading_enabled`를 **끕니다.**
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from muwon.settings.schema import RiskPolicy

#: 명시적으로 이 중 하나여야 '켜짐'이다. 빈 칸·오타는 전부 꺼짐이다.
켜짐표시 = ("Y", "YES", "TRUE", "1", "O", "ON", "예", "켬", "켜짐")

#: 시트 이름 → RiskPolicy 필드. 시트에는 %로, 정책에는 소수로 들어간다.
백분율항목 = {
    "max_position_weight": "max_position_weight",
    "stop_loss_pct": "stop_loss_pct",
    "daily_loss_limit_pct": "daily_loss_limit_pct",
    "take_profit_pct": "take_profit_pct",
}
정수항목 = {"max_concurrent_positions": "max_concurrent_positions"}
참거짓항목 = {"trading_enabled": "trading_enabled"}

#: 정책이 아니라 매매 스크립트가 따로 쓰는 값들.
기타항목 = ("require_approval", "min_turnover_eok")

아는이름 = set(백분율항목) | set(정수항목) | set(참거짓항목) | set(기타항목)


class SettingsError(ValueError):
    """설정 값이 매매에 쓸 수 없는 상태다."""


def _참인가(값: str) -> bool:
    return str(값).strip().upper() in 켜짐표시


def _숫자(이름: str, 값: str) -> float:
    try:
        return float(str(값).strip())
    except ValueError as e:
        raise SettingsError(f"{이름}: 숫자가 아닙니다 ({값!r})") from e


@dataclass(frozen=True)
class 시트설정:
    """시트에서 읽어 검증까지 끝난 값."""

    덮개: dict[str, object] = field(default_factory=dict)
    승인필요: bool = True
    최소거래대금_억: float = 0.0
    모르는이름: tuple[str, ...] = ()


def parse_settings(설정: dict[str, str]) -> 시트설정:
    """`설정` 탭의 이름·값 → 검증된 값.

    **네트워크 없이 시험할 수 있게 따로 뺐다.** 규칙이 이 함수의 전부이고,
    그걸 시험하려고 매번 구글에 붙을 수는 없다."""
    덮개: dict[str, object] = {}
    모르는것: list[str] = []

    for 이름, 원값 in 설정.items():
        키 = str(이름).strip()
        값 = str(원값).strip()
        if not 키:
            continue
        if 키 not in 아는이름:
            모르는것.append(키)
            continue
        if 값 == "":
            # 빈 칸은 "안 적었다"이지 "0으로 하라"가 아니다. 아래 단계가
            # DB나 기본값으로 채운다. 다만 킬스위치만은 빈 칸도 꺼짐이다.
            if 키 == "trading_enabled":
                덮개["trading_enabled"] = False
            continue

        if 키 in 참거짓항목:
            덮개[참거짓항목[키]] = _참인가(값)
        elif 키 in 정수항목:
            수 = _숫자(키, 값)
            if not (1 <= 수 <= 50) or 수 != int(수):
                raise SettingsError(
                    f"{키}: {값!r} — 1에서 50 사이의 정수여야 합니다 "
                    "(동시에 들 수 있는 종목 수입니다)"
                )
            덮개[정수항목[키]] = int(수)
        elif 키 in 백분율항목:
            덮개[백분율항목[키]] = _백분율(키, _숫자(키, 값)) / 100.0

    승인 = 설정.get("require_approval", "")
    최소거래대금 = _숫자("min_turnover_eok", 설정["min_turnover_eok"]) if str(
        설정.get("min_turnover_eok", "")
    ).strip() else 0.0
    if 최소거래대금 < 0:
        raise SettingsError(f"min_turnover_eok: {최소거래대금:g} — 음수일 수 없습니다")

    return 시트설정(
        덮개=덮개,
        # 승인 항목도 빈 칸이면 '받는다'가 안전한 쪽이다.
        승인필요=_참인가(승인) if str(승인).strip() else True,
        최소거래대금_억=최소거래대금,
        모르는이름=tuple(모르는것),
    )


def _백분율(키: str, 수: float) -> float:
    """사람이 %로 적은 값의 범위를 확인한다. 여기가 마지막 방어선이다."""
    if 키 == "max_position_weight":
        if not 0 < 수 <= 50:
            raise SettingsError(
                f"max_position_weight: {수:g}% — 0 초과 50 이하여야 합니다. "
                "절반 넘게 한 종목에 넣을 수 있으면 분산이 아닙니다"
            )
    elif 키 in ("stop_loss_pct", "daily_loss_limit_pct"):
        if not -50 <= 수 < 0:
            raise SettingsError(
                f"{키}: {수:g}% — 음수여야 하고 -50%보다는 커야 합니다. "
                "손절선은 '이만큼 빠지면 판다'이므로 -5처럼 적습니다"
            )
    elif 키 == "take_profit_pct" and not 0 <= 수 <= 100:
        raise SettingsError(f"take_profit_pct: {수:g}% — 0 이상 100 이하여야 합니다")
    return 수


def apply(기본: RiskPolicy, 시트: 시트설정 | None) -> tuple[RiskPolicy, dict[str, str]]:
    """DB에서 읽은 정책 위에 시트 값을 덮는다. (정책, 항목별 출처).

    **시트가 None이면 매매를 끈다.** 시트를 못 읽었다는 뜻인데, 그 상태로
    DB 값을 믿고 돌면 사람이 시트에서 끈 킬스위치가 안 먹는다.

    ## 킬스위치만 규칙이 다르다 — 덮는 게 아니라 **둘 다 켜져야 켜진다**

    다른 항목은 시트가 DB를 이긴다(시트가 원본이니까). 그런데
    `trading_enabled`을 그렇게 하면 **시트가 DB의 킬스위치를 무력화한다** —
    대시보드에서 껐는데 시트가 켜져 있으면 매매가 돈다.

    끄는 스위치는 **어느 쪽에서 꺼도 꺼져야** 한다. 켜는 것만 양쪽 동의를
    받는다. 그러면 두 곳 중 하나를 잊어도 사고가 안 나고, 틀리는 방향이
    언제나 "안 사는 쪽"이다.
    """
    if 시트 is None:
        return replace(기본, trading_enabled=False), {"trading_enabled": "시트를 못 읽어 끔"}

    덮개 = dict(시트.덮개)
    출처 = {필드: "DB" for 필드 in vars(기본)}
    for 필드 in 덮개:
        출처[필드] = "시트"

    시트킬 = 덮개.pop("trading_enabled", None)
    덮개["trading_enabled"] = 켤까 = 기본.trading_enabled and bool(시트킬)
    if 시트킬 is None:
        출처["trading_enabled"] = "시트에 없어 꺼짐"
    elif 켤까:
        출처["trading_enabled"] = "시트+DB 둘 다 켬"
    elif not 시트킬:
        출처["trading_enabled"] = "시트에서 끔"
    else:
        출처["trading_enabled"] = "DB에서 끔"

    return replace(기본, **덮개), 출처


def describe(정책: RiskPolicy, 출처: dict[str, str], 시트: 시트설정 | None) -> str:
    """사람이 읽을 한 덩어리. 로그와 텔레그램이 같은 말을 쓰게 한 군데에 둔다."""
    켬 = "켜짐" if 정책.trading_enabled else "**꺼짐**"
    줄 = [
        f"■ 지금 걸려 있는 설정 (킬스위치 {켬})",
        "",
        f"  한 종목 최대       {정책.max_position_weight * 100:>6.1f}%   [{출처.get('max_position_weight', '?')}]",
        f"  동시 보유          {정책.max_concurrent_positions:>6d}종목  [{출처.get('max_concurrent_positions', '?')}]",
        f"  손절선             {정책.stop_loss_pct * 100:>6.1f}%   [{출처.get('stop_loss_pct', '?')}]",
        f"  하루 손실 한도     {정책.daily_loss_limit_pct * 100:>6.1f}%   [{출처.get('daily_loss_limit_pct', '?')}]",
    ]
    if 시트 is not None:
        줄.append(f"  매수 전 승인       {'받음' if 시트.승인필요 else '안 받음':>6}    [시트]")
        if 시트.최소거래대금_억:
            줄.append(f"  거래대금 문턱      {시트.최소거래대금_억:>6.0f}억   [시트]")
        if 시트.모르는이름:
            줄 += [
                "",
                (f"  ⚠️ 시트에 **모르는 이름 {len(시트.모르는이름)}개**가 있습니다 — "
                 "적어 두셨지만 **아무 효과가 없습니다**:"),
                f"     {', '.join(시트.모르는이름)}",
            ]
    else:
        줄 += ["", "  ⚠️ **시트를 못 읽어 매매를 껐습니다.**"]
    return "\n".join(줄)


def build_policy_provider(service, sheet_id: str, reader=None):
    """매매 스크립트가 쓸 정책 제공자. **한 번만 읽고 그 값으로 그 회차를 돈다.**

    리스크 매니저는 종목마다 정책을 묻는다. 그때마다 구글에 붙으면 느리고,
    더 나쁘게는 **한 회차 도는 중간에 값이 바뀔 수 있다** — 앞 종목은 옛
    기준, 뒤 종목은 새 기준으로 걸러지면 나중에 로그를 봐도 왜 그랬는지
    알 수 없다. 그래서 시작할 때 한 번 읽어 고정한다.

    돌려주는 것: (정책을 돌려주는 함수, 사람이 읽을 설명, 시트설정 또는 None)
    """
    읽기 = reader
    if 읽기 is None:  # pragma: no cover — 실제 구글 호출은 시험하지 않는다
        from muwon.cloud.sector_sheet import read as 시트읽기

        def 읽기():
            return 시트읽기(sheet_id).설정

    try:
        시트 = parse_settings(읽기())
    except Exception as e:  # noqa: BLE001 — 어떤 이유든 못 읽었으면 멈춰야 한다
        시트 = None
        사유 = f"{type(e).__name__}: {e}"
    else:
        사유 = ""

    정책, 출처 = apply(service.get_risk_policy(), 시트)
    글 = describe(정책, 출처, 시트)
    if 사유:
        글 += f"\n     사유: {사유}"
    return (lambda: 정책), 글, 시트
