from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Union
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    PushMessageRequest, TextMessage, FlexMessage, FlexContainer
)
from app.config import Config
from app.utils.logger import logger
from app.repositories.supabase_client import db_get_groups
from app.utils.aliases import FlexDict

class BroadcastResult(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    RETRYABLE_FAIL = "retryable_fail"
    FATAL_FAIL = "fatal_fail"

line_config = Configuration(access_token=Config.LINE_TOKEN)
broadcast_executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="Broadcast")

def broadcast(msg: Union[str, FlexDict, list[Union[str, FlexDict]]]) -> BroadcastResult:
    groups = db_get_groups()
    if not groups:
        return BroadcastResult.SUCCESS # Nothing to do

    raw_msgs = msg if isinstance(msg, list) else [msg]
    line_msgs = []
    for m in raw_msgs:
        if isinstance(m, dict):
            line_msgs.append(FlexMessage(alt_text="EPL Alert", contents=FlexContainer.from_dict(m)))
        else:
            line_msgs.append(TextMessage(text=m))

    def _send(gid: str) -> bool:
        try:
            with ApiClient(line_config) as client:
                MessagingApi(client).push_message(
                    PushMessageRequest(to=gid, messages=line_msgs)
                )
            return True
        except Exception as e:
            logger.error({"event": "push_failed", "group_id": gid, "error": str(e)})
            return False

    futures = []
    for gid in groups:
        futures.append(broadcast_executor.submit(_send, gid))
        
    success_count = 0
    for future in as_completed(futures):
        if future.result():
            success_count += 1
            
    if success_count == len(groups):
        return BroadcastResult.SUCCESS
    elif success_count > 0:
        return BroadcastResult.PARTIAL
    else:
        # Assuming all failed might be network or token issue -> retryable
        # In a real system we could differentiate 401 (fatal) vs 500 (retryable)
        return BroadcastResult.RETRYABLE_FAIL

def get_remaining_quota_text() -> str:
    try:
        with ApiClient(line_config) as client:
            api = MessagingApi(client)
            res = api.get_message_quota_consumption()
            usage = res.total_usage
            remaining = max(0, 200 - usage)
            return f"โควต้าคงเหลือ: {remaining}/200"
    except Exception as e:
        logger.error({"event": "get_quota_failed", "error": str(e)})
        return "โควต้าคงเหลือ: ไม่ทราบ"
