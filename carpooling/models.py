from carpooling import db

class Driver(db.Model):
    __tablename__ = 'drivers'
    index = db.Column(db.Integer, primary_key=True)
    last_name = db.Column(db.String)
    first_name = db.Column(db.String)
    num_seats = db.Column(db.String)
    phone_number = db.Column(db.String)
    email_address = db.Column(db.String)
    student_or_parent = db.Column(db.String)
    num_years_with_license = db.Column(db.String)
    car_type_1 = db.Column(db.String)
    car_color_1 = db.Column(db.String)
    car_type_2 = db.Column(db.String)
    car_color_2 = db.Column(db.String)
    car_type_3 = db.Column(db.String)
    car_color_3 = db.Column(db.String)

