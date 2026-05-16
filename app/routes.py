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
    @app.route("/health")
    def health():
        return jsonify({"status": "healthy", "service": "football-bot"}), 200

    @app.route("/ping")
    def ping():
        return "pong", 200
