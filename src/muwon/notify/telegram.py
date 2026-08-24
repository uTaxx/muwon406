import asyncio
import html

from loguru import logger
from telegram import Bot

from muwon.notify import footer
from muwon.settings.service import SettingsService


class TelegramNotifier:
    """텔레그램 알림 전송기.

    보낼 때마다 SettingsService에서 최신 봇 토큰/채팅ID를 읽으므로, 대시보드
    /CLI에서 나중에 값을 추가·변경해도 프로세스 재시작 없이 다음 전송부터
    바로 적용된다. 토큰/채팅ID가 아직 없으면 실제 전송 대신 로그만 남긴다.
    """

    def __init__(self, settings_service: SettingsService):
        self._settings_service = settings_service

    def send(self, message: str, *, 꼬리: bool = True) -> None:
        """글 하나를 보낸다. 맨 아래에 대시보드 링크가 붙는다.

        꼬리=False는 **긴 글을 조각내 보낼 때 마지막이 아닌 조각**에만 쓴다 —
        조각마다 링크가 붙으면 읽는 흐름이 매번 끊긴다."""
        # 링크는 HTML로 붙는다. 꼬리 없는 조각도 같은 모드로 나가므로
        # 본문을 이스케이프해야 한다 — 종목명이나 오류 글에 <, & 가 섞이면
        # 텔레그램이 **글 전체를 거절하고 알림이 통째로 안 간다.**
        글 = footer.붙이기(message) if 꼬리 else html.escape(message, quote=False)
        cfg = self._settings_service.get_telegram_config()
        if not cfg.bot_token or not cfg.chat_id:
            logger.info(f"[telegram:disabled] {글}")
            return
        asyncio.run(Bot(token=cfg.bot_token).send_message(
            chat_id=cfg.chat_id, text=글,
            parse_mode="HTML", disable_web_page_preview=True))

    def send_long(self, message: str) -> int:
        """길이 제한(4096자)을 넘는 긴 글을 여러 조각으로 나눠 보낸다.

        분석 리포트처럼 통째로 복사해 쓸 글은 잘리면 못 쓰게 되므로,
        줄 단위로 안전하게 나눠 순서대로 보낸다. 보낸 조각 수를 돌려준다."""
        from muwon.analysis.report import TELEGRAM_LIMIT, split_for_telegram

        # 링크가 들어갈 자리를 미리 빼고 자른다. 다 자른 뒤에 붙이면 마지막
        # 조각이 한도를 넘어 본문이 잘린다.
        chunks = split_for_telegram(message, TELEGRAM_LIMIT - len(footer.블록()) - 2)
        for index, chunk in enumerate(chunks, start=1):
            prefix = f"({index}/{len(chunks)})\n" if len(chunks) > 1 else ""
            self.send(prefix + chunk, 꼬리=(index == len(chunks)))
        return len(chunks)
