from .main_routes import main_blueprint
from .auth_routes import auth_blueprint
from .admin_routes import admin_blueprint
from .internal_routes import internal_blueprint



def register_blueprints(app):
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(admin_blueprint)
    app.register_blueprint(internal_blueprint)

def register_task_blueprints(app):
    """
    register task blueprints. Separate because circular import lul
    """
    from .task_routes import task_blueprint
    app.register_blueprint(task_blueprint)