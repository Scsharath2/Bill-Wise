import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'data', 'uploads')
    PARSED_JSON_FOLDER = os.path.join(os.path.dirname(__file__), 'app')  # ← FIXED
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    SQLALCHEMY_DATABASE_URI = 'sqlite:///billwise.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False