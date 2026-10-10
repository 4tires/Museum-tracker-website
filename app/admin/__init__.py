from flask import Blueprint

bp = Blueprint("admin", __name__)

# TODO: admin-only routes to add / edit / delete museums
# TODO: an @admin_required decorator (check current_user.is_authenticated and is_admin, else abort(403))
