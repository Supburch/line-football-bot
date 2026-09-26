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
)
from app.services.line_service import line_config, push_to
from app.services.scheduler_service import scheduler
from app.handlers.command_handler import handle_command
from app.repositories.supabase_client import (
    db_register_group,
    db_insert_delayed_command,
    db_get_due_delayed_commands,
    db_claim_delayed_command,
    db_reopen_delayed_command,
)
from app.utils.helpers import extract_command, extract_delayed_command, safe_group_id

handler = WebhookHandler(Config.LINE_SECRET)


def _delayed_work(job_id: str, target_id: str, cmd: str) -> bool:
    """Claim + deliver one delayed command (idempotent; shared by scheduler & cron)."""
    if not db_claim_delayed_command(job_id):
        return False  # already delivered by another path
    try:
        result = handle_command(cmd)
    except Exception as e:
        logger.error({"event": "delayed_reply_handle_failed", "error": str(e)})
        result = "❌ ขออภัยครับ ระบบขัดข้องชั่วคราว"
    ok = push_to(target_id, result)
    if not ok:
        db_reopen_delayed_command(job_id)  # retry on the next cron tick
    return ok


def schedule_delayed_reply(target_id: str, cmd: str) -> None:
    """Schedules a one-off reply DELAYED_RESPONSE_MINUTES from now.

    The command is persisted to Supabase (so an external cron can recover it if
    Render free tier sleeps/restarts the process) and also scheduled in-process
    for exact timing when the app stays awake. `_delayed_work`'s claim ensures
    the reply is delivered exactly once across both paths.
    """
    if not target_id:
        logger.warning({"event": "delayed_reply_skipped_no_target"})
        return

    run_at = datetime.now(Config.TZ) + timedelta(minutes=DELAYED_RESPONSE_MINUTES)
    job_id = f"delayed_reply_{target_id}_{int(time.time() * 1000)}"

    # 1) Persist so it survives Render free-tier sleeps/restarts.
    db_insert_delayed_command(job_id, target_id, cmd, run_at.isoformat())

    # 2) In-process fast path for exact timing when the app stays awake.
    try:
        scheduler.add_job(
            _delayed_work,
            "date",
            run_date=run_at,
            args=[job_id, target_id, cmd],
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
    except Exception as e:
        logger.error({"event": "delayed_reply_schedule_failed", "error": str(e)})


def process_due_delayed_commands() -> int:
    """Deliver every overdue delayed command. Called by /cron/delayed."""
    delivered = 0
    for row in db_get_due_delayed_commands():
        try:
            if _delayed_work(row["id"], row["target_id"], row["command"]):
                delivered += 1
        except Exception as e:
            logger.error({"event": "delayed_reply_cron_failed", "error": str(e)})
    return delivered


@handler.add(MessageEvent, message=TextMessageContent)
def handle_msg(event):
    text = event.message.text.strip()

    # Delayed wake word: process the command after a delay instead of replying now.
    if any(w in text for w in DELAYED_WAKE_WORDS):
        target_id = safe_group_id(event.source)
        if event.source.type in ["group", "room"] and target_id:
            db_register_group(target_id)
        schedule_delayed_reply(target_id, extract_delayed_command(text))
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
