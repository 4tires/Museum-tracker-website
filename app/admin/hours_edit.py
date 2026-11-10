"""Bulk editing of a museum's opening hours (admin page).

The database stores one OpeningHours row per weekday / date / holiday, but
nobody wants to type seven rows for "Tuesday to Sunday, 10:00-18:00". So the
admin fills in *rules*, and expand_rules() turns each rule into the rows the
database needs:

    rule  "Tue-Sun, 10:00-18:00, last entry 17:30"
      ->  six OpeningHours rows (one per weekday)

Nothing here talks to the database. The caller passes in the museum's existing
rows and gets back unsaved OpeningHours objects plus a list of errors, so the
same result can be shown as a preview or saved, and the logic can be tested
without a database. The checks mirror the CheckConstraints in models.py, so the
admin sees a friendly message instead of an IntegrityError.
"""

import re
from calendar import month_name, monthrange
from collections import Counter
from dataclasses import dataclass, field
from datetime import time

from ..models import OpeningHours
from ..museums.hours import WEEKDAYS, _fmt_hours, rule_text
from ..museums.periods import period_of, period_sort_key, period_text


# --- Labels for the form ----------------------------------------------------

ORDINALS = {1: "First", 2: "Second", 3: "Third", 4: "Fourth", 5: "Fifth", -1: "Last"}
MONTHS_FULL = list(month_name)[1:]


def hours_context(museum, rules=None) -> dict:
    """Template variables the hours panel needs (prefixed so they can't clash with the edit page's)."""
    return dict(
        hours_rules=rules or [RuleInput()],
        hours_blank=RuleInput(),
        hours_existing=existing_rows(museum.opening_hours),
        hours_weekdays=WEEKDAYS,
        hours_months=MONTHS_FULL,
        hours_ordinals=ORDINALS,
    )


# --- What the form sends ---------------------------------------------------

@dataclass
class RuleInput:
    """One rule block of the form, kept as raw strings so it can be shown again."""
    kind: str = "weekly"                  # "weekly" | "date" | "holidays"
    days: list[str] = field(default_factory=list)   # weekday numbers, "0" = Monday
    week_of_month: str = ""               # "", "1".."5", "-1" (last)
    month: str = ""                       # kind == "date"
    day: str = ""
    closed: bool = False
    start_time: str = ""
    end_time: str = ""
    last_entry: str = ""
    month_from: str = ""                  # optional yearly period
    day_from: str = ""
    month_to: str = ""
    day_to: str = ""
    is_special: bool = False
    label: str = ""
    notes: str = ""

    @property
    def is_blank(self) -> bool:
        # The untouched rule block that is always on the page.
        return self.kind == "weekly" and not any(
            (self.days, self.closed, self.start_time, self.end_time, self.last_entry,
             self.month_from, self.month_to, self.label, self.notes)
        )


_RULE_KEY = re.compile(r"^rules-(\d+)-")


def parse_rules(form) -> list[RuleInput]:
    """Read the rules-<n>-<field> inputs. The numbers may have gaps (a rule was removed)."""
    indexes = sorted({int(m.group(1)) for key in form if (m := _RULE_KEY.match(key))})
    rules = []
    for i in indexes:
        def get(name, i=i):
            return form.get(f"rules-{i}-{name}", "").strip()

        rule = RuleInput(
            kind=get("kind") or "weekly",
            days=form.getlist(f"rules-{i}-days"),
            week_of_month=get("week_of_month"),
            month=get("month"), day=get("day"),
            closed=bool(form.get(f"rules-{i}-closed")),
            start_time=get("start_time"), end_time=get("end_time"), last_entry=get("last_entry"),
            month_from=get("month_from"), day_from=get("day_from"),
            month_to=get("month_to"), day_to=get("day_to"),
            is_special=bool(form.get(f"rules-{i}-is_special")),
            label=get("label"), notes=get("notes"),
        )
        if not rule.is_blank:
            rules.append(rule)
    return rules


# --- Turning a rule into rows ------------------------------------------------

def _time(value, label, errors):
    if not value:
        return None
    try:
        return time.fromisoformat(value)
    except ValueError:
        errors.append(f"{label}: '{value}' is not a valid time")
        return None


def _int(value, label, errors, low, high):
    if value in ("", None):
        return None
    try:
        number = int(value)
    except ValueError:
        number = None
    if number is None or not low <= number <= high:
        errors.append(f"{label} must be a number from {low} to {high}")
        return None
    return number


def _expand_rule(rule: RuleInput, errors: list):
    """One rule -> list of column-value dicts (one per row). Appends to errors."""
    # Times
    start = _time(rule.start_time, "Start time", errors)
    end = _time(rule.end_time, "End time", errors)
    last = _time(rule.last_entry, "Last entry", errors)
    if rule.closed:
        if start is not None or end is not None or last is not None:
            errors.append("A closed rule can't have times (untick 'Closed' or clear the times)")
    elif start is None or end is None:
        errors.append("Enter a start and an end time, or tick 'Closed'")
    else:
        if start >= end:
            errors.append("Start time must be before end time")
        if last is not None and not start <= last <= end:
            errors.append("Last entry must be between the start and end time")

    # Yearly period (same rules as the CheckConstraints: no wrapping over 1 Jan)
    month_from = _int(rule.month_from, "Period: first month", errors, 1, 12)
    month_to = _int(rule.month_to, "Period: last month", errors, 1, 12)
    day_from = _int(rule.day_from, "Period: first day", errors, 1, 31)
    day_to = _int(rule.day_to, "Period: last day", errors, 1, 31)
    if (month_from is None) != (month_to is None):
        errors.append("A period needs both a first and a last month")
    elif month_from is not None and month_from > month_to:
        errors.append("A period can't wrap the new year: use two rules (e.g. Nov-Dec and Jan-Mar)")
    if (day_from is None) != (day_to is None):
        errors.append("Period days: fill in both or neither")
    if day_from is not None and month_from is None:
        errors.append("Period days need a first and last month")

    # Which rows does the rule create?
    targets: list[dict] = []
    if rule.kind == "weekly":
        days = {d for d in (_int(x, "Weekday", errors, 0, 6) for x in rule.days) if d is not None}
        week = _int(rule.week_of_month, "Week of the month", errors, -1, 5)
        if week == 0:
            errors.append("Week of the month must be 1-5 or 'last'")
            week = None
        if not days:
            errors.append("Pick at least one weekday")
        targets = [{"weekday": d, "week_of_month": week} for d in sorted(days)]
    elif rule.kind == "date":
        month = _int(rule.month, "Month", errors, 1, 12)
        day = _int(rule.day, "Day", errors, 1, 31)
        if month is None or day is None:
            errors.append("Pick a month and a day")
        elif day > monthrange(2024, month)[1]:   # 2024: a leap year, so 29 Feb is allowed
            errors.append("That month doesn't have that many days")
        else:
            targets = [{"month": month, "day": day}]
    elif rule.kind == "holidays":
        targets = [{"holidays": True}]
    else:
        errors.append("Unknown rule type")

    base = dict(
        weekday=None, week_of_month=None, month=None, day=None, holidays=False,
        month_from=month_from, day_from=day_from, month_to=month_to, day_to=day_to,
        is_closed=rule.closed,
        start_time=None if rule.closed else start,
        end_time=None if rule.closed else end,
        last_entry=None if rule.closed else last,
        is_special=rule.is_special,
        label=rule.label or None,
        notes=rule.notes or None,
    )
    return [{**base, **target} for target in targets]


# --- Describing rows (reuses the formatting helpers of hours.py) ---------------

@dataclass
class RowText:
    when: str          # "Every Tuesday", "25 Dec", "Public holidays"
    period: str        # "1 Apr – 31 Aug" or ""
    hours: str         # "10:00–18:00" or "Closed"
    last_entry: str
    label: str
    notes: str


def describe(h) -> RowText:
    hours, last_entry = _fmt_hours(h)
    return RowText(
        when=rule_text(h), period=period_text(*period_of(h)),
        hours=hours, last_entry=last_entry, label=h.label or "", notes=h.notes or "",
    )


@dataclass
class ExistingRow:
    id: int
    text: RowText


def _edit_sort_key(h):
    return (
        1 if (h.month or h.holidays) else 0,       # weekly rows first, dates/holidays after
        period_sort_key(period_of(h)),
        h.month or 0, h.day or 0,
        h.weekday if h.weekday is not None else 9,
        h.week_of_month or 0,
        h.start_time or time.min,
    )


def existing_rows(rows) -> list[ExistingRow]:
    return [ExistingRow(h.id, describe(h)) for h in sorted(rows, key=_edit_sort_key)]


# --- Preview / save --------------------------------------------------------------

def _identity(h) -> tuple:
    """Two rows with the same identity say the same thing (label and notes don't count)."""
    return (h.weekday, h.week_of_month, h.month, h.day, bool(h.holidays), *period_of(h),
            bool(h.is_closed), h.start_time, h.end_time)


def _slot(h):
    """(weekday, period) for a plain weekly row, else None. Used to warn about a second slot."""
    plain = (h.weekday is not None and h.week_of_month is None and h.month is None
             and not h.holidays and not h.is_special)
    return (h.weekday, period_of(h)) if plain else None


@dataclass
class NewRow:
    row: OpeningHours          # not added to the session until the caller saves it
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


def expand_rules(rules, museum_id: int, existing) -> Expansion:
    result = Expansion()
    if not rules:
        result.errors.append("Add at least one rule")
        return result

    seen = {_identity(h) for h in existing}
    slots = Counter(s for s in map(_slot, existing) if s)

    for n, rule in enumerate(rules, start=1):
        errors: list[str] = []
        for values in _expand_rule(rule, errors):
            row = OpeningHours(museum_id=museum_id, **values)
            duplicate = _identity(row) in seen
            seen.add(_identity(row))

            warning = ""
            slot = _slot(row)
            if slot and not duplicate:
                if slots[slot]:
                    warning = (f"{WEEKDAYS[row.weekday]} already has hours in this period, so this "
                               "adds a second opening slot. Delete the old row to replace it.")
                slots[slot] += 1
            result.rows.append(NewRow(row, describe(row), duplicate, warning))
        result.errors.extend(f"Rule {n}: {e}" for e in errors)
    return result


# --- Changing several existing rows at once ------------------------------------------

def _row_name(h) -> str:
    text = describe(h)
    return f"{text.when} {text.period}".strip()


def bulk_update(rows, form):
    """Apply the 'change selected' fields to rows. Returns (count, errors).

    Only the filled-in fields change. Times apply to open rows (a closed row has
    no times); notes apply to every selected row. Nothing is changed if any
    row would end up invalid.
    """
    errors: list[str] = []
    start = _time(form.get("bulk_start", "").strip(), "Start time", errors)
    end = _time(form.get("bulk_end", "").strip(), "End time", errors)
    last = _time(form.get("bulk_last_entry", "").strip(), "Last entry", errors)
    notes = form.get("bulk_notes", "").strip()
    clear_last = form.get("bulk_clear_last_entry") == "1"

    if not errors and start is None and end is None and last is None and not notes and not clear_last:
        errors.append("Fill in at least one field to change")
    if errors:
        return 0, errors

    plan = []
    for h in rows:
        if h.is_closed:
            plan.append((h, None, None, None))
            continue
        s = start if start is not None else h.start_time
        e = end if end is not None else h.end_time
        l = None if clear_last else (last if last is not None else h.last_entry)
        if s >= e:
            errors.append(f"{_row_name(h)}: the start time would not be before the end time")
        elif l is not None and not s <= l <= e:
            errors.append(f"{_row_name(h)}: the last entry would be outside the opening hours")
        plan.append((h, s, e, l))
    if errors:
        return 0, errors

    for h, s, e, l in plan:
        if not h.is_closed:
            h.start_time, h.end_time, h.last_entry = s, e, l
        if notes:
            h.notes = notes
    return len(plan), []
