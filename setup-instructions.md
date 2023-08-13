# Setup Instructions ✨

## Quickstart
If you already have everything set up, just run the following commands (in separate terminals):

1. Make sure that your postgres server is up and running.
```bash
2. redis-server
3. python -m celery -A carpooling.celeryapp.celery_worker.celery worker --concurrency=2 -E -l info
4. python -m celery -A carpooling.celeryapp.celery_worker.celery beat -l info
5. flask --debug run
```
The website should be up and running at localhost:5000. If not, check the logs for errors.
