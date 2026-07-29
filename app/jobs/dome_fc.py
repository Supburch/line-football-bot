import os
import datetime
import urllib.parse
from app.config import Config
from app.services.line_service import broadcast, BroadcastResult
from app.repositories.supabase_client import get_sent_event, mark_sent_event
from app.utils.logger import logger

def send_dome_fc_morning_greeting():
    """Sends a morning greeting with a Dome FC image every morning from Aug 1 to Aug 20."""
    try:
        today_date = datetime.datetime.now(Config.TZ).date()
        
        # We want to send exactly 20 images ending on August 20, 2026.
        start_date = datetime.date(2026, 8, 1)
        end_date = datetime.date(2026, 8, 20)
        
        if today_date < start_date or today_date > end_date:
            return
            
        day_index = (today_date - start_date).days # 0 to 19
        
        today_str = today_date.strftime("%Y-%m-%d")
        greeting_key = f"dome_fc_greeting_{today_str}"
        
        if get_sent_event(greeting_key):
            logger.info("dome_fc_already_sent_today", extra={"date": today_str})
            return
            
        # Get sorted images from the static directory
        static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "dome_fc")
        if not os.path.exists(static_dir):
            logger.warning("dome_fc_dir_not_found")
            return
            
        files = sorted([f for f in os.listdir(static_dir) if f.endswith(".jpg")])
        if day_index >= len(files):
            logger.warning("dome_fc_not_enough_images")
            return
            
        image_name = files[day_index]
        greeting_text = "🌅 สวัสดีตอนเช้าครับ! ⚽"
        
        if not Config.BASE_URL:
            logger.warning("dome_fc_no_base_url")
            # If we don't have BASE_URL, we fallback to just text
            result = broadcast(greeting_text)
            if result in {BroadcastResult.SUCCESS, BroadcastResult.PARTIAL}:
                mark_sent_event(greeting_key)
            return

        # Ensure filename is URL encoded
        encoded_image_name = urllib.parse.quote(image_name)
        image_url = f"{Config.BASE_URL}/static/dome_fc/{encoded_image_name}"
        
        image_msg = {
            "type": "image",
            "originalContentUrl": image_url,
            "previewImageUrl": image_url
        }
        
        result = broadcast([image_msg, greeting_text])
        if result in {BroadcastResult.SUCCESS, BroadcastResult.PARTIAL}:
            mark_sent_event(greeting_key)
            logger.info("dome_fc_greeting_sent", extra={"day": day_index + 1})
            
    except Exception as e:
        logger.error("dome_fc_greeting_exception", extra={"error": str(e)})
