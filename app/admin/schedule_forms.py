"""Shared form helpers for models with schedule columns (tickets, guided visits)."""

from sqlalchemy.orm import joinedload
from wtforms import SelectField

from .. import models
from ..extensions import db
from ..museums.hours import WEEKDAYS
from .hours_edit import ORDINALS


def _int_or_none(value):
    return int(value) if value not in ("", None) else None


def _choices(options):
    return dict(choices=[("", "—"), *options], coerce=_int_or_none)


# Weekday and week of the month are stored as numbers; show names instead.
SCHEDULE_OVERRIDES = {"weekday": SelectField, "week_of_month": SelectField}
SCHEDULE_ARGS = {
    "weekday": _choices(list(enumerate(WEEKDAYS))),
    "week_of_month": _choices(list(ORDINALS.items())),
}


def exhibition_label(e) -> str:
    return f"{e.museum.name} – {e.name}"


def exhibition_query():
    return (
        db.session.query(models.Exhibition)
        .options(joinedload(models.Exhibition.museum))
        .order_by(models.Exhibition.museum_id, models.Exhibition.name)
    )


EXHIBITION_ARGS = {"get_label": exhibition_label, "query_factory": exhibition_query}


def schedule_problems(m) -> list[str]:
    """Friendly versions of the CheckConstraints shared by tickets and guided visits."""
    p = []
    if (m.month is None) != (m.day is None):
        p.append("An annual date needs both a month and a day")
    if m.weekday is not None and m.month is not None:
        p.append("Choose a weekday or an annual date, not both")
    if m.holidays and (m.weekday is not None or m.month is not None):
        p.append("Public holidays can't be combined with a weekday or a date")
    if m.week_of_month is not None and m.weekday is None:
        p.append("A week of the month needs a weekday")
    if m.start_time and m.end_time and m.start_time >= m.end_time:
        p.append("Start time must be before end time")
    if (m.month_from is None) != (m.month_to is None):
        p.append("A season needs both a first and a last month")
    elif m.month_from is not None and m.month_from > m.month_to:
        p.append("A season can't wrap the new year: create two entries (e.g. Sep–Dec and Jan–Aug)")
    if (m.day_from is None) != (m.day_to is None):
        p.append("Season days: fill in both or neither")
    return p


class ScheduleValidationMixin:
    """Put before BaseView: shows schedule mistakes as one readable message."""

    def on_model_change(self, form, model, is_created):
        problems = schedule_problems(model)
        if problems:
            raise ValueError("; ".join(problems))
        super().on_model_change(form, model, is_created)