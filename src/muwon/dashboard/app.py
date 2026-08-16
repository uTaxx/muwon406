"""설정·리스크정책·변경이력·개발로그를 한 화면에서 보고 고치는 통합 대시보드.

scripts/configure.py와 마찬가지로 SettingsService 하나만 거쳐서 설정값을
읽고 쓴다 — 저장 위치·형식이 CLI와 완전히 동일하다. 변경 이력/개발 로그는
st.fragment(run_every=...)로 자동 갱신되어, 다른 폼(예: KIS 인증정보 입력
중)을 건드리지 않고 그 구역만 주기적으로 새로고침된다. 실행:

    streamlit run src/muwon/dashboard/app.py
"""

from __future__ import annotations

import dataclasses
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
REPO_ROOT = Path(__file__).resolve().parents[3]

import pandas as pd
import streamlit as st

from muwon.config import bootstrap_settings
from muwon.data.universe import find_by_symbol
from muwon.db.models import OrderRow, PositionRow
from muwon.db.session import make_session_factory
from muwon.settings.schema import KISCredentials, RiskPolicy, TelegramConfig
from muwon.settings.service import SettingsService, build_settings_service

st.set_page_config(page_title="muwon406 대시보드", layout="wide")

HISTORY_REFRESH_SECONDS = 5
DEVLOG_REFRESH_SECONDS = 20
TRADING_REFRESH_SECONDS = 5


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


def main() -> None:
    st.title("muwon406 대시보드")

    if not bootstrap_settings.master_key:
        st.warning(
            "MUWON_MASTER_KEY가 설정되어 있지 않습니다. KIS/텔레그램처럼 "
            "암호화가 필요한 값은 저장·조회할 수 없습니다. `.env`에 키를 "
            "채운 뒤 다시 시작하세요 (docs/config_architecture.md 참고)."
        )

    service = get_service()

    render_status_bar(service)
    st.divider()

    col_left, col_right = st.columns(2)
    with col_left:
        with st.expander("리스크 정책", expanded=True):
            render_risk_tab(service)
        with st.expander("KIS 인증정보", expanded=False):
            render_kis_tab(service)
        with st.expander("텔레그램 알림", expanded=False):
            render_telegram_tab(service)
    with col_right:
        with st.expander(f"변경 이력 · {HISTORY_REFRESH_SECONDS}초마다 자동 갱신", expanded=True):
            render_history_fragment(service)
        with st.expander(f"개발 로그(git 커밋) · {DEVLOG_REFRESH_SECONDS}초마다 자동 갱신", expanded=True):
            render_devlog_fragment()

    with st.expander(f"보유 종목 & 최근 주문 · {TRADING_REFRESH_SECONDS}초마다 자동 갱신", expanded=True):
        render_trading_fragment()


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


if __name__ == "__main__":
    main()
