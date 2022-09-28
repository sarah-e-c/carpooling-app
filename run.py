from app import app, db
from app import models
import os

from app import routes
import logging 

logger = logging.getLogger(__name__)

if __name__ == '__main__': # run app
    if len(db.engine.table_names()) < 1:
        logger.info('first time setup')
        db.create_all()

    app.run(debug=True)