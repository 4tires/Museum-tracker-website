from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_security import Security

db = SQLAlchemy()
migrate = Migrate(render_as_batch=True)
csrf = CSRFProtect()
security = Security()