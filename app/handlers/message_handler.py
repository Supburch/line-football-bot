import time
from datetime import datetime, timedelta

from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent, JoinEvent
from linebot.v3.messaging import (
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    FlexMessage,
    FlexContainer,
)
from app.config import Config
from app.utils.logger import logger
from app.utils.constants import (
    BOT_PREFIX,
    WAKE_WORDS,
    DELAYED_WAKE_WORDS,
    DELAYED_RESPONSE_MINUTES,
    DELAYED_ACK_TEMPLATE,
)
from app.services.line_service import line_config, push_to
from app.services.scheduler_service import scheduler
from app.handlers.command_handler import handle_command
from app.repositories.supabase_client import db_register_group
from app.utils.helpers import extract_command, extract_delayed_command, safe_group_id

handler = WebhookHandler(Config.LINE_SECRET)


def _delayed_work(target_id: str, cmd: str) -> None:
    """Runs the command at the delayed mark and pushes the result to the sender."""
    try:
        result = handle_command(cmd)
    except Exception as e:
        logger.error({"event": "delayed_reply_handle_failed", "error": str(e)})
        result = "❌ ขออภัยครับ ระบบขัดข้องชั่วคราว"
    push_to(target_id, result)


def schedule_delayed_reply(target_id: str, cmd: str) -> bool:
    """Schedules a one-off reply DELAYED_RESPONSE_MINUTES from now.

    Returns True when the job was successfully scheduled, so the caller can
    decide whether to acknowledge the request immediately.
    """
    if not target_id:
        logger.warning({"event": "delayed_reply_skipped_no_target"})
        return False

    run_at = datetime.now(Config.TZ) + timedelta(minutes=DELAYED_RESPONSE_MINUTES)
    job_id = f"delayed_reply_{target_id}_{int(time.time() * 1000)}"
    try:
        scheduler.add_job(
            _delayed_work,
            "date",
            run_date=run_at,
            args=[target_id, cmd],
            id=job_id,
            replace_existing=False,
            misfire_grace_time=60,
        )
        logger.info(
            {
                "event": "delayed_reply_scheduled",
                "target_id": target_id,
                "run_at": run_at.isoformat(),
            }
        )
        return True
    except Exception as e:
        logger.error({"event": "delayed_reply_schedule_failed", "error": str(e)})
        return False


@handler.add(MessageEvent, message=TextMessageContent)
def handle_msg(event):
    text = event.message.text.strip()

    # Delayed wake word: process the command after a delay instead of replying now.
    if any(w in text for w in DELAYED_WAKE_WORDS):
        target_id = safe_group_id(event.source)
        if event.source.type in ["group", "room"] and target_id:
            db_register_group(target_id)
        scheduled = schedule_delayed_reply(target_id, extract_delayed_command(text))
        if scheduled:
            # Acknowledge immediately (the reply token is still valid) so the
            # user knows the bot is alive; the actual result is pushed later.
            ack = DELAYED_ACK_TEMPLATE.format(minutes=DELAYED_RESPONSE_MINUTES)
            try:
                with ApiClient(line_config) as client:
                    MessagingApi(client).reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text=ack)],
                        )
                    )
            except Exception as e:
                logger.error({"event": "delayed_reply_ack_failed", "error": str(e)})
        return

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
            api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[msg]))
    except Exception as e:
        logger.error(f"handle_msg error: {e}")
        try:
            with ApiClient(line_config) as client:
                MessagingApi(client).reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="❌ ขออภัยครับ ระบบขัดข้องชั่วคราว")],
                    )
                )
        except Exception:
            pass


@handler.add(JoinEvent)
def handle_join(event):
    if event.source.type in ["group", "room"]:
        if gid := safe_group_id(event.source):
            db_register_group(gid)
