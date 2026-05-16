from flask import Flask
from app.routes import register_routes
from app.services.scheduler_service import start_scheduler

def create_app():
    app = Flask(__name__)
    register_routes(app)
    start_scheduler()
    return app
