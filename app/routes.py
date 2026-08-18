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
            # Deep health check: ensure DB connectivity
            supabase.table("users").select("id").limit(1).execute()
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
