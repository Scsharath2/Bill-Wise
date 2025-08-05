from celery import Celery
from config import Config

celery_app = Celery("grocery-bill-analyzer", broker=Config.CELERY_BROKER_URL)
celery_app.conf.result_backend = Config.CELERY_RESULT_BACKEND