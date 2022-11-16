web: gunicorn carpooling:app
worker: celery --app carpooling.celeryapp.celery_worker.celery worker --loglevel=info