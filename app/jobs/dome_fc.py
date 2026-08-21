import os
import datetime
import urllib.parse
from app.config import Config
from app.services.line_service import broadcast, BroadcastResult
from app.repositories.supabase_client import get_sent_event, mark_sent_event
from app.utils.logger import logger

# Dome FC morning campaign runs Aug 1-21, 2026.
_CAMPAIGN_START = datetime.date(2026, 8, 1)
_CAMPAIGN_FINAL = datetime.date(2026, 8, 23)  # +2 grace days for catch-up.


def send_dome_fc_morning_greeting():
    """Sends a morning greeting with Dome FC images (Aug 1-21, 2026, + grace days).

    Unlike the old date-indexed version, this tracks completion per IMAGE
    (dome_fc_image_<index> in sent_events), not per calendar day. That means:
    - If a day's job never runs (Render asleep, deploy broke, cron missed),
      the missing image(s) are simply still "pending" and get sent on the
      next run automatically — no image is ever silently skipped forever.
    - A day is only "done" once every image up to today has actually been
      confirmed sent via LINE (checked via BroadcastResult), not just
      because the greeting text went through.
    """
    try:
        today_date = datetime.datetime.now(Config.TZ).date()

        if today_date < _CAMPAIGN_START or today_date > _CAMPAIGN_FINAL:
            return

        static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "dome_fc")
        if not os.path.exists(static_dir):
            logger.warning("dome_fc_dir_not_found")
            return

        files = sorted([f for f in os.listdir(static_dir) if f.endswith(".jpg")])
        if not files:
            logger.warning("dome_fc_no_images_found")
            return

        if not Config.BASE_URL:
            logger.warning("dome_fc_no_base_url")
            return

        # Every image whose index has elapsed (today >= that day) and is not
        # yet confirmed sent gets picked up here, regardless of which day
        # it "should" have gone out on. This is what makes it self-healing.
        elapsed_days = (today_date - _CAMPAIGN_START).days + 1  # inclusive of today
        max_index = min(elapsed_days, len(files))
        pending = [
            i for i in range(max_index)
            if not get_sent_event(f"dome_fc_image_{i}")
        ]

        if not pending:
            logger.info("dome_fc_all_images_sent")
            return

        sent_any = False
        for day_index in pending:
            image_name = files[day_index]
            encoded_image_name = urllib.parse.quote(image_name)
            image_url = f"{Config.BASE_URL}/static/dome_fc/{encoded_image_name}"
            image_msg = {
                "type": "image",
                "originalContentUrl": image_url,
                "previewImageUrl": image_url,
            }

            result = broadcast(image_msg)
            if result in {BroadcastResult.SUCCESS, BroadcastResult.PARTIAL}:
                mark_sent_event(f"dome_fc_image_{day_index}")
                sent_any = True
                logger.info("dome_fc_image_sent", extra={"day": day_index + 1})
            else:
                # Do NOT mark as sent — next run will retry this exact image.
                logger.error(
                    "dome_fc_image_failed",
                    extra={"day": day_index + 1, "result": str(result)},
                )

        # Greeting text is independent of image success/failure, and is
        # safe to send every run (it's just a friendly caption, not
        # something that needs strict once-per-day dedup anymore).
        if today_date >= _CAMPAIGN_START + datetime.timedelta(days=len(files) - 1):
            greeting_text = (
                "🌅 สวัสดีตอนเช้าครับ! ⚽\n\n"
                "⚽🔥 พรีเมียร์ลีกกลับมาแล้ว! เตรียมมันส์ครบทุกแมตช์ เริ่มวันนี้"
            )
        else:
            greeting_text = "🌅 สวัสดีตอนเช้าครับ! ⚽"

        if sent_any or not pending:
            broadcast(greeting_text)

    except Exception as e:
        logger.error("dome_fc_greeting_exception", extra={"error": str(e)})
