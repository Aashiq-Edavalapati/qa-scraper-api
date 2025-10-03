from flask import Flask
from celery import Celery
from config import Config
from flask_cors import CORS

celery = Celery(__name__)
celery.config_from_object('config.Config')

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app) # <-- Enable CORS for the entire app

    celery.conf.update(app.config)

    with app.app_context():
        from . import routes
        return app