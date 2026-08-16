import asyncio

from loguru import logger
from telegram import Bot


class TelegramNotifier:
    """텔레그램 알림 전송기.

    토큰/채팅ID가 설정되지 않은 동안(Phase 0~1 초기)에는 실제 전송 대신
    로그만 남기고 넘어간다 — 봇 생성은 사용자가 나중에 진행.
    """

    def __init__(self, bot_token: str, chat_id: str):
        self._bot = Bot(token=bot_token) if bot_token else None
        self._chat_id = chat_id

    def send(self, message: str) -> None:
        if not self._bot or not self._chat_id:
            logger.info(f"[telegram:disabled] {message}")
            return
        asyncio.run(self._bot.send_message(chat_id=self._chat_id, text=message))
