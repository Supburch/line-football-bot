from flask import request, abort, jsonify
from linebot.v3.exceptions import InvalidSignatureError
from app.handlers.message_handler import handler

def register_routes(app):
    @app.route("/callback", methods=["POST"])
    def callback():
        sig = request.headers.get("X-Line-Signature", "")
        body = request.get_data(as_text=True)
        try:
            handler.handle(body, sig)
        except InvalidSignatureError:
            abort(400)
        return "OK"

    @app.route("/")
    def index():
        """Lightweight root — does NOT hit the database."""
        return jsonify({"status": "ok", "service": "football-bot"}), 200

    @app.route("/health")
    def health():
        from app.repositories.supabase_client import supabase
        from app.utils.logger import logger
        
        status = "healthy"
        try:
            # Deep health check: ensure DB connectivity.
            # Use a table this app actually owns (football_groups) rather than
            # a generic 'users' table that may not exist in this project's schema.
            supabase.table("football_groups").select("group_id").limit(1).execute()
        except Exception as e:
            logger.error({"event": "health_check_failed", "error": str(e)})
            return jsonify({
                "status": "unhealthy", 
                "service": "football-bot", 
                "error": "Database connection failed"
            }), 503
            
        return jsonify({"status": status, "service": "football-bot"}), 200

    @app.route("/ping")
    def ping():
        return "pong", 200

    @app.route("/cron/morning")
    def cron_morning():
        """Wake-and-send hook for external schedulers (e.g. cron-job.org).

        Render's free tier sleeps the app when idle, so the in-process 08:00
        cron can be missed. Point an external scheduler at this URL every
        morning (around 08:00 Bangkok time) to wake the app and deliver the
        greeting. Safe to call multiple times: each job de-duplicates via
        Supabase 'sent_events'.
        """
        from app.jobs.countdown import check_world_cup_countdown
        from app.jobs.dome_fc import send_dome_fc_morning_greeting

        check_world_cup_countdown()
        send_dome_fc_morning_greeting()
        return jsonify({"status": "ok"}), 200
