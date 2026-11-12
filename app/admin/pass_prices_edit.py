"""Bulk editing of a pass's prices (admin page). Same idea as hours_edit.py.

The admin gives the durations once ("24h, 48h, 72h") and one line per
audience with its prices in the same order ("31 / 51 / 62"). expand_rows()
turns that into one PassPrice per audience x duration. Nothing here talks to
the database: the caller passes the pass's existing rows and gets back unsaved
PassPrice objects plus a list of errors.
"""

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from ..models import DurationUnit, PassPrice
from ..museums.tickets import UNIT_HOURS, _age_phrase, _duration_text, _money

_UNITS = {
    "h": "hours", "hour": "hours", "hours": "hours",
    "d": "days", "day": "days", "days": "days",
    "m": "months", "month": "months", "months": "months",
    "y": "years", "year": "years", "years": "years",
}
_DURATION = re.compile(r"^(\d+)\s*([a-z]+)$")
_ROW_KEY = re.compile(r"^rows-(\d+)-")
CENT = Decimal("0.01")


# --- What the form sends ---------------------------------------------------

@dataclass
class RowInput:
    """One audience line of the form, kept as raw strings so it can be shown again."""
    label: str = ""
    prices: str = ""          # "31 / 51 / 62", one per duration
    min_age: str = ""
    max_age: str = ""
    student: bool = False
    country: str = ""
    municipality: str = ""
    notes: str = ""

    @property
    def is_blank(self) -> bool:
        return not any((self.label, self.prices, self.min_age, self.max_age,
                        self.student, self.country, self.municipality, self.notes))


def parse_form(form):
    """Returns (durations_text, currency, rows). Row numbers may have gaps."""
    indexes = sorted({int(m.group(1)) for key in form if (m := _ROW_KEY.match(key))})
    rows = []
    for i in indexes:
        def get(name, i=i):
            return form.get(f"rows-{i}-{name}", "").strip()
        row = RowInput(
            label=get("label"), prices=get("prices"),
            min_age=get("min_age"), max_age=get("max_age"),
            student=bool(form.get(f"rows-{i}-student")),
            country=get("country").upper(), municipality=get("municipality"),
            notes=get("notes"),
        )
        if not row.is_blank:
            rows.append(row)
    return (form.get("durations", "").strip(),
            (form.get("currency", "").strip() or "EUR").upper(), rows)


# --- Parsing helpers -----------------------------------------------------------

def parse_durations(text, errors):
    result = []
    for part in re.split(r"[,;]", text or ""):
        part = part.strip().lower()
        if not part:
            continue
        m = _DURATION.match(part)
        unit = _UNITS.get(m.group(2)) if m else None
        if not m or unit is None or int(m.group(1)) == 0:
            errors.append(f"'{part}' is not a valid duration (try 24h, 3 days, 1 year)")
        elif (int(m.group(1)), DurationUnit(unit)) in result:
            errors.append(f"Duration '{part}' appears twice")
        else:
            result.append((int(m.group(1)), DurationUnit(unit)))
    if not result and not errors:
        errors.append("Enter at least one duration, e.g. 24h, 48h, 72h")
    return result


def _price(text, errors, where):
    try:
        value = Decimal(text.strip().replace(",", ".")).quantize(CENT, ROUND_HALF_UP)
    except InvalidOperation:
        errors.append(f"{where}: '{text.strip()}' is not a valid price")
        return None
    if value < 0:
        errors.append(f"{where}: a price can't be negative")
        return None
    return value


def _age(value, label, errors):
    if not value:
        return None
    try:
        number = int(value)
    except ValueError:
        number = -1
    if number < 0:
        errors.append(f"{label} must be a whole number, 0 or more")
        return None
    return number


# --- Turning the form into rows ------------------------------------------------

@dataclass
class RowText:
    label: str
    duration: str      # "24 hours"
    price: str         # "€31.00"
    who: str           # "Ages 16+", "Student", ...
    notes: str


def _who(p) -> str:
    parts = []
    if p.is_student:
        parts.append("Student")
    if p.resident_municipality:
        parts.append(f"Residents of {p.resident_municipality}")
    elif p.resident_country:
        parts.append(f"Residents ({p.resident_country})")
    age = _age_phrase(p.min_age, p.max_age)
    if age:
        parts.append(f"ages {age}")
    return ", ".join(parts)


def describe(p) -> RowText:
    return RowText(
        label=p.label,
        duration=_duration_text(p.duration_value, p.duration_unit.value),
        price=_money(p.price, p.currency),
        who=_who(p), notes=p.notes or "",
    )


def _identity(p) -> tuple:
    # The database's unique key: the same label can exist for different durations.
    return (p.label, p.duration_value, p.duration_unit)


@dataclass
class NewRow:
    row: PassPrice
    text: RowText
    is_duplicate: bool = False
    warning: str = ""


@dataclass
class Expansion:
    rows: list[NewRow] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def to_add(self) -> list:
        return [r.row for r in self.rows if not r.is_duplicate]

    @property
    def duplicate_count(self) -> int:
        return sum(r.is_duplicate for r in self.rows)

    @property
    def can_save(self) -> bool:
        return not self.errors and bool(self.to_add)


def expand_rows(durations_text, currency, rows, pass_id, existing) -> Expansion:
    result = Expansion()
    durations = parse_durations(durations_text, result.errors)
    if not rows:
        result.errors.append("Add at least one audience line")
    if len(currency) != 3:
        result.errors.append("Currency must be a 3-letter code, e.g. EUR")
    if result.errors:
        return result

    by_identity = {_identity(p): p for p in existing}
    seen = set(by_identity)

    for n, r in enumerate(rows, start=1):
        errors = []
        where = f"Line {n}"
        if not r.label:
            errors.append(f"{where}: enter who it is for (e.g. Adult)")
        prices = [p for p in re.split(r"/", r.prices) if p.strip()]
        if len(prices) != len(durations):
            errors.append(f"{where}: {len(durations)} price(s) expected (one per duration, "
                          f"separated by /), found {len(prices)}")
        min_age = _age(r.min_age, f"{where}: minimum age", errors)
        max_age = _age(r.max_age, f"{where}: maximum age", errors)
        if min_age is not None and max_age is not None and min_age > max_age:
            errors.append(f"{where}: minimum age is above the maximum age")
        if r.country and len(r.country) != 2:
            errors.append(f"{where}: country must be a 2-letter code, e.g. PT")
        values = [_price(p, errors, where) for p in prices] if len(prices) == len(durations) else []
        if errors:
            result.errors.extend(errors)
            continue

        for (value, unit), price in zip(durations, values):
            row = PassPrice(
                pass_id=pass_id, label=r.label, duration_value=value, duration_unit=unit,
                price=price, currency=currency, notes=r.notes or None,
                min_age=min_age, max_age=max_age, is_student=r.student,
                resident_country=r.country or None,
                resident_municipality=r.municipality or None,
            )
            duplicate = _identity(row) in seen
            seen.add(_identity(row))
            warning = ""
            old = by_identity.get(_identity(row))
            if duplicate and old is not None and old.price != price:
                warning = (f"Exists with price {_money(old.price, old.currency)}: skipped. "
                           "Use 'Change the selected rows' below to update it.")
            result.rows.append(NewRow(row, describe(row), duplicate, warning))
    return result


# --- Existing rows -----------------------------------------------------------------

@dataclass
class ExistingRow:
    id: int
    text: RowText


def _sort_key(p):
    return (p.min_age or 0, p.label, p.duration_value * UNIT_HOURS[p.duration_unit.value])


def existing_rows(rows) -> list[ExistingRow]:
    return [ExistingRow(p.id, describe(p)) for p in sorted(rows, key=_sort_key)]


def prices_context(museum_pass, rows=None, durations="", currency="EUR") -> dict:
    """Template variables for the panel (prefixed so they can't clash with the edit page's)."""
    return dict(
        prices_rows=rows or [RowInput()],
        prices_blank=RowInput(),
        prices_existing=existing_rows(museum_pass.prices),
        prices_durations=durations,
        prices_currency=currency,
    )


def bulk_update(rows, form):
    """Set a price, change prices by a percentage, and/or set notes. Returns (count, errors)."""
    errors: list[str] = []
    fixed_text = form.get("bulk_price", "").strip()
    percent_text = form.get("bulk_percent", "").strip()
    notes = form.get("bulk_notes", "").strip()

    fixed = _price(fixed_text, errors, "New price") if fixed_text else None
    percent = None
    if percent_text:
        try:
            percent = Decimal(percent_text.replace(",", "."))
        except InvalidOperation:
            errors.append(f"Percentage: '{percent_text}' is not a number")
    if fixed_text and percent_text:
        errors.append("Use either a new price or a percentage, not both")
    if not errors and fixed is None and percent is None and not notes:
        errors.append("Fill in at least one field to change")
    if errors:
        return 0, errors

    plan = []
    for p in rows:
        new = p.price
        if fixed is not None:
            new = fixed
        elif percent is not None:
            new = (p.price * (Decimal(100) + percent) / 100).quantize(CENT, ROUND_HALF_UP)
        if new < 0:
            errors.append(f"{p.label} ({describe(p).duration}): the price would be negative")
        plan.append((p, new))
    if errors:
        return 0, errors

    for p, new in plan:
        p.price = new
        if notes:
            p.notes = notes
    return len(plan), []