from flask import Blueprint, render_template
from app.extensions import db
from app.models import Museum

bp = Blueprint("museums", __name__)


@bp.route("/")
def index():
    # TODO: list museums (add search/filter by city, country, category later)
    stmt = db.select(Museum).order_by(Museum.name)
    museum_list = db.session.execute(stmt).scalars().all()
    return render_template("museums/index.html", museums = museum_list)


# TODO: museum detail page, e.g. /museums/<slug>
