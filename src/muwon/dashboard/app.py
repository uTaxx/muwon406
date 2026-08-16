"""KIS 인증정보/텔레그램/리스크 정책을 관리하는 설정 대시보드.

scripts/configure.py와 마찬가지로 SettingsService 하나만 거쳐서 값을
읽고 쓴다 — 저장 위치·형식이 CLI와 완전히 동일하다. 실행:

    streamlit run src/muwon/dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st

from muwon.config import bootstrap_settings
from muwon.settings.schema import KISCredentials, RiskPolicy, TelegramConfig
from muwon.settings.service import SettingsService, build_settings_service

st.set_page_config(page_title="muwon406 설정 대시보드", layout="centered")


@st.cache_resource
def get_service() -> SettingsService:
    return build_settings_service()


def _mask(value: str) -> str:
    if not value:
        return "(미설정)"
    return value[:2] + "*" * max(len(value) - 2, 0)


def main() -> None:
    st.title("muwon406 설정 대시보드")

    if not bootstrap_settings.master_key:
        st.warning(
            "MUWON_MASTER_KEY가 설정되어 있지 않습니다. KIS/텔레그램처럼 "
            "암호화가 필요한 값은 저장·조회할 수 없습니다. `.env`에 키를 "
            "채운 뒤 다시 시작하세요 (docs/config_architecture.md 참고)."
        )

    service = get_service()
    tab_risk, tab_kis, tab_telegram = st.tabs(["리스크 정책", "KIS 인증정보", "텔레그램"])
    with tab_risk:
        render_risk_tab(service)
    with tab_kis:
        render_kis_tab(service)
    with tab_telegram:
        render_telegram_tab(service)


def render_risk_tab(service: SettingsService) -> None:
    st.subheader("리스크 정책")
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
            )
        )
        st.success("리스크 정책 저장 완료 — 봇 프로세스는 최대 5초(캐시 TTL) 내 반영됩니다.")
        st.rerun()


def render_kis_tab(service: SettingsService) -> None:
    st.subheader("KIS 인증정보")
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
    st.subheader("텔레그램 알림")
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


if __name__ == "__main__":
    main()
