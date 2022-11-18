from .init_db import init_db_command, init_db_command_for_code
from .address_matching_test import address_matching_test_command
from .make_admin import make_admin_command
from .fill_fake_people import fill_fake_people_command
from.make_example_signup import make_example_signup_command
from .store_as_test_data import store_as_test_data_command

def register_commands(app):
    """
    Register Click commands.
    """
    app.cli.add_command(init_db_command)
    app.cli.add_command(address_matching_test_command)
    app.cli.add_command(make_admin_command)
    app.cli.add_command(fill_fake_people_command)
    app.cli.add_command(make_example_signup_command)
    app.cli.add_command(store_as_test_data_command)