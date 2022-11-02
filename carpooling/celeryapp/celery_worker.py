"""
Run using the command:
python celery -A app.celeryapp.celery_worker.celery worker --concurrency=2 -E -l info
"""
from carpooling import celeryapp, create_app

app = create_app()
celery = celeryapp.create_celery_app(app)
celeryapp.celery = celery