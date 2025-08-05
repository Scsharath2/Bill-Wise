from app import create_app
from app.celery_config import celery_app  # ✅ no circular import

flask_app = create_app()
celery_app.conf.update(flask_app.config)

# Import task modules *after* app context is ready
from app.tasks import parse_json_async

# Task context binding
class ContextTask(celery_app.Task):
    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return self.run(*args, **kwargs)

celery_app.Task = ContextTask
