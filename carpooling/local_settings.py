import os
from datetime import timedelta

from load_dotenv import load_dotenv

load_dotenv()

# credit: flask/celery/sqlalchemy example repo on github
# *****************************
# Environment specific settings
# *****************************

# credit: flask/sqlalchemy/celery repository on github

# DO NOT use "DEBUG = True" in production environments
DEBUG = bool(os.environ.get('DEBUG', False))

# DO NOT use Unsecure Secrets in production environments
# Generate a safe one with:
#     python -c "import os; print repr(os.urandom(24));"
SECRET_KEY = os.environ['SECRET_KEY']

# SQLAlchemy settings
SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL'].replace('postgres://', 'postgresql://', 1) # 'postgresql://postgres:postgres@localhost/test_carpooling_app' # 'sqlite:///test.db'# 'postgresql://qzqhpcmrlkzzgo:84c9b853f90df0ce9d2d16ed8e40eec261c3986fa69cbfa9cc8adcfb1a138505@ec2-35-170-146-54.compute-1.amazonaws.com:5432/d4aq5pfpjrhene'
SQLALCHEMY_TRACK_MODIFICATIONS = False    # Avoids a SQLAlchemy Warning

# Flask-Mail settings
# For smtp.gmail.com to work, you MUST set "Allow less secure apps" to ON in Google Accounts.
# Change it in https://myaccount.google.com/security#connectedapps (near the bottom).
MAIL_SERVER = 'smtp.zoho.com'
MAIL_PORT = 587
MAIL_USE_SSL = False
MAIL_USE_TLS = True
MAIL_USERNAME = os.environ['MAIL_USERNAME']
MAIL_PASSWORD = os.environ['MAIL_PASSWORD']

# # Sendgrid settings
# SENDGRID_API_KEY='place-your-sendgrid-api-key-here'

# # Flask-User settings
# USER_APP_NAME = 'Flask-User starter app'
# USER_EMAIL_SENDER_NAME = 'Your name'
# USER_EMAIL_SENDER_EMAIL = 'yourname@gmail.com'

# ADMINS = [
#     '"Admin One" <admin1@gmail.com>',
#     ]

CELERY_BROKER_URL = os.environ['REDIS_URL']
CELERY_BACKEND_URL = os.environ['REDIS_URL']


if DEBUG:
    schedule = timedelta(seconds=10)
else:
    schedule = timedelta(minutes=10)

CELERYBEAT_SCHEDULE = {
    # Executes every minute for testing purposes, every 10 minutes in production
    'periodic_task-every-minute': {
        'task': 'maintenance_task',
        'schedule': schedule
    }
}

GOOGLE_API_KEY = 'asdlkfjadsflkj' # not used
