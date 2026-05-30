import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.line_service import broadcast_executor
from app.jobs.monitor_goals import monitor_goals
from app.jobs.smart_schedule import run_smart_schedule, _jitter
from app.jobs.weekly_summary import check_weekly_summary
from app.jobs.cleanup import run_cleanup
from app.jobs.countdown import check_world_cup_countdown

from app.utils.logger import logger

scheduler = BackgroundScheduler(timezone="Asia/Bangkok")

def start_scheduler():
    # Pass scheduler instance to smart_schedule so it can reschedule goal_monitor
    scheduler.add_job(monitor_goals, "interval", minutes=_jitter(20, 5), id="goal_monitor", max_instances=1, coalesce=True, replace_existing=True)
    scheduler.add_job(lambda: run_smart_schedule(scheduler), "cron", minute="0,30", id="smart_schedule", max_instances=1, coalesce=True, replace_existing=True)
    scheduler.add_job(check_weekly_summary, "cron", hour=23, minute=0, id="weekly_summary", max_instances=1, replace_existing=True)
    scheduler.add_job(run_cleanup, "interval", minutes=60, id="cleanup_sent_events", max_instances=1, coalesce=True, replace_existing=True)
    scheduler.add_job(check_world_cup_countdown, "cron", hour=8, minute=0, id="wc_countdown", max_instances=1, replace_existing=True)

    scheduler.start()
    
    # Run smart schedule immediately at startup to set the correct polling speed instantly
    try:
        run_smart_schedule(scheduler)
        logger.info("startup_smart_schedule_success")
    except Exception as e:
        logger.error("startup_smart_schedule_failed", extra={"error": str(e)})

    atexit.register(lambda: scheduler.shutdown())
    atexit.register(lambda: broadcast_executor.shutdown(wait=False))
