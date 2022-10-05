from carpooling import app, db
from carpooling import models
import os

from carpooling import routes
import logging 
import secrets

logger = logging.getLogger(__name__)

if __name__ == '__main__': # run app
<<<<<<< HEAD
    
    logging.basicConfig(level=logging.DEBUG)
    if len(db.engine.table_names()) < 5:
        logger.info('first time setup')
        try:
            models.AuthKey.query.delete() # only for testing
        except:
            pass
        db.create_all()
        models.AuthKey.query.delete()
=======
    logging.basicConfig(level=logging.DEBUG)
    if len(db.engine.table_names()) < 2:
        logger.info('first time setup')
        models.AuthKey.query.delete()
        db.create_all()
>>>>>>> 48e185e (reverting)
        first_key = models.AuthKey(
            key = secrets.token_hex(4)
        )
        test_man = models.Driver(
            last_name = 'test',
            first_name = 'test',
            car_type_1 = 'test',
            car_color_1 = 'test',
            car_type_2 = 'test',
            car_color_2 = 'test',
            num_seats = 1,
            phone_number = 'test',
            email_address = 'test',
            student_or_parent = 'student',
            emergency_contact_number = 'test',
            emergency_contact_relation = 'test',
            num_years_with_license = 1
        )

        db.session.add(first_key)
        db.session.add(test_man)
        db.session.commit()
    
    app.run(debug=True)