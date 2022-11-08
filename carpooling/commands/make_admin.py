from carpooling import create_app, db
from carpooling import models


class MakeAdminCommand():

    def run(self, first_name, last_name, is_testing=True):
        """
        run the command.
        """
        app = create_app()
        with app.app_context() as f:
            make_admin(first_name, last_name)

def make_admin(first_name, last_name):
    """
    Method you can hard code to make someone admin
    """
    user = models.User.query.filter_by(first_name=first_name, last_name=last_name).first()
    user.is_admin = 2
    db.session.commit()
