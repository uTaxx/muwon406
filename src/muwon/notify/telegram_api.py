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


#: 우리가 받겠다고 텔레그램에 알리는 종류.
받을것 = ["message", "callback_query"]


def get_updates(token: str, offset: int) -> list[dict]:
    """새 메시지와 **누른 버튼**을 받아 온다.

    ## 함정 하나 — `allowed_updates`는 텔레그램이 기억한다

    여기 안 적은 종류는 **도착하는 즉시 버려진다.** 그리고 이 값은 요청
    하나에만 적용되는 게 아니라 **다음에 바꿀 때까지 서버가 기억한다.**

    처음에 `["message"]`만 적어 뒀다가 버튼을 붙였는데, 그 사이에 누른
    버튼은 전부 버려졌다. 버튼은 도는 표시만 내다 풀리고, 로그에는 "새
    메시지 0개"만 남아서 **무엇이 잘못됐는지 알 방법이 없었다.**

    고친 뒤에도 **고치기 전에 누른 것은 돌아오지 않는다** — 이미 버려졌다.
    다시 눌러야 한다."""
    return call(token, "getUpdates", offset=offset, timeout=0, allowed_updates=받을것)


def webhook_info(token: str) -> dict:
    """봇에 웹훅이 걸려 있나. **걸려 있으면 `getUpdates`는 아무것도 못 받는다.**

    한 봇을 두 곳에서 받을 수는 없다. n8n 같은 데서 같은 봇에 웹훅을 걸면
    우리 쪽은 조용히 빈손이 되는데, 그 사실이 어디에도 안 나타난다.
    그래서 시작할 때 물어보고 찍는다."""
    return call(token, "getWebhookInfo", raise_on_error=False)


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
