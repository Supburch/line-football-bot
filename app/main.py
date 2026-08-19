import time
import traceback
from flask import Flask, request, g
from app.routes import register_routes
from app.services.scheduler_service import start_scheduler
from app.utils.logger import logger

def create_app():
    app = Flask(__name__)
    
    @app.before_request
    def start_timer():
        g.start_time = time.time()

    @app.after_request
    def log_request(response):
        # Auto-detect BASE_URL from the first real request if not set via ENV
        from app.config import Config
        if not Config.BASE_URL and request.host_url:
            host_url = request.host_url
            if host_url.startswith("http://") and "localhost" not in host_url and "127.0.0.1" not in host_url:
                host_url = host_url.replace("http://", "https://", 1)
            Config.BASE_URL = host_url.rstrip('/')

        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            logger.info({
                "event": "http_request",
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_ms": round(duration * 1000, 2)
            })
        return response

    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error({
            "event": "unhandled_exception",
            "error": str(e),
            "traceback": traceback.format_exc()
        })
        return "Internal Server Error", 500

    register_routes(app)
    start_scheduler()
    return app
