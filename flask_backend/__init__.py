# This file makes flask_backend a Python package.

# Import the Flask app instance for easier discoverability by WSGI servers
from .app import app

# Optionally, you could initialize Flask extensions here if needed,
# but for now, app.py handles its own setup.
# Example:
# from flask_pymongo import PyMongo
# mongo = PyMongo()
#
# def create_app():
#     app = Flask(__name__)
#     # Load config
#     # Initialize extensions
#     mongo.init_app(app)
#     return app

# For the current setup, just making 'app' available is sufficient.
# The app instance is created and configured in app.py.
# The APScheduler is also started within app.py when it's run.

# If you had blueprints, you would register them here or in a factory function.
# from .routes import main_blueprint
# app.register_blueprint(main_blueprint)
