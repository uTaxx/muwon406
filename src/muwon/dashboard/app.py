"""설정·리스크정책·변경이력·개발로그를 한 화면에서 보고 고치는 통합 대시보드.

scripts/configure.py와 마찬가지로 SettingsService 하나만 거쳐서 설정값을
읽고 쓴다 — 저장 위치·형식이 CLI와 완전히 동일하다. 변경 이력/개발 로그는
st.fragment(run_every=...)로 자동 갱신되어, 다른 폼(예: KIS 인증정보 입력
중)을 건드리지 않고 그 구역만 주기적으로 새로고침된다.

로컬 실행:
    streamlit run src/muwon/dashboard/app.py

폰/PC 어디서든 접속 가능한 상시 대시보드로 쓰려면 Streamlit Community
Cloud에 배포한다 — docs/deploy_streamlit_cloud.md 참고. 그 환경은 컨테이너가
재배포될 때마다 로컬 디스크가 사라지므로, 이 파일이 뜰 때 구글드라이브에서
muwon.db를 내려받고(아래 sync_db_from_drive), 설정을 바꿀 때마다 다시
올린다(sync_db_to_drive) — GitHub Actions(scripts/gdrive_sync.py)와 같은
구글드라이브 폴더를 공유해서, 대시보드에서 바꾼 설정이 다음 자동매매 실행에
반영되고 자동매매가 만든 매매 기록이 대시보드에도 보이게 한다.
"""

from __future__ import annotations

import dataclasses
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
REPO_ROOT = Path(__file__).resolve().parents[3]

import pandas as pd
import streamlit as st

st.set_page_config(page_title="muwon406 대시보드", layout="wide")

# Streamlit Community Cloud는 시크릿을 st.secrets로 주지 OS 환경변수로 주지
# 않는다 — 이 프로젝트의 설정 로딩(BootstrapSettings, gdrive_sync)은 전부
# os.environ/.env 기준이라, muwon.* 모듈을 import하기 전에(=BootstrapSettings가
# 만들어지기 전에) 여기서 미리 os.environ에 복사해 둔다. 로컬에서 .env로
# 실행할 때는 secrets.toml이 없어 아무 일도 안 하고 넘어간다.
try:
    for _key, _value in st.secrets.items():
        os.environ.setdefault(_key, str(_value))
except Exception:  # noqa: BLE001, S110 — secrets.toml 자체가 없는 로컬 실행은 정상 상황
    pass

from sqlalchemy import select

from muwon.cloud.gdrive_sync import download as gdrive_download
from muwon.cloud.gdrive_sync import upload as gdrive_upload
from muwon.config import bootstrap_settings
from muwon.data.universe import find_by_symbol
from muwon.db.models import (
    BacktestRunRow,
    OrderRow,
    PositionRow,
    RunLogRow,
    TradeRow,
)
from muwon.db.session import make_session_factory
from muwon.settings.schema import (
    KISCredentials,
    RiskPolicy,
    StrategySelection,
    TelegramConfig,
)
from muwon.settings.service import SettingsService, build_settings_service
from muwon.strategy.registry import CATEGORIES, get_definition, list_definitions

HISTORY_REFRESH_SECONDS = 5
DEVLOG_REFRESH_SECONDS = 20
TRADING_REFRESH_SECONDS = 5
DRIVE_SYNC_REFRESH_SECONDS = 30


@st.cache_resource
def get_service() -> SettingsService:
    return build_settings_service()


@st.cache_resource
def get_session_factory():
    return make_session_factory(bootstrap_settings.database_url)


def _mask(value: str) -> str:
    if not value:
        return "(미설정)"
    return value[:2] + "*" * max(len(value) - 2, 0)


def _drive_sync_configured() -> bool:
    return bool(os.environ.get("GDRIVE_SA_KEY_JSON")) and bool(os.environ.get("GDRIVE_FOLDER_ID"))


def _local_db_path() -> str | None:
    prefix = "sqlite:///"
    url = bootstrap_settings.database_url
    if not url.startswith(prefix):
        return None  # Postgres 등 파일 기반이 아닌 DB는 동기화 대상이 아니다
    return url[len(prefix) :]


def sync_db_from_drive() -> None:
    if not _drive_sync_configured():
        return
    path = _local_db_path()
    if path is None:
        return
    gdrive_download(os.environ["GDRIVE_FOLDER_ID"], Path(path).name, path)


def sync_db_to_drive() -> None:
    """설정을 바꾼 직후 호출한다 — 안 그러면 이 서버가 재배포되거나 다음
    GitHub Actions 실행이 구글드라이브에서 옛 상태를 받아가서, 방금 화면에서
    바꾼 값이 없던 일이 된다."""
    if not _drive_sync_configured():
        return
    path = _local_db_path()
    if path is None or not Path(path).exists():
        return
    gdrive_upload(os.environ["GDRIVE_FOLDER_ID"], Path(path).name, path)


@st.cache_resource
def _initial_drive_sync() -> bool:
    """프로세스가 뜰 때 딱 한 번만 — st.cache_resource라 위젯 조작으로
    화면이 다시 그려질 때마다(rerun) 다시 받지 않고, 이 서버 프로세스가
    살아있는 동안 최초 1회만 실행된다. 그 뒤로는 아래 주기적 갱신
    (render_drive_sync_fragment)이 최신 상태를 이어받는다."""
    sync_db_from_drive()
    return True


@st.fragment(run_every=DRIVE_SYNC_REFRESH_SECONDS)
def render_drive_sync_fragment() -> None:
    sync_db_from_drive()
    st.caption(
        f"☁️ 구글드라이브 동기화: {datetime.now():%H:%M:%S}"  # noqa: DTZ005 — 화면 표시용, 로컬시각이면 충분
        " (자동매매가 만든 최신 상태를 주기적으로 받아옵니다)"
    )


CARD_CSS = """
<style>
.muwon-cards { display: flex; gap: 12px; overflow-x: auto; padding: 2px 2px 10px; }
.muwon-card {
  flex: 1 0 190px; background: #fff; border-radius: 16px; padding: 14px 16px;
  box-shadow: 0 1px 3px rgba(16,24,40,.08); border: 1px solid #EEF0F4;
}
.muwon-chip {
  width: 40px; height: 40px; border-radius: 12px; display: flex;
  align-items: center; justify-content: center; font-size: 20px; margin-bottom: 10px;
}
.muwon-label { font-size: 12px; color: #667085; }
.muwon-value { font-size: 20px; font-weight: 700; color: #101828; margin: 2px 0 6px; }
.muwon-badge {
  display: inline-block; padding: 2px 10px; border-radius: 999px;
  font-size: 11px; font-weight: 600;
}
@media (prefers-color-scheme: dark) {
  .muwon-card { background: #1B1E24; border-color: #2A2E36; }
  .muwon-value { color: #ECEDEE; }
  .muwon-label { color: #98A2B3; }
}
</style>
"""

#: 목업의 파스텔 칩 색. 보라=전략, 초록=연결, 파랑=데이터, 주황=시간.
CHIP_COLORS = {
    "purple": ("#F4EBFF", "#7F56D9"),
    "green": ("#E7F6EC", "#12805C"),
    "blue": ("#E8F1FF", "#175CD3"),
    "orange": ("#FFF3E6", "#B54708"),
}


def _card(icon: str, color: str, label: str, value: str, badge: str, badge_color: str) -> str:
    chip_bg, chip_fg = CHIP_COLORS[color]
    badge_bg, badge_fg = CHIP_COLORS[badge_color]
    return (
        f'<div class="muwon-card">'
        f'<div class="muwon-chip" style="background:{chip_bg};color:{chip_fg}">{icon}</div>'
        f'<div class="muwon-label">{label}</div>'
        f'<div class="muwon-value">{value}</div>'
        f'<div class="muwon-badge" style="background:{badge_bg};color:{badge_fg}">{badge}</div>'
        f"</div>"
    )


def realized_pnl(session_factory) -> tuple[float, float, int]:
    """(오늘 실현손익, 누적 실현손익, 오늘 청산 건수).

    '오늘 손익'을 평가금액으로 내려면 지금 시세가 필요한데 대시보드는 시세를
    받지 않는다. 그래서 **청산이 끝난 거래**만으로 낸다 — 추정이 아니라
    실제로 계좌에 반영된 금액이다. 화면 문구도 '실현손익'이라고 못 박는다."""
    today = datetime.now().date()  # noqa: DTZ005 — 화면 표시용
    with session_factory() as session:
        trades = session.query(TradeRow).all()
    todays = [t for t in trades if t.exited_at and t.exited_at.date() == today]
    return (
        sum(t.pnl_amount for t in todays),
        sum(t.pnl_amount for t in trades),
        len(todays),
    )


def last_activity(session_factory) -> datetime | None:
    """마지막으로 무언가 일어난 시각 — 주문·청산 중 가장 최근."""
    with session_factory() as session:
        order = session.query(OrderRow).order_by(OrderRow.created_at.desc()).first()
        trade = session.query(TradeRow).order_by(TradeRow.exited_at.desc()).first()
    stamps = [x for x in (order.created_at if order else None, trade.exited_at if trade else None) if x]
    return max(stamps) if stamps else None


def _ago(moment: datetime | None) -> str:
    if moment is None:
        return "기록 없음"
    delta = datetime.now() - moment  # noqa: DTZ005 — 화면 표시용
    minutes = int(delta.total_seconds() // 60)
    if minutes < 1:
        return "방금 전"
    if minutes < 60:
        return f"{minutes}분 전"
    if minutes < 60 * 24:
        return f"{minutes // 60}시간 전"
    return f"{minutes // (60 * 24)}일 전"


def render_summary_cards(service: SettingsService) -> None:
    """목업의 상단 요약 카드 4개.

    목업은 '전략 3개 활성'으로 그려져 있지만 이 엔진은 활성 전략이 하나다.
    숫자를 3으로 맞추면 화면이 거짓말을 한다 — 실제 값을 쓰고, 여러 전략을
    동시에 굴리는 건 엔진 쪽 결정이 끝난 뒤의 일이다(설계안 §11에서 지금은
    만들지 않기로 결론).
    """
    session_factory = get_session_factory()
    policy = service.get_risk_policy()
    selection = service.get_strategy_selection()

    try:
        creds = service.get_kis_credentials()
        connected = bool(creds.app_key and creds.app_secret)
        env_label = "실거래" if creds.kis_env == "real" else "모의투자"
    except RuntimeError:
        connected, env_label = False, "확인 불가"

    today_pnl, total_pnl, today_count = realized_pnl(session_factory)
    activity = last_activity(session_factory)

    st.markdown(CARD_CSS, unsafe_allow_html=True)
    cards = [
        _card(
            "📈", "purple", "활성 전략",
            _display_name_for(selection.active_key),
            "LIVE" if policy.trading_enabled else "중지됨",
            "purple" if policy.trading_enabled else "orange",
        ),
        _card(
            "🔌", "green", "KIS 연결", env_label,
            "연결됨" if connected else "인증정보 없음",
            "green" if connected else "orange",
        ),
        _card(
            "💰", "blue", "오늘 실현손익",
            f"{today_pnl:+,.0f}원",
            f"누적 {total_pnl:+,.0f}원 · 오늘 {today_count}건",
            "blue",
        ),
        _card(
            "🕒", "orange", "마지막 매매 기록",
            activity.strftime("%H:%M") if activity else "—",
            _ago(activity), "orange",
        ),
    ]
    st.markdown(f'<div class="muwon-cards">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_notifications_tab() -> None:
    """주문·청산을 시간순으로 모아 보여준다.

    목업에는 '미확인 뱃지'가 있지만 읽음 상태를 저장할 곳이 없다. 표시만
    해 두고 값을 채우면 늘 미확인으로 보이거나 늘 읽음으로 보인다 — 둘 다
    거짓이라 아예 넣지 않았다. 읽음 처리가 필요해지면 테이블을 하나 만들고
    그때 붙인다."""
    session_factory = get_session_factory()
    with session_factory() as session:
        orders = session.query(OrderRow).order_by(OrderRow.created_at.desc()).limit(60).all()
        trades = session.query(TradeRow).order_by(TradeRow.exited_at.desc()).limit(60).all()

    events = [
        {
            "시각": o.created_at,
            "종류": "매수 주문" if o.side == "buy" else "매도 주문",
            "내용": f"{_symbol_name(o.symbol)} {o.quantity}주 @ {o.price:,.0f}원",
            "사유": o.reason,
        }
        for o in orders
    ] + [
        {
            "시각": t.exited_at,
            "종류": "청산 완료",
            "내용": f"{_symbol_name(t.symbol)} {t.pnl_pct:+.2f}% ({t.pnl_amount:+,.0f}원)",
            "사유": t.exit_reason,
        }
        for t in trades
    ]
    events = [e for e in events if e["시각"]]
    if not events:
        st.info(
            "아직 알림으로 보여 줄 기록이 없습니다. 자동매매가 주문을 내거나 "
            "포지션을 청산하면 여기에 시간순으로 쌓입니다."
        )
        return

    events.sort(key=lambda e: e["시각"], reverse=True)
    st.caption("주문과 청산을 시간순으로 모았습니다. 읽음 처리는 아직 없습니다.")
    st.dataframe(
        pd.DataFrame(
            [
                {**e, "시각": e["시각"].strftime("%m-%d %H:%M:%S")}
                for e in events[:80]
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )


def render_run_log(limit: int = 15) -> None:
    """엔진이 회차마다 남긴 한 줄을 그대로 보여 준다.

    빈 대시보드는 두 가지를 동시에 뜻한다 — "살 게 없었다"와 "안 돌았다".
    이 표가 그 둘을 가른다. 신호는 났는데 주문이 0이면 막은 이유가 함께
    보인다."""
    with get_session_factory()() as session:
        rows = session.scalars(
            select(RunLogRow).order_by(RunLogRow.created_at.desc()).limit(limit)
        ).all()
    if not rows:
        st.info(
            "실행 기록이 없습니다. 기록을 남기기 시작한 2026-08-18 이전 회차이거나, "
            "아직 한 번도 돌지 않은 것입니다."
        )
        return
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "실행": row.created_at.strftime("%m-%d %H:%M"),
                    "기준일": row.run_date.isoformat() if row.run_date else "시세없음",
                    "전략": row.strategy_key,
                    "대상/판단": f"{row.universe_size}/{row.checked_symbols}",
                    "신호(매수/매도)": f"{row.buy_signals}/{row.sell_signals}",
                    "주문": row.orders,
                    "막힌 이유": row.rejections.replace("\n", " · ") or "—",
                }
                for row in rows
            ]
        ),
        hide_index=True,
        width="stretch",
    )


def render_admin_tab(service: SettingsService) -> None:
    """설정·운영 관리 — 목업의 '관리' 탭.

    매매를 보는 화면과 설정을 바꾸는 화면을 갈라 놓는 게 이 탭의 목적이다.
    지금까지는 한 페이지에 섞여 있어서, 상태를 확인하러 들어와도 인증정보
    입력란이 먼저 보였다."""
    with st.expander("최근 실행 · 돌긴 돌았나", expanded=False):
        render_run_log()
    with st.expander("KIS 인증정보 · API 키 및 계좌 연결", expanded=False):
        render_kis_tab(service)
    with st.expander("텔레그램 알림 · 체결·오류·리포트", expanded=False):
        render_telegram_tab(service)
    # 리스크 정책은 대시보드 탭에만 둔다. 양쪽에 넣었더니 Streamlit이
    # 같은 키의 폼이 두 개라며 화면 전체를 죽였다 — 목업에서도 리스크
    # 정책은 대시보드 목록에 있고 관리 탭에는 없다.
    with st.expander(f"변경 이력 · {HISTORY_REFRESH_SECONDS}초마다 자동 갱신", expanded=False):
        render_history_fragment(service)
    with st.expander(f"개발 로그(git 커밋) · {DEVLOG_REFRESH_SECONDS}초마다 자동 갱신", expanded=False):
        render_devlog_fragment()


def main() -> None:
    _initial_drive_sync()
    st.title("muwon406 대시보드")
    st.caption("자주 쓰는 항목 중심")
    if _drive_sync_configured():
        render_drive_sync_fragment()

    if not bootstrap_settings.master_key:
        st.warning(
            "MUWON_MASTER_KEY가 설정되어 있지 않습니다. KIS/텔레그램처럼 "
            "암호화가 필요한 값은 저장·조회할 수 없습니다. `.env`에 키를 "
            "채운 뒤 다시 시작하세요 (docs/config_architecture.md 참고)."
        )

    service = get_service()

    broken_keys = service.undecryptable_secret_keys()
    if broken_keys:
        st.warning(
            "다음 값들이 **지금 MUWON_MASTER_KEY로는 열리지 않습니다** — "
            "마스터키를 새로 발급했는데 DB에는 이전 키로 암호화된 값이 남아 있는 "
            "상태입니다: `" + "`, `".join(broken_keys) + "`\n\n"
            "해당 항목(관리 탭의 KIS 인증정보 / 텔레그램 알림)에 값을 다시 입력해 "
            "저장하면 새 키로 다시 암호화되어 정상으로 돌아옵니다. GitHub "
            "Actions가 매 실행마다 KIS·텔레그램 값을 다시 써 주므로, 다음 "
            "자동매매 실행 뒤에 저절로 해결되기도 합니다.",
            icon="🔑",
        )

    # 목업은 하단 탭 바지만 Streamlit에는 그 위젯이 없다. CSS로 흉내내면
    # 버전이 오를 때마다 깨지므로 상단 탭을 쓴다 — 순서와 이름은 목업 그대로다.
    tab_home, tab_strategy, tab_records, tab_alerts, tab_admin = st.tabs(
        ["🏠 대시보드", "📈 전략", "📋 기록", "🔔 알림", "👤 관리"]
    )

    with tab_home:
        render_summary_cards(service)
        render_status_bar(service)
        st.divider()
        with st.expander(f"보유 종목 & 최근 주문 · {TRADING_REFRESH_SECONDS}초마다 자동 갱신", expanded=True):
            render_trading_fragment()
        with st.expander("리스크 정책 · 손절 · 비중 · 노출 한도", expanded=False):
            render_risk_tab(service)

    with tab_strategy:
        render_strategy_tab(service)
        st.divider()
        st.caption("전략 리뷰 — 다른 전략이었다면?")
        render_strategy_review_tab(service)

    with tab_records:
        render_trades_tab()

    with tab_alerts:
        render_notifications_tab()

    with tab_admin:
        st.caption("설정 및 운영 관리")
        render_admin_tab(service)


def render_status_bar(service: SettingsService) -> None:
    policy = service.get_risk_policy()

    col_toggle, col_env, col_time = st.columns([2, 2, 1])
    with col_toggle:
        enabled = st.toggle(
            "자동매매 활성화",
            value=policy.trading_enabled,
            help="꺼두면 RiskManager가 신규 진입 신호를 전부 거부합니다 (킬스위치).",
        )
        if enabled != policy.trading_enabled:
            service.set_risk_policy(dataclasses.replace(policy, trading_enabled=enabled))
            sync_db_to_drive()
            st.rerun()

    with col_env:
        try:
            kis_env = service.get_kis_credentials().kis_env
        except RuntimeError:
            kis_env = "(미확인)"
        if kis_env == "real":
            st.error("KIS 환경: **실거래(real)**", icon="⚠️")
        else:
            st.info(f"KIS 환경: {kis_env}")

    with col_time:
        st.caption(f"상태 조회: {datetime.now():%H:%M:%S}")  # noqa: DTZ005 — 화면 표시용, 로컬시각이면 충분


def _best_backtest_by_key(session_factory) -> dict[str, BacktestRunRow]:
    """전략별로 가장 최근 백테스트 기록 하나씩 — 전략 목록 옆에 성적을
    같이 보여주기 위한 것(수동 스윕/일일 리뷰 구분 없이 최신 것)."""
    with session_factory() as session:
        rows = (
            session.query(BacktestRunRow)
            .order_by(BacktestRunRow.created_at.desc())
            .limit(500)
            .all()
        )
    latest: dict[str, BacktestRunRow] = {}
    for row in rows:
        latest.setdefault(row.strategy_key, row)
    return latest


def render_strategy_tab(service: SettingsService) -> None:
    """실거래에 쓰는 전략(가설)을 보여주고 바꾼다.

    "가설"이 뭔지: 이동평균/RSI 계산에 쓰는 숫자(며칠짜리 창을 볼지 등)를
    바꾸면 같은 로직이라도 다른 결과가 나온다 — 그 숫자 조합 하나하나가
    strategy/registry.py에 이름표(전략 키)를 달고 등록되어 있다. 여기서
    "활성"으로 고른 것 하나만 실제 매매(run_paper_trading.py /
    run_realtime_trading.py)에 쓰인다.

    전략이 20개가 넘어가면 한 표에 다 늘어놓는 게 오히려 안 읽히므로,
    계열(추세추종/평균회귀/돌파·모멘텀/복합) 필터와 백테스트 성적을 함께
    붙여 "어떤 계열이 지금 장에 통하는가"를 바로 볼 수 있게 했다."""
    current_key = service.get_strategy_selection().active_key
    backtests = _best_backtest_by_key(get_session_factory())

    selected_categories = st.multiselect(
        "계열 필터",
        options=CATEGORIES,
        default=CATEGORIES,
        help=(
            "추세추종=오르는 걸 따라 사고 꺾이면 판다(승률 낮고 손익비 큼) · "
            "평균회귀=많이 빠지면 되돌아온다에 베팅(승률 높고 한 번에 크게 잃을 위험) · "
            "돌파·모멘텀=박스를 뚫으면 그 방향으로 간다(가짜 돌파가 약점) · "
            "복합=여러 규칙을 섞은 것"
        ),
    )
    only_traded = st.toggle(
        "백테스트에서 거래가 있었던 전략만",
        value=False,
        help="조건이 너무 빡빡해 한 번도 진입하지 않은 가설을 숨깁니다.",
    )

    definitions = [d for d in list_definitions() if d.category in selected_categories]
    if only_traded:
        definitions = [d for d in definitions if (backtests.get(d.key) is not None and backtests[d.key].num_trades > 0)]

    if not definitions:
        st.info("조건에 맞는 전략이 없습니다 — 필터를 넓혀 보세요.")
        return

    rows = []
    for d in definitions:
        run = backtests.get(d.key)
        rows.append(
            {
                "활성": "⭐" if d.key == current_key else "",
                "계열": d.category,
                "전략": d.display_name,
                "키": d.key,
                "수익률": f"{run.total_return_pct:+.2f}%" if run else "-",
                "MDD": f"{run.max_drawdown_pct:.1f}%" if run else "-",
                "승률": f"{run.win_rate_pct:.0f}%" if run else "-",
                "거래": run.num_trades if run else "-",
                "상태": d.status,
            }
        )
    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
        height=min(38 * (len(rows) + 1) + 3, 460),
    )
    st.caption(
        f"등록 {len(list_definitions())}개 중 {len(definitions)}개 표시 · "
        "성적은 가장 최근 백테스트 기준(`run_hypothesis_sweep.py` / 매일 도는 `run_daily_review.py`)입니다. "
        "MDD=고점 대비 최대 하락폭, 승률=이익으로 끝난 매매 비율."
    )

    with st.expander("전략별 상세 설명", expanded=False):
        for d in definitions:
            st.markdown(f"**{d.display_name}** `{d.key}` · {d.category}  \n{d.description}")

    options = [d.key for d in definitions]
    with st.form("strategy_form"):
        selected = st.selectbox(
            "실거래에 쓸 전략",
            options=options,
            index=options.index(current_key) if current_key in options else 0,
            format_func=lambda k: f"{get_definition(k).display_name}  ({k})",
        )
        submitted = st.form_submit_button("이 전략으로 전환")

    if submitted:
        service.set_strategy_selection(StrategySelection(active_key=selected))
        sync_db_to_drive()
        st.success(f"실거래 활성 전략을 '{selected}'로 변경했습니다 — 다음 매매 실행부터 반영됩니다.")
        st.rerun()


def render_risk_tab(service: SettingsService) -> None:
    current = service.get_risk_policy()

    with st.form("risk_form"):
        max_position_weight = st.number_input(
            "종목당 최대 비중",
            min_value=0.01,
            max_value=1.0,
            value=current.max_position_weight,
            step=0.01,
            format="%.2f",
        )
        stop_loss_pct = st.number_input(
            "손절 기준 (음수, 예: -0.05 = -5%)",
            min_value=-1.0,
            max_value=0.0,
            value=current.stop_loss_pct,
            step=0.01,
            format="%.2f",
        )
        daily_loss_limit_pct = st.number_input(
            "일일 손실 한도 (음수)",
            min_value=-1.0,
            max_value=0.0,
            value=current.daily_loss_limit_pct,
            step=0.01,
            format="%.2f",
        )
        max_concurrent_positions = st.number_input(
            "최대 동시 보유 종목 수",
            min_value=1,
            max_value=50,
            value=current.max_concurrent_positions,
            step=1,
        )
        submitted = st.form_submit_button("저장")

    if submitted:
        service.set_risk_policy(
            RiskPolicy(
                max_position_weight=max_position_weight,
                stop_loss_pct=stop_loss_pct,
                daily_loss_limit_pct=daily_loss_limit_pct,
                max_concurrent_positions=int(max_concurrent_positions),
                trading_enabled=current.trading_enabled,  # 상단 토글이 이 값의 유일한 창구
            )
        )
        sync_db_to_drive()
        st.success("리스크 정책 저장 완료 — 봇 프로세스는 최대 5초(캐시 TTL) 내 반영됩니다.")
        st.rerun()


def render_kis_tab(service: SettingsService) -> None:
    try:
        current = service.get_kis_credentials()
    except RuntimeError as e:
        st.error(str(e))
        return

    st.caption(
        f"현재: env={current.kis_env} · app_key={_mask(current.app_key)} · "
        f"app_secret={_mask(current.app_secret)} · account_no={_mask(current.account_no)}"
    )
    if current.is_real:
        st.warning("현재 실거래(real) 환경으로 설정되어 있습니다.")

    with st.form("kis_form"):
        kis_env = st.selectbox(
            "환경", options=["paper", "real"], index=["paper", "real"].index(current.kis_env)
        )
        app_key = st.text_input("App Key", value="", type="password", placeholder="변경 시에만 입력")
        app_secret = st.text_input(
            "App Secret", value="", type="password", placeholder="변경 시에만 입력"
        )
        account_no = st.text_input("계좌번호", value="", placeholder="변경 시에만 입력")
        account_product_cd = st.text_input(
            "계좌상품코드", value=current.account_product_cd or "01"
        )
        submitted = st.form_submit_button("저장")

    if submitted:
        try:
            service.set_kis_credentials(
                KISCredentials(
                    kis_env=kis_env,
                    app_key=app_key or current.app_key,
                    app_secret=app_secret or current.app_secret,
                    account_no=account_no or current.account_no,
                    account_product_cd=account_product_cd or current.account_product_cd,
                )
            )
            sync_db_to_drive()
            st.success("KIS 인증정보 저장 완료")
            st.rerun()
        except RuntimeError as e:
            st.error(str(e))


def render_telegram_tab(service: SettingsService) -> None:
    try:
        current = service.get_telegram_config()
    except RuntimeError as e:
        st.error(str(e))
        return

    st.caption(f"현재: chat_id={current.chat_id or '(미설정)'} · bot_token={_mask(current.bot_token)}")

    with st.form("telegram_form"):
        bot_token = st.text_input(
            "Bot Token", value="", type="password", placeholder="변경 시에만 입력"
        )
        chat_id = st.text_input("Chat ID", value=current.chat_id)
        submitted = st.form_submit_button("저장")

    if submitted:
        try:
            service.set_telegram_config(
                TelegramConfig(bot_token=bot_token or current.bot_token, chat_id=chat_id)
            )
            sync_db_to_drive()
            st.success("텔레그램 설정 저장 완료")
            st.rerun()
        except RuntimeError as e:
            st.error(str(e))


def _display_setting_value(value: str | None, is_secret: bool, decrypted: bool) -> str:
    if is_secret and not decrypted:
        return "(복호화 불가)"
    if value is None:
        return "(신규)"
    if is_secret:
        return _mask(value)
    return value


@st.fragment(run_every=HISTORY_REFRESH_SECONDS)
def render_history_fragment(service: SettingsService) -> None:
    render_history_tab(service)
    st.caption(f"마지막 갱신: {datetime.now():%H:%M:%S}")  # noqa: DTZ005 — 화면 표시용, 로컬시각이면 충분


def render_history_tab(service: SettingsService) -> None:
    st.caption("리스크 정책·KIS 인증정보·텔레그램 값이 바뀔 때마다 자동으로 남는 기록입니다.")

    entries = service.get_settings_history(limit=200)
    if not entries:
        st.info("아직 변경 이력이 없습니다.")
        return

    rows = [
        {
            "변경시각": e.changed_at.strftime("%Y-%m-%d %H:%M:%S"),
            "설정키": e.key,
            "이전값": _display_setting_value(e.old_value, e.is_secret, e.decrypted),
            "새값": _display_setting_value(e.new_value, e.is_secret, e.decrypted),
            "비밀값": "예" if e.is_secret else "",
        }
        for e in entries
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


@st.fragment(run_every=DEVLOG_REFRESH_SECONDS)
def render_devlog_fragment() -> None:
    render_devlog_tab()
    st.caption(f"마지막 갱신: {datetime.now():%H:%M:%S}")  # noqa: DTZ005 — 화면 표시용, 로컬시각이면 충분


def render_devlog_tab() -> None:
    try:
        output = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "log", "-n", "50", "--pretty=format:%h|%ad|%s", "--date=short"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        st.error(f"git 로그를 읽을 수 없습니다: {e}")
        return

    rows = []
    for line in output.splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3:
            rows.append({"커밋": parts[0], "날짜": parts[1], "메시지": parts[2]})

    if not rows:
        st.info("커밋 기록이 없습니다.")
        return
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _symbol_name(symbol: str) -> str:
    ticker = find_by_symbol(symbol)
    return ticker.name if ticker else symbol


@st.fragment(run_every=TRADING_REFRESH_SECONDS)
def render_trading_fragment() -> None:
    render_trading_tab()
    st.caption(f"마지막 갱신: {datetime.now():%H:%M:%S}")  # noqa: DTZ005 — 화면 표시용, 로컬시각이면 충분


def render_trading_tab() -> None:
    session_factory = get_session_factory()
    with session_factory() as session:
        positions = session.query(PositionRow).order_by(PositionRow.entry_date.desc()).all()
        orders = session.query(OrderRow).order_by(OrderRow.created_at.desc()).limit(50).all()

    col_positions, col_orders = st.columns(2)
    with col_positions:
        st.caption("보유 종목")
        if not positions:
            st.info("보유 중인 포지션이 없습니다.")
        else:
            rows = [
                {
                    "종목": f"{_symbol_name(p.symbol)}({p.symbol})",
                    "수량": p.quantity,
                    "진입가": f"{p.entry_price:,.0f}",
                    "진입일": p.entry_date.isoformat(),
                    "진입사유": p.entry_reason,
                }
                for p in positions
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with col_orders:
        st.caption("최근 주문 (최대 50건)")
        if not orders:
            st.info("주문 기록이 없습니다.")
        else:
            rows = [
                {
                    "시각": o.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "종목": f"{_symbol_name(o.symbol)}({o.symbol})",
                    "구분": "매수" if o.side == "buy" else "매도",
                    "수량": o.quantity,
                    "가격": f"{o.price:,.0f}",
                    "사유": o.reason,
                    "모의": "예" if o.is_paper else "실전",
                }
                for o in orders
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_trades_tab() -> None:
    """청산까지 끝난 매매(진입+청산 한 왕복)만 보여준다 — 아직 들고 있는
    포지션은 위 '보유 종목' 표에 있다. 어떤 전략(strategy_key)이 어떤
    조건에서 이기고 졌는지를 보려는 용도라, 향후 이 데이터를 AI가 읽고
    전략 수정을 제안하는 단계로 이어질 수 있도록 만들어 둔 표다."""
    session_factory = get_session_factory()
    with session_factory() as session:
        trades = session.query(TradeRow).order_by(TradeRow.exited_at.desc()).limit(50).all()

    if not trades:
        st.info("아직 청산까지 완료된 매매 기록이 없습니다.")
        return

    rows = [
        {
            "종목": f"{_symbol_name(t.symbol)}({t.symbol})",
            "전략": t.strategy_key,
            "수량": t.quantity,
            "진입가": f"{t.entry_price:,.0f}",
            "청산가": f"{t.exit_price:,.0f}",
            "손익": f"{t.pnl_amount:+,.0f}",
            "손익률": f"{t.pnl_pct:+.2f}%",
            "진입사유": t.entry_reason,
            "청산사유": t.exit_reason,
            "청산일시": t.exited_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for t in trades
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _display_name_for(strategy_key: str) -> str:
    try:
        return get_definition(strategy_key).display_name
    except KeyError:
        return strategy_key  # 이후 레지스트리에서 빠진 옛 전략 키일 수 있음


def _category_for(strategy_key: str) -> str:
    try:
        return get_definition(strategy_key).category
    except KeyError:
        return "-"


def _latest_daily_review(session_factory) -> tuple[BacktestRunRow | None, list[BacktestRunRow]]:
    """scripts/run_daily_review.py가 매일 남기는 기록(notes="daily_review")
    중, 가장 최근 기준일(period_end)의 전략별 결과를 하나씩만 골라 돌려준다
    (같은 날 여러 번 재실행했으면 가장 최근 것만 남긴다)."""
    with session_factory() as session:
        rows = (
            session.query(BacktestRunRow)
            .filter(BacktestRunRow.notes == "daily_review")
            .order_by(BacktestRunRow.period_end.desc(), BacktestRunRow.created_at.desc())
            .all()
        )
    if not rows:
        return None, []

    latest_period_end = rows[0].period_end
    seen: set[str] = set()
    latest_rows = []
    for row in rows:
        if row.period_end != latest_period_end or row.strategy_key in seen:
            continue
        seen.add(row.strategy_key)
        latest_rows.append(row)
    return rows[0], latest_rows


def render_strategy_review_tab(service: SettingsService) -> None:
    """"오늘 다른 전략이었다면 수익률이 어땠을까"를 매일 자동으로 계산해
    쌓아둔 결과(scripts/run_daily_review.py)를 표로 보여준다. GitHub
    Actions가 평일마다 자동으로 채워주므로, 여기서는 DB에 이미 쌓인
    값을 읽기만 한다."""
    session_factory = get_session_factory()
    latest, rows = _latest_daily_review(session_factory)

    if latest is None:
        st.info(
            "아직 일일 전략 리뷰 결과가 없습니다 — "
            "scripts/run_daily_review.py가 최소 한 번은 실행되어야 합니다 "
            "(GitHub Actions가 평일마다 자동으로 실행합니다)."
        )
        return

    active_key = service.get_strategy_selection().active_key
    active_row = next((r for r in rows if r.strategy_key == active_key), None)

    st.caption(f"기준 기간: {latest.period_start} ~ {latest.period_end} (최근 일일 리뷰)")

    sorted_rows = sorted(rows, key=lambda r: r.total_return_pct, reverse=True)
    table_rows = [
        {
            "활성": "⭐" if r.strategy_key == active_key else "",
            "계열": _category_for(r.strategy_key),
            "전략": _display_name_for(r.strategy_key),
            "수익률": f"{r.total_return_pct:+.2f}%",
            "MDD": f"{r.max_drawdown_pct:.1f}%",
            "승률": f"{r.win_rate_pct:.0f}%",
            "거래": r.num_trades,
            "활성 대비": (
                "-"
                if active_row is None
                else f"{r.total_return_pct - active_row.total_return_pct:+.2f}%p"
            ),
        }
        for r in sorted_rows
    ]
    st.dataframe(
        pd.DataFrame(table_rows),
        use_container_width=True,
        hide_index=True,
        height=min(38 * (len(table_rows) + 1) + 3, 460),
    )

    # 계열별 평균 — 개별 전략의 운을 걷어내고 "지금 장에 어떤 성격이 통하는가"를 본다
    by_category: dict[str, list[float]] = {}
    for r in sorted_rows:
        by_category.setdefault(_category_for(r.strategy_key), []).append(r.total_return_pct)
    if len(by_category) > 1:
        summary = sorted(
            ((cat, sum(v) / len(v), len(v)) for cat, v in by_category.items()),
            key=lambda x: x[1],
            reverse=True,
        )
        st.caption("계열별 평균 수익률 — 개별 전략의 운보다 '지금 장의 성격'을 보여준다")
        st.dataframe(
            pd.DataFrame(
                [{"계열": c, "평균 수익률": f"{avg:+.2f}%", "전략 수": n} for c, avg, n in summary]
            ),
            use_container_width=True,
            hide_index=True,
        )

    st.caption(
        "MDD(최대낙폭)는 그 기간 중 고점 대비 최대 몇 %까지 떨어졌었는지, "
        "승률은 전체 매매 중 이익으로 끝난 비율입니다. "
        "승률이 낮아도 이길 때 크게 이기면 총수익은 플러스일 수 있으니 함께 봐야 합니다."
    )


if __name__ == "__main__":
    main()
