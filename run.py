from carpooling import app, db
from carpooling import models
import os

from carpooling import routes
import logging 
import secrets

logger = logging.getLogger(__name__)

if __name__ == '__main__': # run app
    logging.basicConfig(level=logging.DEBUG)
    if len(db.engine.table_names()) < 2:
        logger.info('first time setup')
        models.AuthKey.query.delete()
        db.create_all()
        first_key = models.AuthKey(
            key = secrets.token_hex(4)
        )
        db.session.add(first_key)
        db.session.commit()
    
    app.run(debug=True)