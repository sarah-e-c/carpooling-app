from .main_routes import main_blueprint

def register_blueprints(app):
    app.register_blueprint(main_blueprint)