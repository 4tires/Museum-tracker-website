from flask import Blueprint, render_template
from app.extensions import db
from app.models import Museum
from .hours import build_opening_hours

bp = Blueprint("museums", __name__)

@bp.route("/")
def index():
    return render_template("museums/index.html")


@bp.route("/museums")
def museums():
    # TODO: list museums (add search/filter by city, country, category later)
    stmt = db.select(Museum).order_by(Museum.name)
    museum_list = db.session.execute(stmt).scalars().all()
    return render_template("museums/museum_list.html", museums=museum_list)


# TODO: museum detail page, e.g. /museums/<slug>

@bp.route("/museums/<int:museum_id>")
def museum(museum_id):
    museum = db.get_or_404(Museum, museum_id)
    hours = build_opening_hours(museum.opening_hours)
    return render_template("museums/museum.html", museum=museum, hours=hours)
