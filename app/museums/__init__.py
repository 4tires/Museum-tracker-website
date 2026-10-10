from flask import Blueprint, render_template

bp = Blueprint("museums", __name__)


@bp.route("/")
def index():
    # TODO: list museums (add search/filter by city, country, category later)
    return render_template("museums/index.html")


# TODO: museum detail page, e.g. /museums/<slug>
