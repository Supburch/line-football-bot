import random
from datetime import datetime
from app.config import Config
from app.utils.constants import WORLD_CUP_START, STAGE_TRANSLATION, TERMINAL_MATCH_STATUSES
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
            logger.info("wc_countdown_trigger", extra={"days_left": delta})
            flex_payload = build_countdown_flex(delta)
            broadcast(flex_payload)
        elif delta == 0:
            # Kickoff Day Special Welcome
            logger.info("wc_countdown_kickoff_day")
            welcome_text = (
                "🏆 ศึกสายเลือดแชมป์ชนแชมป์ระดับโลกเริ่มขึ้นแล้ว!\n"
                "FIFA WORLD CUP เปิดฉากอย่างเป็นทางการแล้ววันนี้! 🎉\n\n"
                "เตรียมรับแจ้งเตือนประตูสดและเชียร์ทีมชาติที่คุณรักได้ที่นี่ตลอดทัวร์นาเมนต์ครับ! ⚽"
            )
            broadcast(welcome_text)
        else:
            # Tournament is active! Send daily morning schedule briefing
            logger.info("wc_countdown_active_tournament", extra={"days_past": abs(delta)})
            from app.services.football_service import svc
            
            # Smart check: ceases morning greetings once the World Cup has officially ended
            # Layer 1 & 2: cheap lookup on competitions/WC
            comp_data = svc.fetch("competitions/WC", ttl=14400)
            tournament_active = True
            
            if isinstance(comp_data, dict):
                current_season = comp_data.get("currentSeason", {})
                # Layer 1: Check if winner is decided (truthy check)
                winner = current_season.get("winner")
                if winner:
                    tournament_active = False
                else:
                    # Layer 2: Check if endDate has passed
                    end_date_str = current_season.get("endDate", "")
                    if end_date_str:
                        try:
                            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                            if end_date <= today:
                                tournament_active = False
                        except Exception:
                            pass
            
            # Layer 3: Fallback check of all matches (only if layer 1 & 2 couldn't determine termination)
            if tournament_active:
                all_data = svc.fetch("competitions/WC/matches", ttl=14400)
                if isinstance(all_data, dict):
                    all_matches = all_data.get("matches", [])
                    
                    # Smart Final match lookup as the ultimate source of truth
                    final_match = next(
                        (m for m in all_matches if m.get("stage") == "FINAL"),
                        None
                    )
                    if final_match:
                        tournament_active = final_match.get("status") not in TERMINAL_MATCH_STATUSES
                    elif all_matches:
                        tournament_active = any(
                            m.get("status") not in TERMINAL_MATCH_STATUSES
                            for m in all_matches
                        )
            
            if not tournament_active:
                logger.info("wc_countdown_tournament_ended_silencing")
                return
            
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
                        stage_th = STAGE_TRANSLATION.get(stage_raw, "ฟุตบอลโลก")
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
        logger.error("wc_countdown_exception", extra={"error": str(e)})
