import os
import datetime
import urllib.parse
from app.config import Config
from app.services.line_service import broadcast, BroadcastResult
from app.repositories.supabase_client import get_sent_event, mark_sent_event
from app.utils.logger import logger

# Dome FC morning campaign runs Aug 1-21, 2026.
_CAMPAIGN_START = datetime.date(2026, 8, 1)
_CAMPAIGN_FINAL = datetime.date(2026, 8, 21)  # Last day of the campaign.


def _day_indices_for(today_date):
    """Return the 0-based image indices to send for the given date.

    Normal days send one image (day 1..20). The final day sends the last two
    images (19 and 20) together to close out the campaign.
    """
    if today_date < _CAMPAIGN_START or today_date > _CAMPAIGN_FINAL:
        return []
    if today_date == _CAMPAIGN_FINAL:
        return [18, 19]
    return [(today_date - _CAMPAIGN_START).days]


def send_dome_fc_morning_greeting():
    """Sends a morning greeting with Dome FC images (Aug 1-21, 2026)."""
    try:
        today_date = datetime.datetime.now(Config.TZ).date()
        today_str = today_date.strftime("%Y-%m-%d")
        greeting_key = f"dome_fc_greeting_{today_str}"

        if get_sent_event(greeting_key):
            logger.info("dome_fc_already_sent_today", extra={"date": today_str})
            return

        day_indices = _day_indices_for(today_date)
        if not day_indices:
            return

        static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "dome_fc")
        if not os.path.exists(static_dir):
            logger.warning("dome_fc_dir_not_found")
            return

        files = sorted([f for f in os.listdir(static_dir) if f.endswith(".jpg")])

        greeting_text = "🌅 สวัสดีตอนเช้าครับ! ⚽"

        if not Config.BASE_URL:
            logger.warning("dome_fc_no_base_url")
            result = broadcast(greeting_text)
            if result in {BroadcastResult.SUCCESS, BroadcastResult.PARTIAL}:
                mark_sent_event(greeting_key)
            return

        for day_index in day_indices:
            if day_index >= len(files):
                logger.warning("dome_fc_not_enough_images", extra={"day": day_index + 1})
                continue

            image_name = files[day_index]
            encoded_image_name = urllib.parse.quote(image_name)
            image_url = f"{Config.BASE_URL}/static/dome_fc/{encoded_image_name}"
            image_msg = {
                "type": "image",
                "originalContentUrl": image_url,
                "previewImageUrl": image_url,
            }

            # Send each image best-effort; a failure must not block the text.
            try:
                broadcast(image_msg)
                logger.info("dome_fc_image_sent", extra={"day": day_index + 1})
            except Exception as img_err:
                logger.error("dome_fc_image_exception", extra={"error": str(img_err)})

        # Send the greeting text once so the morning message always arrives.
        result = broadcast(greeting_text)
        if result in {BroadcastResult.SUCCESS, BroadcastResult.PARTIAL}:
            mark_sent_event(greeting_key)
            logger.info("dome_fc_greeting_sent", extra={"days": [d + 1 for d in day_indices]})
        else:
            logger.warning("dome_fc_greeting_broadcast_failed")

    except Exception as e:
        logger.error("dome_fc_greeting_exception", extra={"error": str(e)})
