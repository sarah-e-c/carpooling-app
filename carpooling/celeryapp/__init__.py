import logging
import ssl
import sys

# credit: example flask-sqlalchemy-celery github repo

from celery import Celery
from celery.signals import after_setup_logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

CELERY_TASK_LIST = [
    'carpooling.tasks',
]

db_session = None
celery = None


def create_celery_app(_app=None):
    """
    Create a new Celery object and tie together the Celery config to the app's config.
    Wrap all tasks in the context of the Flask application.
    :param _app: Flask app
    :return: Celery app
    """
    # New Relic integration
    # if os.environ.get('NEW_RELIC_CELERY_ENABLED') == 'True':
    #     _app.initialize('celery')

    from carpooling import db

    celery = Celery(_app.import_name,
                    broker=_app.config['CELERY_BROKER_URL'],
                    include=CELERY_TASK_LIST)
    celery.conf.update(_app.config)
    always_eager = _app.config['TESTING'] or False
    celery.conf.update({'CELERY_ALWAYS_EAGER': always_eager,
                        'CELERY_RESULT_BACKEND': f"db+{_app.config['SQLALCHEMY_DATABASE_URI']}"})
    # if _app.config['CELERY_REDIS_USE_SSL']:
    #     broker_use_ssl = {'ssl_cert_reqs': ssl.CERT_NONE}
    #     celery.conf.update({'BROKER_USE_SSL': broker_use_ssl})
    celery.__setattr__('to_add_to_session', [])
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            if not celery.conf.CELERY_ALWAYS_EAGER:
                with _app.app_context():
                    # Flask-SQLAlchemy doesn't appear to create a SQLA session that is thread safe for a
                    # Celery worker to use. To get around that we can just go ahead and create our own
                    # engine and session specific to this Celery task run.
                    #
                    # Connection Pools with multiprocessing:
                    # https://docs.sqlalchemy.org/en/latest/core/pooling.html#using-connection-pools-with-multiprocessing
                    #
                    # FMI: https://stackoverflow.com/a/51773204/920389
                    # db.session.remove()
                    # db.session.close_all()
                    # db.engine.dispose()
                    #
                    # engine = create_engine(_app.config['SQLALCHEMY_DATABASE_URI'], convert_unicode=True)
                    # db_sess = scoped_session(sessionmaker(autocommit=False, autoflush=True, bind=engine))
                    # db.session = db_sess

                    return TaskBase.__call__(self, *args, **kwargs)
            else:
                # special pytest setup
                # db.session = models.db.session = db_session
                db.session = db_session
                return TaskBase.__call__(self, *args, **kwargs)

        def after_return(self, status, retval, task_id, args, kwargs, einfo):
            """
            After each Celery task, teardown our db session.
            FMI: https://gist.github.com/twolfson/a1b329e9353f9b575131
            Flask-SQLAlchemy uses create_scoped_session at startup which avoids any setup on a
            per-request basis. This means Celery can piggyback off of this initialization.
            """

            if _app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN']:
                if not isinstance(retval, Exception):
                    with _app.app_context():
                        for item in celery.__getattribute__('to_add_to_session'):
                            db.session.add(item)
                            celery.__getattribute__('to_add_to_session').remove(item)
                        db.session.commit()
                        db.session.remove()
                        db.session.close_all()
                        db.engine.dispose()

            # If we aren't in an eager request (i.e. Flask will perform teardown), then teardown
            if not celery.conf.CELERY_ALWAYS_EAGER:
                with _app.app_context():
                    db.session.remove()
                    db.session.close_all()
                    db.engine.dispose()

    celery.Task = ContextTask

    # Sentry error tracking
    # minion.init_celery_client(_app)

    return celery
