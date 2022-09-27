from distutils.command.build_scripts import first_line_re
from genericpath import isfile
from carpooling import app, db
from carpooling import models
import os

from carpooling import routes

if __name__ == '__main__':
    if not os.path.isfile('carpooling/driver_data.db'):
        db.create_all()
        first_user = models.Driver(
            first_name='sarah',
            last_name='crowder'
        )
        db.session.add(first_user)
        db.session.commit()

    app.run(debug=True) #gjghjhghjghjgjhgjhgjhghghgpoipoi0980=-0