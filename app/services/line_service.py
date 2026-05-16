from concurrent.futures import ThreadPoolExecutor
from typing import Union, Dict
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    PushMessageRequest, TextMessage, FlexMessage, FlexContainer
)
from app.config import Config
from app.utils.logger import logger
from app.repositories.supabase_client import db_get_groups
from app.utils.aliases import FlexDict

line_config = Configuration(access_token=Config.LINE_TOKEN)
broadcast_executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="Broadcast")

def broadcast(msg: Union[str, FlexDict]):
    groups = db_get_groups()
    if not groups:
        return

    line_msg = (
        FlexMessage(alt_text="EPL Alert", contents=FlexContainer.from_dict(msg))
        if isinstance(msg, dict)
        else TextMessage(text=msg)
    )

    def _send(gid: str):
        try:
            with ApiClient(line_config) as client:
                MessagingApi(client).push_message(
                    PushMessageRequest(to=gid, messages=[line_msg])
                )
        except Exception as e:
            logger.error(f"Push failed {gid}: {e}")

    for gid in groups:
        broadcast_executor.submit(_send, gid)
