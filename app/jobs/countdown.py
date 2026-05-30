from datetime import datetime
from app.config import Config
from app.utils.constants import WORLD_CUP_START
from app.flex.flex_builders import build_countdown_flex
from app.services.line_service import broadcast
from app.utils.logger import logger

def check_world_cup_countdown():
    """Calculates remaining days and broadcasts a premium countdown Flex Message every morning."""
    try:
        start_date = datetime.strptime(WORLD_CUP_START, "%Y-%m-%d").date()
        today = datetime.now(Config.TZ).date()
        delta = (start_date - today).days

        if delta > 0:
            logger.info({"event": "wc_countdown_trigger", "days_left": delta})
            flex_payload = build_countdown_flex(delta)
            broadcast(flex_payload)
        elif delta == 0:
            # Kickoff Day Special Welcome
            logger.info({"event": "wc_countdown_kickoff_day"})
            welcome_text = (
                "🏆 ศึกสายเลือดแชมป์ชนแชมป์ระดับโลกเริ่มขึ้นแล้ว!\n"
                "FIFA WORLD CUP เปิดฉากอย่างเป็นทางการแล้ววันนี้! 🎉\n\n"
                "เตรียมรับแจ้งเตือนประตูสดและเชียร์ทีมชาติที่คุณรักได้ที่นี่ตลอดทัวร์นาเมนต์ครับ! ⚽"
            )
            broadcast(welcome_text)
        else:
            logger.info({"event": "wc_countdown_inactive", "days_past": abs(delta)})
            
    except Exception as e:
        logger.error({"event": "wc_countdown_exception", "error": str(e)})
