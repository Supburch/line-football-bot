from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging import ApiClient, MessagingApi, ReplyMessageRequest, TextMessage, FlexMessage, FlexContainer
from app.config import Config
from app.utils.logger import logger
from app.utils.constants import BOT_PREFIX, WAKE_WORDS
from app.services.line_service import line_config
from app.handlers.command_handler import handle_command
from app.repositories.supabase_client import db_register_group
from app.utils.helpers import extract_command, safe_group_id

handler = WebhookHandler(Config.LINE_SECRET)

@handler.add(MessageEvent, message=TextMessageContent)
def handle_msg(event):
    text = event.message.text.strip()
    is_cmd = text.startswith(BOT_PREFIX)
    is_woke = any(w in text for w in WAKE_WORDS)
    if not (is_cmd or is_woke):
        return

    if event.source.type in ["group", "room"]:
        if gid := safe_group_id(event.source):
            db_register_group(gid)

    cmd = extract_command(text)
    result = handle_command(cmd)

    try:
        with ApiClient(line_config) as client:
            api = MessagingApi(client)
            msg = (
                FlexMessage(alt_text="EPL Update", contents=FlexContainer.from_dict(result))
                if isinstance(result, dict)
                else TextMessage(text=result)
            )
            api.reply_message(ReplyMessageRequest(
                reply_token=event.reply_token, messages=[msg]
            ))
    except Exception as e:
        logger.error(f"handle_msg error: {e}")
        try:
            with ApiClient(line_config) as client:
                MessagingApi(client).reply_message(ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="❌ ขออภัยครับ ระบบขัดข้องชั่วคราว")]
                ))
        except Exception:
            pass
