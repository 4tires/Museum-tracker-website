from datetime import date

from flask import Blueprint, render_template
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import Museum, MuseumPass, Ticket
from .exhibitions import split_exhibitions
from .hours import build_opening_hours
from .tickets import build_tickets

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

def _load_museum(museum_id):
    # Load what the page needs up front, so each ticket doesn't trigger its own
    # queries for its exhibitions and pass.
    return db.get_or_404(
        Museum,
        museum_id,
        options=[
            selectinload(Museum.exhibitions),
            selectinload(Museum.opening_hours),
            selectinload(Museum.tickets).selectinload(Ticket.exhibitions),
            selectinload(Museum.tickets)
            .selectinload(Ticket.museum_pass)
            .selectinload(MuseumPass.prices),
        ],
    )


@bp.route("/museums/<int:museum_id>")
def museum(museum_id):
    museum = _load_museum(museum_id)
    today = date.today()
    hours = build_opening_hours(museum.opening_hours)
    exhibitions = split_exhibitions(museum.exhibitions, today)
    tickets = build_tickets(museum.tickets, museum.exhibitions, today)
    return render_template(
        "museums/museum.html",
        museum=museum,
        hours=hours,
        exhibitions=exhibitions,
        tickets=tickets,
    )


@bp.route("/museums/<int:museum_id>/archive")
def museum_archive(museum_id):
    museum = _load_museum(museum_id)
    exhibitions = split_exhibitions(museum.exhibitions, date.today())
    return render_template(
        "museums/museum_archive.html", museum=museum, exhibitions=exhibitions
    )