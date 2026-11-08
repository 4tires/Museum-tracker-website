from flask import Flask
from sqlalchemy import event
from sqlalchemy.engine import Engine

from config import Config

from .extensions import csrf, db, migrate, security


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    # SQLite ignores foreign keys unless this is switched on per connection.
    # Harmless to skip on other databases, so only run it for sqlite3.
    if dbapi_connection.__class__.__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Import models so Flask-Migrate can see them.
    from . import models  # noqa: F401
    from .museums import bp as museums_bp
    from .admin import admin
    from flask_security import SQLAlchemyUserDatastore
    from .auth.forms import ExtendedRegisterForm
    
    user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
    security.init_app(app, user_datastore, register_form=ExtendedRegisterForm)
    admin.init_app(app)

    app.register_blueprint(museums_bp)

    return app
