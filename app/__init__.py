from flask import Flask
from sqlalchemy import event
from sqlalchemy.engine import Engine

from config import Config

from .extensions import csrf, db, login_manager, migrate


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
    login_manager.init_app(app)
    csrf.init_app(app)

    # Import models so Flask-Migrate can see them.
    from . import models  # noqa: F401

    from .admin import bp as admin_bp
    from .auth import bp as auth_bp
    from .museums import bp as museums_bp

    app.register_blueprint(museums_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    return app
