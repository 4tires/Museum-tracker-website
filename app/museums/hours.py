"""Display logic for a museum's opening hours.

The database stores one flat list of OpeningHours rows. The museum page shows
three different things, so this module sorts the rows into three groups:

    regular   -> a weekday and times, optionally limited to a yearly period
                 (e.g. 1 Apr – 31 Aug), and nothing else: no specific date,
                 holiday or Nth-week rule, and not flagged is_special. Rows are
                 grouped by period, and each period becomes one Mon-Sun table
                 (one button on the page). A plain "closed every Monday" row
                 also lives here and shows as "Closed".
    closures  -> is_closed = True plus any other qualifier. e.g. 25 Dec, public
                 holidays, "closed 1 Feb – 15 Feb every year".
    special   -> everything else: open-hours overrides such as "first Thursday
                 of the month, open until 22:00", or a weekly row flagged
                 is_special ("Late Thursday").

Every row lands in exactly one group, so nothing is silently dropped.
There is no date logic: rows stay on the page until they are changed or
deleted in the database, and periods never wrap the new year (a winter
schedule that crosses 1 Jan is stored as two periods).
"""

from dataclasses import dataclass, field
from datetime import time
from typing import Iterable, Optional

from .periods import period_of, period_sort_key, period_text

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
ORDINALS = {1: "First", 2: "Second", 3: "Third", 4: "Fourth", 5: "Fifth", -1: "Last"}


# --- What the template receives -------------------------------------------

@dataclass
class Slot:
    hours: str        # "10:00–18:00", or "Closed"
    last_entry: str   # "17:30", or "" if none


@dataclass
class DayHours:
    day: str
    slots: list[Slot]  # one per opening period of the day (a lunch break gives two); [] = "not listed"


@dataclass
class Schedule:
    title: str            # button label: "1 Apr – 31 Aug", or "All year"
    is_year_round: bool
    days: list[DayHours]  # always seven, Monday to Sunday


@dataclass
class SpecialRow:
    label: str        # "Late Thursday" or ""
    when: str         # "First Thursday of the month"
    period: str       # "1 Apr – 31 Aug" or ""
    hours: str        # "10:00–22:00"
    last_entry: str   # "21:30" or ""
    notes: str


@dataclass
class Closure:
    when: str         # "25 Dec", "1 Feb – 15 Feb", "Public holidays"
    label: str
    notes: str


@dataclass
class OpeningHoursView:
    regular: list[Schedule] = field(default_factory=list)
    special: list[SpecialRow] = field(default_factory=list)
    closures: list[Closure] = field(default_factory=list)

    @property
    def has_regular(self) -> bool:
        return any(d.slots for s in self.regular for d in s.days)

    @property
    def is_empty(self) -> bool:
        return not (self.has_regular or self.special or self.closures)


# --- Formatting helpers ----------------------------------------------------

def _fmt_hours(h) -> tuple[str, str]:
    # Always returns (hours, last_entry), so callers can unpack it safely.
    if h.is_closed:
        return "Closed", ""
    hours = f"{h.start_time:%H:%M}–{h.end_time:%H:%M}"
    last_entry = f"{h.last_entry:%H:%M}" if h.last_entry else ""
    return hours, last_entry


def _recurrence(h) -> Optional[str]:
    """Which recurring pattern a row follows (without its period), or None."""
    if h.holidays:
        return "Public holidays"
    if h.month and h.day:
        return f"{h.day} {MONTHS[h.month - 1]}"
    if h.weekday is not None and h.week_of_month:
        return f"{ORDINALS[h.week_of_month]} {WEEKDAYS[h.weekday]} of the month"
    if h.weekday is not None:
        return f"Every {WEEKDAYS[h.weekday]}"
    return None


def rule_text(h) -> str:
    return _recurrence(h) or "Special schedule"


def closure_when(h) -> str:
    # A closure is a pattern, a period, or both.
    parts = [p for p in (_recurrence(h), period_text(*period_of(h))) if p]
    return " · ".join(parts) or "Closed"


# --- Classification and sorting --------------------------------------------

def _is_weekly_schedule(h) -> bool:
    """A weekday, optionally within a yearly period, and nothing else."""
    return (
        h.weekday is not None
        and h.week_of_month is None
        and h.month is None
        and h.day is None
        and not h.holidays
    )


def _start(h) -> time:
    # start_time is NULL on closed rows; time.min (00:00) keeps sorting from crashing.
    return h.start_time or time.min


def _special_sort_key(h):
    return (
        h.weekday if h.weekday is not None else 9,
        h.week_of_month or 0,
        period_sort_key(period_of(h)),
        _start(h),
    )


def _closure_sort_key(h):
    # Calendar order: annual date or period start; holidays and the rest last.
    if h.month and h.day:
        return (h.month, h.day)
    if h.month_from:
        return (h.month_from, h.day_from or 0)
    return (13, 0)


# --- Entry point -----------------------------------------------------------

def build_opening_hours(rows: Iterable) -> OpeningHoursView:
    # Sort OpeningHours rows into regular / special / closures for display.
    by_period: dict[tuple, dict[int, list]] = {}
    special_rows, closure_rows = [], []

    for h in rows:
        if h.is_closed and not _is_weekly_schedule(h):
            closure_rows.append(h)
        elif _is_weekly_schedule(h) and not h.is_special:
            days = by_period.setdefault(period_of(h), {i: [] for i in range(7)})
            days[h.weekday].append(h)
        else:
            special_rows.append(h)

    regular = []
    for period in sorted(by_period, key=period_sort_key):
        year_round = period[0] is None
        regular.append(Schedule(
            title="All year" if year_round else period_text(*period),
            is_year_round=year_round,
            days=[
                DayHours(WEEKDAYS[i], [Slot(*_fmt_hours(h)) for h in sorted(by_period[period][i], key=_start)])
                for i in range(7)
            ],
        ))

    special = []
    for h in sorted(special_rows, key=_special_sort_key):
        hours, last_entry = _fmt_hours(h)
        special.append(SpecialRow(
            label=h.label or "",
            when=rule_text(h),
            period=period_text(*period_of(h)),
            hours=hours,
            last_entry=last_entry,
            notes=h.notes or "",
        ))

    closures = [
        Closure(when=closure_when(h), label=h.label or "", notes=h.notes or "")
        for h in sorted(closure_rows, key=_closure_sort_key)
    ]
    return OpeningHoursView(regular=regular, special=special, closures=closures)