import random
from datetime import datetime
from app.config import Config
from app.utils.constants import WORLD_CUP_START
from app.flex.flex_builders import build_countdown_flex
from app.services.line_service import broadcast
from app.utils.logger import logger
from app.utils.greetings import FOOTBALL_GREETINGS

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
            # Tournament is active! Send daily morning schedule briefing
            logger.info({"event": "wc_countdown_active_tournament", "days_past": abs(delta)})
            from app.services.football_service import svc
            
            data = svc.fetch("competitions/WC/matches?status=SCHEDULED", ttl=300)
            if isinstance(data, dict):
                matches = data.get("matches", [])
                today_str = datetime.now(Config.TZ).strftime("%Y-%m-%d")
                today_matches = []
                for m in matches:
                    utc_str = m.get("utcDate", "")
                    try:
                        dt_utc  = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
                        dt_bkk  = dt_utc.astimezone(Config.TZ)
                        if dt_bkk.strftime("%Y-%m-%d") == today_str:
                            today_matches.append(m)
                    except Exception:
                        pass
                
                if today_matches:
                    quote = random.choice(FOOTBALL_GREETINGS)
                    briefing_lines = [
                        f"🌅 สวัสดีตอนเช้าครับแฟนบอลโลก! 🏆\n\n💬 \"{quote}\"\n\nวันนี้มีศึกดวลแข้งฟุตบอลโลกรอคุณอยู่ ดังนี้:\n"
                    ]
                    for m in today_matches:
                        home = m["homeTeam"]["name"]
                        away = m["awayTeam"]["name"]
                        utc_str = m.get("utcDate", "")
                        dt_utc  = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
                        dt_bkk  = dt_utc.astimezone(Config.TZ)
                        time_str = dt_bkk.strftime("%H:%M น.")
                        stage_raw = m.get("stage", "")
                        stage_th = {
                            "GROUP_STAGE": "รอบแบ่งกลุ่ม",
                            "LAST_32": "รอบ 32 ทีมสุดท้าย",
                            "ROUND_OF_32": "รอบ 32 ทีมสุดท้าย",
                            "LAST_16": "รอบ 16 ทีมสุดท้าย",
                            "ROUND_OF_16": "รอบ 16 ทีมสุดท้าย",
                            "QUARTER_FINALS": "รอบ 8 ทีมสุดท้าย",
                            "SEMI_FINALS": "รอบรองชนะเลิศ",
                            "THIRD_PLACE": "รอบชิงอันดับ 3",
                            "FINAL": "รอบชิงชนะเลิศ"
                        }.get(stage_raw, "ฟุตบอลโลก")
                        briefing_lines.append(f"🕐 {time_str} | {home} vs {away} ({stage_th})")
                    briefing_lines.append("\nอย่าลืมเฝ้าหน้าจอเชียร์ทีมรักกันนะครับ! ⚽🔥")
                    broadcast("\n".join(briefing_lines))
                else:
                    quote = random.choice(FOOTBALL_GREETINGS)
                    rest_day_text = (
                        f"🌅 สวัสดีตอนเช้าวันพักแข้งครับแฟนบอลโลก! 🏆\n\n"
                        f"💬 \"{quote}\"\n\n"
                        f"วันนี้ไม่มีโปรแกรมการแข่งขันฟุตบอลโลก (วันพักผ่อนของนักกีฬาและทีมงาน) 😴\n"
                        f"รักษาสุขภาพและเตรียมกำลังใจให้พร้อมสำหรับรอบถัดไปนะครับ! ⚽☕"
                    )
                    broadcast(rest_day_text)
            
    except Exception as e:
        logger.error({"event": "wc_countdown_exception", "error": str(e)})
