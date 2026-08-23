"""把低熵的 response id 換成唯一值，讓 SpendLogs 的 request_id 不再撞號。

背景：
  * SpendLogs 的 request_id 取自 get_spend_logs_id()：優先用上游回傳的
    response id，缺了才退回 litellm_call_id，無設定開關可改。
  * Ollama 系上游回的 id 是
    chatcmpl-<0..998>，號碼空間只有 999 個；撞號的紀錄被
    create_many(skip_duplicates=True) 靜默丟棄，不報錯、不留日誌。
    實測一天內就能讓成功請求的留存率掉到三成。

掛鉤點為什麼是 async_logging_hook：
  Logging.async_success_handler 會「先」對所有 CustomLogger 呼叫
  async_logging_hook（LOGGING HOOK 迴圈），「之後」才把結果派發給各
  callback 的 async_log_success_event —— 寫 SpendLogs 的 _ProxyDBLogger
  也在派發那一輪。所以在這裡改寫 id，保證先於落庫，沒有競態。
  串流回應落庫時讀的是 model_call_details["async_complete_streaming_response"]，
  與 result 不是同一個物件，要一併改寫（同一個請求用同一個新 id）。

改寫規則：
  * 只動「沒有 id」或「前綴後不足 16 字元」的低熵 id（chatcmpl-473 這種）；
    上游若回的是夠長的唯一 id 就原樣保留，維持 client 與紀錄的對應。
  * 新 id = 原前綴 + litellm_call_id（proxy 回應的 x-litellm-call-id header
    就是它，仍可與 client 端關聯）；拿不到 call id 才退回 uuid4。
  * 任何例外都吞掉並回傳原值 —— 這個 hook 絕不能弄斷整條 logging 鏈。

失敗的請求本來就沒有上游 id、會用 litellm_call_id（UUID），不受影響。
"""

from __future__ import annotations

import re
import uuid
from typing import Any

from litellm.integrations.custom_logger import CustomLogger

# 「字母開頭 + '-' 或 '_'」視為 id 前綴，如 chatcmpl- / cmpl- / resp_
_PREFIX_RE = re.compile(r"^([A-Za-z]+[-_])")

# 前綴後的隨機部分短於這個長度就視為低熵、需要改寫（UUID 為 36 字元）
_MIN_UNIQUE_SUFFIX = 16


def _needs_rewrite(current_id: Any) -> bool:
    if not current_id or not isinstance(current_id, str):
        return True
    match = _PREFIX_RE.match(current_id)
    suffix = current_id[match.end():] if match else current_id
    return len(suffix) < _MIN_UNIQUE_SUFFIX


def _rewrite_id(obj: Any, unique_suffix: str) -> None:
    """就地改寫 obj 的 id。obj 可能是 pydantic 回應物件、dict 或 None。"""
    if obj is None:
        return
    if isinstance(obj, dict):
        current = obj.get("id")
        if "id" in obj and _needs_rewrite(current):
            match = _PREFIX_RE.match(current) if isinstance(current, str) else None
            obj["id"] = f"{match.group(1) if match else 'chatcmpl-'}{unique_suffix}"
    elif hasattr(obj, "id"):
        current = getattr(obj, "id", None)
        if _needs_rewrite(current):
            match = _PREFIX_RE.match(current) if isinstance(current, str) else None
            obj.id = f"{match.group(1) if match else 'chatcmpl-'}{unique_suffix}"


def _apply(kwargs: dict, result: Any) -> None:
    litellm_params = kwargs.get("litellm_params") or {}
    call_id = kwargs.get("litellm_call_id") or litellm_params.get("litellm_call_id")
    # 同一個請求的 result 與組裝後的串流回應必須拿到同一個新 id
    unique_suffix = str(call_id or uuid.uuid4())
    _rewrite_id(result, unique_suffix)
    _rewrite_id(kwargs.get("async_complete_streaming_response"), unique_suffix)
    _rewrite_id(kwargs.get("complete_streaming_response"), unique_suffix)


class UniqueRequestId(CustomLogger):
    async def async_logging_hook(
        self, kwargs: dict, result: Any, call_type: str
    ) -> tuple[dict, Any]:
        try:
            _apply(kwargs, result)
        except Exception:
            pass  # 改寫失敗就維持原樣
        return kwargs, result

    def logging_hook(
        self, kwargs: dict, result: Any, call_type: str
    ) -> tuple[dict, Any]:
        try:
            _apply(kwargs, result)
        except Exception:
            pass
        return kwargs, result


unique_request_id = UniqueRequestId()
