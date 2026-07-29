import atexit
import time
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.line_service import broadcast_executor
from app.jobs.monitor_goals import monitor_goals, log_state_manager_health
from app.jobs.smart_schedule import run_smart_schedule, _jitter
from app.jobs.weekly_summary import check_weekly_summary
from app.jobs.cleanup import run_cleanup
from app.jobs.countdown import check_world_cup_countdown
from app.jobs.dome_fc import send_dome_fc_morning_greeting

from app.utils.logger import logger

scheduler = BackgroundScheduler(timezone="Asia/Bangkok")

def start_scheduler():
    # Pass scheduler instance to smart_schedule so it can reschedule goal_monitor
    scheduler.add_job(monitor_goals, "interval", minutes=_jitter(20, 5), id="goal_monitor", max_instances=1, coalesce=True, replace_existing=True)
    scheduler.add_job(lambda: run_smart_schedule(scheduler), "cron", minute="0,30", id="smart_schedule", max_instances=1, coalesce=True, replace_existing=True)
    scheduler.add_job(check_weekly_summary, "cron", hour=23, minute=0, id="weekly_summary", max_instances=1, replace_existing=True)
    scheduler.add_job(run_cleanup, "interval", minutes=60, id="cleanup_sent_events", max_instances=1, coalesce=True, replace_existing=True)
    scheduler.add_job(check_world_cup_countdown, "cron", hour=8, minute=0, id="wc_countdown", max_instances=1, replace_existing=True)
    scheduler.add_job(send_dome_fc_morning_greeting, "cron", hour=8, minute=5, id="dome_fc_greeting", max_instances=1, replace_existing=True)
    
    # Observability: Fixed 30-minute health report cron job
    scheduler.add_job(log_state_manager_health, "cron", minute="0,30", id="state_manager_health", max_instances=1, coalesce=True, replace_existing=True)

    scheduler.start()
    
    # Run smart schedule immediately at startup to set the correct polling speed instantly
    try:
        run_smart_schedule(scheduler)
        logger.info("startup_smart_schedule_success")
    except Exception as e:
        logger.error("startup_smart_schedule_failed", extra={"error": str(e)})
        # Failsafe: if startup smart schedule fails, set fast polling to avoid 20-min silence
        try:
            scheduler.reschedule_job("goal_monitor", trigger="interval", minutes=3)
            logger.info("startup_failsafe_fast_mode_activated")
        except Exception:
            pass

    # Asynchronously check for missed morning greeting if restarting within the 8–10 AM window BKK
    # Only triggers during the 2-hour grace window to recover from a missed cron job.
    # Intentionally skips restarts at other hours (e.g. night deploys) to avoid off-hours greetings.
    def _async_startup_greeting_check():
        time.sleep(5)  # Let the app stabilize and connect to Supabase
        try:
            from datetime import datetime
            from app.config import Config
            now_bkk = datetime.now(Config.TZ)
            if 8 <= now_bkk.hour < 10:
                logger.info("startup_checking_missed_morning_greeting", extra={"current_hour": now_bkk.hour})
                check_world_cup_countdown()
                send_dome_fc_morning_greeting()
            else:
                logger.info("startup_greeting_check_skipped_outside_window", extra={"current_hour": now_bkk.hour})
        except Exception as startup_err:
            logger.error("startup_greeting_check_failed", extra={"error": str(startup_err)})

    threading.Thread(target=_async_startup_greeting_check, daemon=True).start()

    atexit.register(lambda: scheduler.shutdown())
    atexit.register(lambda: broadcast_executor.shutdown(wait=False))
