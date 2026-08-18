import asyncio

from loguru import logger
from telegram import Bot

from muwon.settings.service import SettingsService


class TelegramNotifier:
    """텔레그램 알림 전송기.

    보낼 때마다 SettingsService에서 최신 봇 토큰/채팅ID를 읽으므로, 대시보드
    /CLI에서 나중에 값을 추가·변경해도 프로세스 재시작 없이 다음 전송부터
    바로 적용된다. 토큰/채팅ID가 아직 없으면 실제 전송 대신 로그만 남긴다.
    """

    def __init__(self, settings_service: SettingsService):
        self._settings_service = settings_service

    def send(self, message: str) -> None:
        cfg = self._settings_service.get_telegram_config()
        if not cfg.bot_token or not cfg.chat_id:
            logger.info(f"[telegram:disabled] {message}")
            return
        asyncio.run(Bot(token=cfg.bot_token).send_message(chat_id=cfg.chat_id, text=message))

    def send_long(self, message: str) -> int:
        """길이 제한(4096자)을 넘는 긴 글을 여러 조각으로 나눠 보낸다.

        분석 리포트처럼 통째로 복사해 쓸 글은 잘리면 못 쓰게 되므로,
        줄 단위로 안전하게 나눠 순서대로 보낸다. 보낸 조각 수를 돌려준다."""
        from muwon.analysis.report import split_for_telegram

        chunks = split_for_telegram(message)
        for index, chunk in enumerate(chunks, start=1):
            prefix = f"({index}/{len(chunks)})\n" if len(chunks) > 1 else ""
            self.send(prefix + chunk)
        return len(chunks)
