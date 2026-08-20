"""텔레그램 HTTP API를 그대로 부르는 얇은 층.

## 왜 따로 두나

`TelegramNotifier`는 "글을 보낸다" 하나만 한다. 버튼을 붙이고, 누른 것에
답하고, 이미 보낸 글의 버튼을 갈아 끼우는 일은 그보다 텔레그램 쪽 사정에
가깝다. 그걸 알림 클래스에 섞으면 알림을 쓰는 자리마다 텔레그램 사정을
알아야 한다.

**보내는 자료가 그대로 HTTP 몸통이 된다.** 버튼 판(`inline_keyboard`)이
이미 그 모양의 사전이라, 라이브러리 객체로 감쌌다 푸는 단계를 없앤다.

## 실패해도 죽지 않는다

알림이 안 갔다고 매매나 리포트가 멈추면 안 된다. 그래서 부르는 쪽이
`raise_on_error=False`를 주면 실패를 값으로 돌려준다.
"""

from __future__ import annotations

import json
from typing import Any

import requests

BASE = "https://api.telegram.org/bot{token}/{method}"
TIMEOUT = 30


def call(token: str, method: str, raise_on_error: bool = True, **몸통: Any) -> dict:
    """텔레그램 API 한 번. 돌려주는 것은 `result` 부분이다."""
    보낼것 = {k: v for k, v in 몸통.items() if v is not None}
    # 사전·목록은 JSON 글자로 넣어야 한다 — 텔레그램은 폼 값만 받는다.
    for k, v in list(보낼것.items()):
        if isinstance(v, dict | list):
            보낼것[k] = json.dumps(v, ensure_ascii=False)
    try:
        r = requests.post(BASE.format(token=token, method=method), data=보낼것, timeout=TIMEOUT)
        몸 = r.json()
    except (requests.RequestException, ValueError) as e:
        if raise_on_error:
            raise
        return {"ok": False, "description": f"{type(e).__name__}: {e}"}
    if not 몸.get("ok"):
        if raise_on_error:
            raise RuntimeError(f"텔레그램이 거절했습니다({method}): {몸.get('description')}")
        return 몸
    return 몸.get("result", {})


def get_updates(token: str, offset: int) -> list[dict]:
    """새 메시지와 **누른 버튼**을 받아 온다.

    `allowed_updates`에 `callback_query`를 안 넣으면 버튼을 눌러도
    아무것도 안 온다 — 그러면 버튼이 먹통인데 이유를 알 수 없다."""
    return call(
        token, "getUpdates", offset=offset, timeout=0,
        allowed_updates=["message", "callback_query"],
    )


def send(token: str, chat_id: str, text: str, reply_markup: dict | None = None) -> dict:
    return call(token, "sendMessage", chat_id=chat_id, text=text, reply_markup=reply_markup)


def answer_callback(token: str, callback_query_id: str, text: str = "",
                    show_alert: bool = False) -> None:
    """버튼을 누른 사람 화면에 잠깐 뜨는 한 줄.

    **이걸 안 보내면 버튼이 계속 도는 표시로 남는다** — 먹었는지 아닌지
    알 수가 없어서 또 누르게 된다."""
    call(token, "answerCallbackQuery", raise_on_error=False,
         callback_query_id=callback_query_id, text=text[:200], show_alert=show_alert)


def edit_reply_markup(token: str, chat_id: str, message_id: int,
                      reply_markup: dict | None) -> None:
    """이미 보낸 글의 버튼을 갈아 끼운다.

    같은 판으로 바꾸려 하면 텔레그램이 '안 바뀌었다'고 거절하는데, 그건
    고장이 아니므로 조용히 넘긴다."""
    call(token, "editMessageReplyMarkup", raise_on_error=False,
         chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)
