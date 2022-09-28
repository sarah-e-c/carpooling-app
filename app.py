from carpooling import app, db
from carpooling import models
import os

from carpooling import routes
import logging 

logger = logging.getLogger(__name__) # i cri everytime

if __name__ == '__main__': # run app
    if len(db.engine.table_names()) < 1:
        logger.info('first time setup')
        db.create_all()

    app.run(debug=True)