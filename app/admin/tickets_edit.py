"""Editing a museum's tickets (admin page).

Everything that decides what a submitted form *means* lives here, with no Flask
and no database access, so it can be tested on its own. tickets_admin.py only
loads the rows, calls these functions and saves the result.

A "ticket" in the admin is what you would say out loud: "Standard, 10 € from
January to August and 12 € from September to December". The database stores
one Ticket row per season, so one submitted form can create several rows
(one per season price). Editing changes exactly one row.

The checks mirror the CheckConstraints and unique constraints of models.Ticket,
so the admin sees a specific message ("Standard already exists for all year")
instead of an IntegrityError.
"""

import json
import re
from calendar import monthrange
from dataclasses import dataclass, field
from datetime import date, time
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from types import SimpleNamespace
from typing import Optional

from werkzeug.datastructures import MultiDict

from ..models import DurationUnit, EntryPolicy, Validity
from ..museums.exhibitions import exhibition_sort_key, is_archived
from ..museums.hours import ORDINALS, WEEKDAYS, rule_text
from ..museums.periods import FULL_MONTHS, period_of, period_sort_key, period_text
from ..museums.tickets import (
    _duration_text, _enum_value, _price_text, _time_window, audience_text,
)

CENT = Decimal("0.01")
MAX_PRICE = Decimal("999999.99")          # Numeric(8, 2)
SEASON_KEY = re.compile(r"^seasons-(\d+)-")
SEASON_FIELDS = ("price", "month_from", "day_from", "month_to", "day_to")


# --- Reading the form --------------------------------------------------------

class _Reader:
    """Typed access to form fields; problems are appended to `errors`."""

    def __init__(self, form, errors: list):
        self.form = form
        self.errors = errors

    def text(self, name: str, default: str = "") -> str:
        return (self.form.get(name) or default).strip()

    def integer(self, name: str, label: str, low=None, high=None) -> Optional[int]:
        """A whole number, or None when the field is empty (or invalid: then an error is added)."""
        raw = self.text(name)
        if not raw:
            return None
        try:
            value = int(raw)
        except ValueError:
            value = None
        if value is None or (low is not None and value < low) or (high is not None and value > high):
            if low is not None and high is not None:
                bounds = f" from {low} to {high}"
            elif low is not None:
                bounds = f" of at least {low}"
            else:
                bounds = ""
            self.errors.append(f"{label} must be a whole number{bounds}.")
            return None
        return value

    def clock(self, name: str, label: str) -> Optional[time]:
        raw = self.text(name)
        if not raw:
            return None
        try:
            return time.fromisoformat(raw)
        except ValueError:
            self.errors.append(f"{label} must be a valid time.")
            return None


def _number(raw: str, label: str, errors: list) -> Optional[Decimal]:
    """A decimal number. A comma works as the decimal separator ("2,8")."""
    try:
        value = Decimal(raw.strip().replace(",", "."))
    except InvalidOperation:
        value = None
    if value is None or not value.is_finite():
        errors.append(f"{label} must be a number, like 12.50.")
        return None
    return value


def parse_money(raw: str, label: str, errors: list, *, signed: bool = False) -> Optional[Decimal]:
    """A price with at most two decimals. `signed` allows a negative amount (for price changes)."""
    value = _number(raw, label, errors)
    if value is None:
        return None
    if abs(value) > MAX_PRICE:
        errors.append(f"{label} is too large.")
    elif value != value.quantize(CENT):
        errors.append(f"{label} can have at most two decimals.")
    elif value < 0 and not signed:
        errors.append(f"{label} can't be negative.")
    else:
        return value
    return None


def _season_text(period: tuple) -> str:
    return period_text(*period) or "All year"


@dataclass(frozen=True)
class Season:
    """One price, optionally limited to a yearly period (no wrapping over 1 January)."""
    price: Decimal
    month_from: Optional[int] = None
    day_from: Optional[int] = None
    month_to: Optional[int] = None
    day_to: Optional[int] = None

    @property
    def period(self) -> tuple:
        return (self.month_from, self.day_from, self.month_to, self.day_to)


def _read_seasons(form, errors: list) -> tuple[list[Season], int]:
    """The `seasons-<n>-<field>` rows. Returns (valid seasons, number of rows that were filled in)."""
    indexes = sorted({int(m.group(1)) for key in form if (m := SEASON_KEY.match(key))})
    filled = [
        i for i in indexes
        if any((form.get(f"seasons-{i}-{name}") or "").strip() for name in SEASON_FIELDS)
    ]
    seasons = []
    for n, i in enumerate(filled, start=1):
        problems: list[str] = []
        r = _Reader(form, problems)
        price = None
        if r.text(f"seasons-{i}-price"):
            price = parse_money(r.text(f"seasons-{i}-price"), "Price", problems)
        else:
            problems.append("Enter a price.")

        mf = r.integer(f"seasons-{i}-month_from", "First month", 1, 12)
        mt = r.integer(f"seasons-{i}-month_to", "Last month", 1, 12)
        df = r.integer(f"seasons-{i}-day_from", "First day", 1, 31)
        dt = r.integer(f"seasons-{i}-day_to", "Last day", 1, 31)
        if (mf is None) != (mt is None):
            problems.append("A season needs a first and a last month.")
        elif mf is not None and mf > mt:
            problems.append(
                "A season can't cross 1 January: enter two prices (for example Sep–Dec and Jan–Aug)."
            )
        if (df is None) != (dt is None):
            problems.append("Enter both season days, or neither.")
        if mf is None and df is not None:
            problems.append("Season days need a first and a last month.")
        if mf and df and df > monthrange(2024, mf)[1]:
            problems.append("The first day doesn't exist in that month.")
        if mt and dt and dt > monthrange(2024, mt)[1]:
            problems.append("The last day doesn't exist in that month.")
        if mf and mf == mt and df and dt and df > dt:
            problems.append("The season ends before it starts.")

        where = f"Price {n}: " if len(filled) > 1 else ""
        errors.extend(where + p for p in problems)
        if not problems:
            seasons.append(Season(price, mf, df, mt, dt))
    return seasons, len(filled)


@dataclass
class TicketInput:
    common: dict                  # column values shared by every row of this ticket
    seasons: list[Season]
    season_rows: int              # rows filled in (valid or not)
    exhibition_ids: list[int]
    errors: list[str]


def _enum(cls, raw: str, label: str, errors: list):
    try:
        return cls(raw)
    except ValueError:
        errors.append(f"Select a valid {label}.")
        return None


def parse_ticket_form(form, *, pass_ids: set) -> TicketInput:
    errors: list[str] = []
    r = _Reader(form, errors)

    label = r.text("label")
    if not label:
        errors.append("Enter a ticket label.")
    elif len(label) > 100:
        errors.append("The label can have at most 100 characters.")

    currency = r.text("currency", "EUR").upper()
    if not re.fullmatch(r"[A-Z]{3}", currency):
        errors.append("Currency must be a three-letter code, like EUR.")

    pass_id = r.integer("pass_id", "Museum pass", 1)
    if pass_id is not None and pass_id not in pass_ids:
        errors.append("That museum pass doesn't exist.")

    entry_policy = _enum(EntryPolicy, r.text("entry_policy", "anytime"), "entry policy", errors)

    validity = _enum(Validity, r.text("validity", "single_entry"), "validity", errors)
    validity_value = validity_unit = None
    if validity is Validity.period:
        validity_value = r.integer("validity_value", "Validity duration", 1)
        unit = r.text("validity_unit")
        validity_unit = DurationUnit(unit) if unit in {u.value for u in DurationUnit} else None
        if validity_value is None or validity_unit is None:
            errors.append("A ticket valid for a period needs a duration and a unit.")

    # Audience
    min_age = r.integer("min_age", "Minimum age", 0)
    max_age = r.integer("max_age", "Maximum age", 0)
    if min_age is not None and max_age is not None and min_age > max_age:
        errors.append("The minimum age can't be higher than the maximum age.")
    country = r.text("resident_country").upper() or None
    if country and not re.fullmatch(r"[A-Z]{2}", country):
        errors.append("Resident country must be a two-letter code, like PT.")
    municipality = r.text("resident_municipality") or None
    if municipality and len(municipality) > 100:
        errors.append("The municipality can have at most 100 characters.")

    # Schedule: only the fields of the chosen kind are read, the rest are ignored.
    kind = r.text("schedule_kind", "always")
    weekday = week_of_month = month = day = None
    holidays = False
    if kind == "weekday":
        if r.text("weekday"):
            weekday = r.integer("weekday", "Weekday", 0, 6)
        else:
            errors.append("Pick a weekday.")
        week_of_month = r.integer("week_of_month", "Week of the month", -1, 5)
        if week_of_month == 0:
            errors.append("Week of the month must be 1–5 or 'last'.")
    elif kind == "date":
        month = r.integer("month", "Month", 1, 12)
        day = r.integer("day", "Day", 1, 31)
        if not r.text("month") or not r.text("day"):
            errors.append("Pick a month and a day.")
        elif month and day and day > monthrange(2024, month)[1]:
            errors.append("That month doesn't have that many days.")
    elif kind == "holidays":
        holidays = True
    elif kind != "always":
        errors.append("Select a valid schedule.")

    start_time = r.clock("start_time", "Start time")
    end_time = r.clock("end_time", "End time")
    if start_time and end_time and start_time >= end_time:
        errors.append("The start time must be before the end time.")

    exhibition_ids = []
    for raw in form.getlist("exhibition_ids"):
        try:
            exhibition_ids.append(int(raw))
        except ValueError:
            errors.append("Invalid exhibition selection.")

    seasons, season_rows = _read_seasons(form, errors)

    common = {
        "label": label, "currency": currency, "notes": r.text("notes") or None,
        "pass_id": pass_id, "entry_policy": entry_policy, "validity": validity,
        "validity_value": validity_value, "validity_unit": validity_unit,
        "resident_country": country, "resident_municipality": municipality,
        "min_age": min_age, "max_age": max_age, "is_student": bool(form.get("is_student")),
        "weekday": weekday, "week_of_month": week_of_month, "month": month, "day": day,
        "holidays": holidays, "start_time": start_time, "end_time": end_time,
    }
    return TicketInput(common, seasons, season_rows, exhibition_ids, errors)


# --- Describing a ticket (the table and the preview) --------------------------

@dataclass
class RowView:
    id: Optional[int]
    label: str
    price: str            # "€12.00", "Free", "Included in pass"
    audience: str         # "Full price", "Ages 65+", "Lisboa Card"
    when: str             # "Every Sunday · 10:00–14:00", or "" when it always applies
    terms: str            # validity and entry policy, only when unusual
    exhibitions: str      # "All exhibitions", or the names
    archived: int         # linked exhibitions that are archived
    notes: str
    unlisted: bool        # the public page hides it: no current exhibition is linked


def _when_text(t) -> str:
    has_rule = t.weekday is not None or t.month is not None or bool(t.holidays)
    return " · ".join(p for p in (rule_text(t) if has_rule else "", _time_window(t)) if p)


def _terms_text(t) -> str:
    parts = []
    validity = _enum_value(t.validity) or "single_entry"
    if validity == "same_day":
        parts.append("Same day")
    elif validity == "period":
        parts.append("Valid " + _duration_text(t.validity_value or 1, _enum_value(t.validity_unit) or "days"))
    policy = _enum_value(t.entry_policy) or "anytime"
    if policy == "recommended":
        parts.append("Booking recommended")
    elif policy == "timed_slot":
        parts.append("Timed slot")
    return " · ".join(parts)


def row_view(t, linked, all_exhibitions, today: date) -> RowView:
    """Summarise a Ticket, or anything shaped like one (the preview uses a SimpleNamespace)."""
    current_all = [e for e in all_exhibitions if not is_archived(e, today)]
    current = [e for e in linked if not is_archived(e, today)]
    if not current:
        names = ""
    elif len(current_all) > 1 and {e.id for e in current} == {e.id for e in current_all}:
        names = "All exhibitions"
    else:
        names = ", ".join(e.name for e in sorted(current, key=exhibition_sort_key))
    return RowView(
        id=getattr(t, "id", None), label=t.label, price=_price_text(t),
        audience=audience_text(t), when=_when_text(t), terms=_terms_text(t),
        exhibitions=names, archived=len(linked) - len(current), notes=t.notes or "",
        unlisted=not current,
    )


@dataclass
class Group:
    key: str
    title: str            # "All year", "1 Jan – 31 Aug"
    rows: list[RowView]


def build_table(tickets, exhibitions, today: date) -> list[Group]:
    """Tickets grouped by season (year-round first), alphabetical inside each group."""
    ordered = sorted(
        tickets, key=lambda t: (period_sort_key(period_of(t)), t.label.casefold(), t.price)
    )
    groups: dict[tuple, Group] = {}
    for t in ordered:
        period = period_of(t)
        group = groups.setdefault(period, Group(f"g{len(groups)}", _season_text(period), []))
        group.rows.append(row_view(t, t.exhibitions, exhibitions, today))
    return list(groups.values())


def form_values(t) -> dict:
    """A ticket as the form's field values (strings), so the modal can be filled by script."""
    def s(value):
        return "" if value is None else str(value)

    kind = ("weekday" if t.weekday is not None else "date" if t.month is not None
            else "holidays" if t.holidays else "always")
    return {
        "label": t.label, "currency": t.currency or "EUR", "pass_id": s(t.pass_id),
        "notes": t.notes or "",
        "entry_policy": _enum_value(t.entry_policy) or "anytime",
        "validity": _enum_value(t.validity) or "single_entry",
        "validity_value": s(t.validity_value), "validity_unit": _enum_value(t.validity_unit) or "",
        "min_age": s(t.min_age), "max_age": s(t.max_age),
        "resident_country": t.resident_country or "",
        "resident_municipality": t.resident_municipality or "",
        "is_student": bool(t.is_student),
        "schedule_kind": kind, "weekday": s(t.weekday), "week_of_month": s(t.week_of_month),
        "month": s(t.month), "day": s(t.day),
        "start_time": f"{t.start_time:%H:%M}" if t.start_time else "",
        "end_time": f"{t.end_time:%H:%M}" if t.end_time else "",
        "exhibition_ids": [e.id for e in t.exhibitions],
        "season": {
            "price": f"{t.price:.2f}", "month_from": s(t.month_from), "day_from": s(t.day_from),
            "month_to": s(t.month_to), "day_to": s(t.day_to),
        },
    }


def tickets_context(museum, passes, today: date) -> dict:
    """Template variables for the tickets panel (prefixed so they can't clash with the edit page's)."""
    exhibitions = sorted(museum.exhibitions, key=exhibition_sort_key)
    groups = build_table(museum.tickets, exhibitions, today)
    return dict(
        tickets_groups=groups,
        tickets_count=len(museum.tickets),
        tickets_unlisted=sum(row.unlisted for g in groups for row in g.rows),
        tickets_data={
            "tickets": {t.id: form_values(t) for t in museum.tickets},
            "defaultExhibitions": [e.id for e in exhibitions if not is_archived(e, today)],
        },
        ticket_passes=passes,
        ticket_exhibitions=[
            SimpleNamespace(id=e.id, name=e.name, archived=is_archived(e, today)) for e in exhibitions
        ],
        ticket_weekdays=WEEKDAYS,
        ticket_ordinals=ORDINALS,
        ticket_months=FULL_MONTHS,
    )


# --- Adding and editing one ticket ---------------------------------------------

@dataclass
class PlannedRow:
    status: str                   # "new" | "update"
    values: dict                  # Ticket columns for this row
    target: Optional[object]      # the existing Ticket when updating
    view: RowView


@dataclass
class Plan:
    rows: list[PlannedRow] = field(default_factory=list)
    exhibitions: list = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def can_save(self) -> bool:
        return bool(self.rows) and not self.errors


def plan_ticket(form, *, museum_id, tickets, exhibitions, passes, today: date,
                editing_id: Optional[int] = None) -> Plan:
    """Turn the form into the rows to create (or the one row to update). Saves nothing."""
    pass_by_id = {p.id: p for p in passes}
    parsed = parse_ticket_form(form, pass_ids=set(pass_by_id))
    plan = Plan(errors=list(parsed.errors))

    by_id = {e.id: e for e in exhibitions}
    wanted = list(dict.fromkeys(parsed.exhibition_ids))
    plan.exhibitions = [by_id[i] for i in wanted if i in by_id]
    if len(plan.exhibitions) != len(wanted):
        plan.errors.append("Choose exhibitions of this museum only.")

    target = None
    if editing_id is not None:
        target = next((t for t in tickets if t.id == editing_id), None)
        if target is None:
            plan.errors.append("That ticket no longer exists. Reload the page.")
        elif parsed.season_rows > 1:
            plan.errors.append("Editing changes one ticket: use one price row.")
    if parsed.season_rows == 0:
        plan.errors.append("Enter a price.")

    # A label can be reused only for different periods (uq_ticket_museum_label_period and the
    # year-round index). Check here, against the stored rows and against this form's own rows.
    label = parsed.common["label"]
    taken = {
        (t.label, period_of(t)) for t in tickets if target is None or t.id != target.id
    }
    for season in parsed.seasons:
        key = (label, season.period)
        if label and key in taken:
            plan.errors.append(f'"{label}" already exists for {_season_text(season.period).lower()}.')
        taken.add(key)

    if plan.errors:
        return plan

    for season in parsed.seasons:
        values = {
            **parsed.common, "price": season.price, "month_from": season.month_from,
            "day_from": season.day_from, "month_to": season.month_to, "day_to": season.day_to,
        }
        shown = SimpleNamespace(**values, museum_pass=pass_by_id.get(values["pass_id"]))
        plan.rows.append(PlannedRow(
            "update" if target is not None else "new", values, target,
            row_view(shown, plan.exhibitions, exhibitions, today),
        ))
    if plan.rows and plan.rows[0].view.unlisted:
        plan.warnings.append(
            "No current exhibition is selected, so visitors won't see this ticket on the museum page."
        )
    return plan


# --- Creating several tickets from the same form -------------------------------

def plan_ticket_batch(form, *, museum_id, tickets, exhibitions, passes, today: date) -> Plan:
    """Plan one or more ticket definitions, sharing all non-row settings and seasons."""
    raw_rows = form.get("ticket_rows", "")
    try:
        ticket_rows = json.loads(raw_rows)
    except (TypeError, ValueError):
        return Plan(errors=["The ticket rows could not be read. Please try again."])

    if not isinstance(ticket_rows, list) or not ticket_rows:
        return Plan(errors=["Add at least one ticket."])
    if len(ticket_rows) > 100:
        return Plan(errors=["You can create at most 100 tickets at once."])

    season_indexes = sorted({
        int(match.group(1))
        for key in form
        if (match := SEASON_KEY.match(key))
    })
    if not season_indexes:
        return Plan(errors=["Add at least one season period."])

    plan = Plan()
    seen = set()

    for index, item in enumerate(ticket_rows, start=1):
        if not isinstance(item, dict):
            plan.errors.append(f"Ticket {index}: invalid ticket row.")
            continue

        # Keep every shared field (including repeated exhibition_ids), then replace
        # the fields that belong to this individual ticket.
        row_form = MultiDict(form.items(multi=True))
        row_form["label"] = str(item.get("label") or "")
        row_form["pass_id"] = "" if item.get("pass_id") is None else str(item.get("pass_id"))
        row_form["min_age"] = "" if item.get("min_age") is None else str(item.get("min_age"))
        row_form["max_age"] = "" if item.get("max_age") is None else str(item.get("max_age"))
        row_form["resident_country"] = "" if item.get("resident_country") is None else str(item.get("resident_country"))
        row_form["resident_municipality"] = "" if item.get("resident_municipality") is None else str(item.get("resident_municipality"))
        row_form["is_student"] = "1" if item.get("is_student") else ""

        # A ticket's single price is applied to every shared season period.
        row_price = "" if item.get("price") is None else str(item.get("price"))
        for season_index in season_indexes:
            row_form[f"seasons-{season_index}-price"] = row_price

        row_plan = plan_ticket(
            row_form, museum_id=museum_id, tickets=tickets, exhibitions=exhibitions,
            passes=passes, today=today,
        )
        plan.exhibitions = row_plan.exhibitions

        prefix = f"Ticket {index}"
        label = str(item.get("label") or "").strip()
        if label:
            prefix += f' ("{label[:100]}")'
        plan.errors.extend(f"{prefix}: {error}" for error in row_plan.errors)
        plan.warnings.extend(f"{prefix}: {warning}" for warning in row_plan.warnings)

        for planned in row_plan.rows:
            key = (planned.values["label"], (
                planned.values["month_from"], planned.values["day_from"],
                planned.values["month_to"], planned.values["day_to"],
            ))
            if key in seen:
                plan.errors.append(
                    f'{prefix}: "{planned.values["label"]}" is duplicated in this batch '
                    f'for {_season_text(key[1]).lower()}.'
                )
            seen.add(key)
            plan.rows.append(planned)

    # A batch is all-or-nothing: never let a partially valid batch be saved.
    if plan.errors:
        plan.rows.clear()
    return plan



# --- Changing several tickets at once -------------------------------------------

PRICE_MODES = {"set", "percent", "add"}
EXHIBITION_MODES = {"add", "remove", "replace"}


@dataclass
class PriceChange:
    ticket: object
    label: str
    season: str
    old: Decimal
    new: Decimal


def plan_price_change(tickets, mode: str, raw: str) -> tuple[list[PriceChange], list[str]]:
    """New prices for the selected tickets. Saves nothing; changes nothing if any would be invalid."""
    errors: list[str] = []
    if mode not in PRICE_MODES:
        return [], ["Choose how to change the price."]
    if not tickets:
        return [], ["Select at least one ticket."]
    if not raw.strip():
        return [], ["Enter an amount."]

    if mode == "percent":
        amount = _number(raw, "The percentage", errors)
        if amount is not None and amount <= -100:
            errors.append("The percentage must be above -100.")
    else:
        amount = parse_money(raw, "The amount", errors, signed=(mode == "add"))
    if errors:
        return [], errors

    changes = []
    for t in tickets:
        if mode == "set":
            new = amount
        elif mode == "percent":
            new = (t.price * (100 + amount) / 100).quantize(CENT, ROUND_HALF_UP)
        else:
            new = (t.price + amount).quantize(CENT, ROUND_HALF_UP)
        name = f'"{t.label}" ({_season_text(period_of(t)).lower()})'
        if new < 0:
            errors.append(f"{name} would cost less than zero.")
        elif new > MAX_PRICE:
            errors.append(f"{name} would cost too much.")
        elif new != t.price:
            changes.append(PriceChange(t, t.label, _season_text(period_of(t)), t.price, new))
    if not errors and not changes:
        errors.append("No price would change.")
    return changes, errors


# Groups of fields the bulk editor can change. A group is applied only when it is ticked;
# everything else on each ticket (including its price) stays as it is.
# group -> form field names (what parse_ticket_form reads)
BULK_FORM_FIELDS = {
    "label": ("label",),
    "pass": ("pass_id",),
    "currency": ("currency",),
    "notes": ("notes",),
    "entry": ("entry_policy",),
    "validity": ("validity", "validity_value", "validity_unit"),
    "audience": ("min_age", "max_age", "resident_country", "resident_municipality", "is_student"),
    "schedule": ("schedule_kind", "weekday", "week_of_month", "month", "day", "start_time", "end_time"),
    "period": ("month_from", "day_from", "month_to", "day_to"),
}
# group -> Ticket columns it writes
BULK_COLUMNS = {
    "label": ("label",),
    "pass": ("pass_id",),
    "currency": ("currency",),
    "notes": ("notes",),
    "entry": ("entry_policy",),
    "validity": ("validity", "validity_value", "validity_unit"),
    "audience": ("min_age", "max_age", "resident_country", "resident_municipality", "is_student"),
    "schedule": ("weekday", "week_of_month", "month", "day", "holidays", "start_time", "end_time"),
    "period": ("month_from", "day_from", "month_to", "day_to"),
}


@dataclass
class TicketEdit:
    ticket: object
    label: str
    season: str
    changes: list            # (what, old text, new text)
    values: dict             # the columns to write


def _ticket_form(t) -> MultiDict:
    """A stored ticket as a submitted form, so it goes through the same checks as a typed one."""
    base = MultiDict()
    for key, value in form_values(t).items():
        if key == "exhibition_ids":
            for i in value:
                base.add(key, str(i))
        elif key == "season":
            for name, v in value.items():
                base[f"seasons-0-{name}"] = v
        elif key == "is_student":
            base[key] = "1" if value else ""
        else:
            base[key] = value
    return base


def plan_bulk_edit(form, selected, *, tickets, exhibitions, passes, today: date) -> tuple[list[TicketEdit], list[str]]:
    """Change the ticked field groups on the selected tickets. Saves nothing; all or nothing."""
    groups = [g for g in BULK_FORM_FIELDS if g in form.getlist("bulk_groups")]
    if not groups:
        return [], ["Tick what you want to change."]

    pass_by_id = {p.id: p for p in passes}
    problems: dict[str, list[str]] = {}
    planned = []                                   # (ticket, all column values)
    for t in selected:
        base = _ticket_form(t)
        for group in groups:
            for name in BULK_FORM_FIELDS[group]:
                target = f"seasons-0-{name}" if group == "period" else name
                if name == "is_student":
                    base[target] = "1" if form.get("set_is_student") else ""
                else:
                    base[target] = form.get(f"set_{name}", "")
        parsed = parse_ticket_form(base, pass_ids=set(pass_by_id))
        label = f'"{t.label}" ({_season_text(period_of(t)).lower()})'
        for error in parsed.errors:
            problems.setdefault(error, []).append(label)
        if parsed.errors or len(parsed.seasons) != 1:
            continue
        season = parsed.seasons[0]
        planned.append((t, {
            **parsed.common, "price": t.price, "month_from": season.month_from,
            "day_from": season.day_from, "month_to": season.month_to, "day_to": season.day_to,
        }))

    # Report each problem once; name the tickets only when it doesn't concern all of them.
    errors = []
    for message, names in problems.items():
        if len(names) == len(selected):
            errors.append(message)
        else:
            more = "…" if len(names) > 3 else ""
            errors.append(f"{message} ({', '.join(names[:3])}{more})")
    if errors:
        return [], errors

    # Same rule as plan_ticket: a label can be reused only for different periods.
    selected_ids = {t.id for t in selected}
    taken = {(t.label, period_of(t)) for t in tickets if t.id not in selected_ids}
    for t, values in planned:
        period = (values["month_from"], values["day_from"], values["month_to"], values["day_to"])
        if (values["label"], period) in taken:
            message = f'"{values["label"]}" would already exist for {_season_text(period).lower()}.'
            if message not in errors:
                errors.append(message)
        taken.add((values["label"], period))
    if errors:
        return [], errors

    edits = []
    for t, values in planned:
        columns = [c for g in groups for c in BULK_COLUMNS[g]]
        new = {c: values[c] for c in columns}
        if all(getattr(t, c) == new[c] for c in columns):
            continue
        shown = SimpleNamespace(**values, museum_pass=pass_by_id.get(values["pass_id"]))
        before = row_view(t, t.exhibitions, exhibitions, today)
        after = row_view(shown, t.exhibitions, exhibitions, today)
        changes = []
        old_season = _season_text(period_of(t))
        new_season = _season_text((values["month_from"], values["day_from"], values["month_to"], values["day_to"]))
        if old_season != new_season:
            changes.append(("Season", old_season, new_season))
        for what, attr in (("Ticket", "label"), ("Price", "price"), ("Who", "audience"),
                           ("When", "when"), ("Terms", "terms"), ("Notes", "notes")):
            old, now = getattr(before, attr), getattr(after, attr)
            if old != now:
                changes.append((what, old or "—", now or "—"))
        edits.append(TicketEdit(t, t.label, old_season, changes, new))
    if not edits:
        return [], ["Nothing would change."]
    return edits, []


def change_exhibitions(tickets, mode: str, exhibitions: list) -> int:
    """Add, remove or replace linked exhibitions. Returns how many tickets changed."""
    changed = 0
    for t in tickets:
        current = list(t.exhibitions)
        if mode == "add":
            new = current + [e for e in exhibitions if e not in current]
        elif mode == "remove":
            new = [e for e in current if e not in exhibitions]
        else:
            new = list(exhibitions)
        if {e.id for e in new} != {e.id for e in current}:
            t.exhibitions = new
            changed += 1
    return changed
