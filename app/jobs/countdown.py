import random
from datetime import datetime
from app.config import Config
from app.utils.constants import WORLD_CUP_START, STAGE_TRANSLATION, TERMINAL_MATCH_STATUSES
from app.flex.flex_builders import build_countdown_flex, build_scorers_flex
from app.services.line_service import broadcast, BroadcastResult
from app.repositories.supabase_client import get_sent_event, mark_sent_event
from app.utils.logger import logger
from app.utils.greetings import get_random_greeting
from app.utils.free_tv_schedule import format_free_tv_section, is_free_tv_match

def check_world_cup_countdown():
    """Calculates remaining days and broadcasts a premium countdown Flex Message every morning."""
    try:
        today_date = datetime.now(Config.TZ).date()
        today_str = today_date.strftime("%Y-%m-%d")
        greeting_key = f"morning_greeting_{today_str}"
        
        # Deduplication check: do not send if already successfully sent today
        if get_sent_event(greeting_key):
            logger.info("wc_countdown_already_sent_today", extra={"date": today_str})
            return

        start_date = datetime.strptime(WORLD_CUP_START, "%Y-%m-%d").date()
        delta = (start_date - today_date).days

        if delta > 0:
            logger.info("wc_countdown_trigger", extra={"days_left": delta})
            flex_payload = build_countdown_flex(delta)
            result = broadcast(flex_payload)
            if result in {BroadcastResult.SUCCESS, BroadcastResult.PARTIAL}:
                mark_sent_event(greeting_key)
        elif delta == 0:
            # Kickoff Day Special Welcome
            logger.info("wc_countdown_kickoff_day")
            welcome_text = (
                "🏆 ศึกสายเลือดแชมป์ชนแชมป์ระดับโลกเริ่มขึ้นแล้ว!\n"
                "FIFA WORLD CUP เปิดฉากอย่างเป็นทางการแล้ววันนี้! 🎉\n\n"
                "เตรียมรับแจ้งเตือนประตูสดและเชียร์ทีมชาติที่คุณรักได้ที่นี่ตลอดทัวร์นาเมนต์ครับ! ⚽"
            )
            result = broadcast(welcome_text)
            if result in {BroadcastResult.SUCCESS, BroadcastResult.PARTIAL}:
                mark_sent_event(greeting_key)
        else:
            # Tournament is active! Send daily morning schedule briefing
            logger.info("wc_countdown_active_tournament", extra={"days_past": abs(delta)})
            from app.services.football_service import svc
            
            # Smart check: ceases morning greetings once the World Cup has officially ended
            comp_data = svc.fetch("competitions/WC", ttl=14400)
            tournament_active = True
            
            if isinstance(comp_data, dict):
                current_season = comp_data.get("currentSeason", {})
                winner = current_season.get("winner")
                if winner:
                    tournament_active = False
                else:
                    end_date_str = current_season.get("endDate", "")
                    if end_date_str:
                        try:
                            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                            if end_date <= today_date:
                                tournament_active = False
                        except Exception:
                            pass
            
            if tournament_active:
                all_data = svc.fetch("competitions/WC/matches", ttl=14400)
                if isinstance(all_data, dict):
                    all_matches = all_data.get("matches", [])
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
                # Mark as sent to prevent checking/calling APIs again today
                mark_sent_event(greeting_key)
                return
            
            # Only display greeting + top scorers
            quote = get_random_greeting()
            greeting_text = (
                f"🌅 สวัสดีตอนเช้าครับแฟนบอลโลก! 🏆\n\n"
                f"💬 \"{quote}\""
            )

            from app.utils.constants import ACTIVE_COMPETITION
            scorers_data = svc.fetch(f"competitions/{ACTIVE_COMPETITION}/scorers", ttl=14400)
            
            messages_to_send = [greeting_text]
            if isinstance(scorers_data, dict):
                scorers = scorers_data.get("scorers", [])
                if scorers:
                    scorers_flex = build_scorers_flex(scorers)
                    messages_to_send.append(scorers_flex)
            
            result = broadcast(messages_to_send)
            if result in {BroadcastResult.SUCCESS, BroadcastResult.PARTIAL}:
                mark_sent_event(greeting_key)
            else:
                # API failed (rate limit / network error) — send fallback greeting
                logger.warning("wc_morning_api_failed_fallback")
                free_tv_section = format_free_tv_section(today_date)
                quote = random.choice(FOOTBALL_GREETINGS)
                fallback_text = (
                    f"🌅 สวัสดีตอนเช้าครับแฟนบอลโลก! 🏆\n\n"
                    f"💬 \"{quote}\"\n\n"
                    f"วันนี้มีฟุตบอลโลกรอเชียร์อยู่! ⚽🔥"
                )
                if free_tv_section:
                    fallback_text += free_tv_section
                result = broadcast(fallback_text)
                if result in {BroadcastResult.SUCCESS, BroadcastResult.PARTIAL}:
                    mark_sent_event(greeting_key)
            
    except Exception as e:
        logger.error("wc_countdown_exception", extra={"error": str(e)})
