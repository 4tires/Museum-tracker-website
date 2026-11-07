"""Display logic for audioguides and guided visits.

Same idea as hours.py and tickets.py: the database stores plain rows, and this
module turns them into what the museum / exhibition pages show. Nothing here
is stored, and there is no database access (the caller loads the rows).

Guided visits
    A guided visit follows the same schedule columns as opening hours
    (weekday, Nth week of the month, annual date, holidays, yearly period), so
    the "when" text reuses rule_text() and period_text(). A visit linked to an
    archived exhibition is hidden, like its tickets (see exhibitions.py).
"""

from dataclasses import dataclass
from datetime import date
from typing import Iterable

from .exhibitions import is_archived
from .hours import rule_text
from .periods import period_of, period_sort_key, period_text
from .tickets import _money, _time_window

AUDIOGUIDE_LABELS = {
    "smartphone_app": "Smartphone app",
    "web_qr": "Web page (QR code)",
    "physical_device": "Device loaned at the museum",
}


# --- What the template receives -------------------------------------------

@dataclass
class AudioguideRow:
    kind: str             # "Smartphone app"
    price: str            # "Free", "€3.00"
    details: list[str]    # ["Bring your own headphones", "Deposit required"]
    languages: str        # "Portuguese, English" or ""
    notes: str


@dataclass
class GuidedVisitRow:
    name: str
    exhibition_id: int | None     # for the link; None = whole museum
    exhibition_name: str
    when: str                     # "Every Saturday · 11:00–12:00"
    period: str                   # "1 Apr – 30 Sep" or ""
    duration: str                 # "1 h 30 min"
    price: str                    # "Free", "€5.00", "Price not listed"
    details: list[str]            # ["Reservation required", "Up to 15 people"]
    languages: str
    description: str
    notes: str


# --- Formatting helpers ----------------------------------------------------

def _languages(languages) -> str:
    return ", ".join(sorted(lang.name for lang in languages))


def _price(amount, currency) -> str:
    if amount is None:
        return "Price not listed"
    if amount == 0:
        return "Free"
    return _money(amount, currency)


def duration_text(minutes: int) -> str:
    hours, rest = divmod(minutes, 60)
    if hours and rest:
        return f"{hours} h {rest} min"
    if hours:
        return f"{hours} h"
    return f"{rest} min"


# --- Entry points ----------------------------------------------------------

def build_audioguides(audioguides: Iterable) -> list[AudioguideRow]:
    rows = []
    for a in sorted(audioguides, key=lambda a: a.audioguide_type.value):
        details = []
        if a.requires_own_headphones:
            details.append("Bring your own headphones")
        if a.deposit_required:
            details.append("Deposit required")
        rows.append(AudioguideRow(
            kind=AUDIOGUIDE_LABELS.get(a.audioguide_type.value, a.audioguide_type.value),
            price=_price(a.price, a.currency),
            details=details,
            languages=_languages(a.languages),
            notes=a.notes or "",
        ))
    return rows


def _visit_sort_key(g):
    return (
        g.weekday if g.weekday is not None else 9,
        g.week_of_month or 0,
        period_sort_key(period_of(g)),
        g.start_time,
    )


def build_guided_visits(guided_visits: Iterable, today: date) -> list[GuidedVisitRow]:
    rows = []
    for g in sorted(guided_visits, key=_visit_sort_key):
        if g.exhibition and is_archived(g.exhibition, today):
            continue
        details = []
        if g.requires_reservation:
            details.append("Reservation required")
        if g.max_participants:
            details.append(f"Up to {g.max_participants} people")
        rows.append(GuidedVisitRow(
            name=g.name,
            exhibition_id=g.exhibition.id if g.exhibition else None,
            exhibition_name=g.exhibition.name if g.exhibition else "",
            when=" · ".join(p for p in (rule_text(g), _time_window(g)) if p),
            period=period_text(*period_of(g)),
            duration=duration_text(g.duration_minutes),
            price=_price(g.price, g.currency),
            details=details,
            languages=_languages(g.languages),
            description=g.description or "",
            notes=g.notes or "",
        ))
    return rows
