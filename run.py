from carpooling import app, db
from carpooling import models
import os

from carpooling import routes
import logging 

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    if len(db.engine.table_names()) < 1:
        logger.info('first time setup')
        db.create_all()

    app.run(debug=True)