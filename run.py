from carpooling import app, db
from carpooling import models
import os

from carpooling import routes

if __name__ == '__main__':
    if not os.path.isfile('carpooling/driver_data.db'):
        db.create_all()
        first_user = models.Driver(
            first_name='sarah',
            last_name='crowder',
            car_type_1 = 'Mazda 6',
            car_color_1 = 'Black',
            car_type_2 = 'Honda Civic',
            car_color_2 = 'Light Blue',
            phone_number = 8045906570,
            email_address = 'sarah.beth.crowder@gmail.com',
            num_seats = 2,
            student_or_parent = 'Student',
            extra_information = 'First'
        )
        db.session.add(first_user)
        db.session.commit()

    app.run(debug=True)