from .init_db import init_db_command
from .test_address_matching import test_address_matching_command
from .make_admin import make_admin_command
from .fill_fake_people import fill_fake_people_command
from.make_example_signup import make_example_signup_command

def register_commands(app):
    """
    Register Click commands.
    """
    app.cli.add_command(init_db_command)
    app.cli.add_command(test_address_matching_command)
    app.cli.add_command(make_admin_command)
    app.cli.add_command(fill_fake_people_command)
    app.cli.add_command(make_example_signup_command)
    pass