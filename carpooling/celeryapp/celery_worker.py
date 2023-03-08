"""
Run using the command:
python celery -A carpooling.celeryapp.celery_worker.celery worker --concurrency=2 -E -l info
"""
from carpooling import celeryapp, create_app

print('here')

app = create_app()
celery = celeryapp.create_celery_app(app)
celeryapp.celery = celery
