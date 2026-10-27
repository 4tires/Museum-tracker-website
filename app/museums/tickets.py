"""Display logic for a museum's tickets.

Mirrors hours.py: the database stores one flat list of Ticket rows, and this
module turns it into what the museum page shows. Nothing here is stored.

What the page shows
    One price grid per yearly period (a "Summer" / "Winter" button, using the
    same month_from/day_from/month_to/day_to columns as opening hours). With no
    seasonal rows there is a single "All year" grid.

    Columns = what the ticket gives access to (derived from the set of
              exhibitions linked in ticket_exhibition).
    Rows    = who the ticket is for (derived from the audience columns: pass,
              residency, student, age) ...
              ... followed by a "Special access" group: tickets that depend on
              a date or time (first Monday of the month, Sundays until 14:00,
              public holidays). They sit in the same columns, so it is clear
              which exhibitions they cover.

Visibility rules
    * Only exhibitions that are not archived count (see exhibitions.py).
    * A ticket with no links to a current exhibition is not shown at all:
      either it has no links (a data error to fix) or everything it covered
      has been archived.
    * A year-round ticket applies in every season, so when seasonal prices
      exist it is repeated in each seasonal grid. If a seasonal ticket
      covers the same audience and exhibitions, the seasonal one wins.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from .exhibitions import exhibition_sort_key, is_archived
from .hours import rule_text
from .periods import period_of, period_sort_key, period_text

CURRENCY_SYMBOLS = {"EUR": "€"}


# --- What the template receives -------------------------------------------

@dataclass
class Entry:
    price: str         # "€15.00", "Free", "Included in pass"
    label: str         # the stored ticket label (shown only if a cell has several)


@dataclass
class Column:
    title: str                 # "All exhibitions", "Weight-Counter-Weight", ...
    includes: list[str]        # exhibition names, only when the column covers several


@dataclass
class TicketRow:
    audience: str                         # "Full price", "Ages 65+", "Lisboa Card"
    cells: list[Optional[list[Entry]]]    # one per column; None = not sold


@dataclass
class RuleRow:
    label: str                            # "First Monday of the month"
    when: str                             # "First Monday of the month · 10:00–14:00"
    who: str                              # "Municipality residents" or ""
    cells: list[Optional[list[Entry]]]    # one per column; only the covered one is set


@dataclass
class Schedule:
    title: str            # button label: "1 Apr – 30 Sep", or "All year"
    is_year_round: bool
    columns: list[Column]
    rows: list[TicketRow]
    rule_rows: list[RuleRow]


@dataclass
class TicketsView:
    schedules: list[Schedule] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.schedules


# --- Audience (who the ticket is for) --------------------------------------

def _age_phrase(min_age, max_age) -> str:
    if min_age is not None and max_age is not None:
        return f"{min_age}–{max_age}"
    if min_age is not None:
        return f"{min_age}+"
    if max_age is not None:
        return f"up to {max_age}"
    return ""


def _residency(t) -> str:
    # The museum already tells which municipality / country, so no name is shown.
    if t.resident_municipality:
        return "Municipality residents"
    if t.resident_country:
        return "Country residents"
    return ""


def audience_text(t) -> str:
    """'Full price', 'Ages 13–18', 'Student, ages up to 25', 'Lisboa Card', ..."""
    if t.pass_id and t.museum_pass:
        return t.museum_pass.name
    parts = []
    if t.is_student:
        parts.append("Student")
    if _residency(t):
        parts.append(_residency(t))
    age = _age_phrase(t.min_age, t.max_age)
    if age:
        parts.append(f"ages {age}")
    if not parts:
        return "Full price"
    text = ", ".join(parts)
    return text[0].upper() + text[1:]


def _audience_key(t) -> tuple:
    return (
        t.pass_id, t.resident_country, t.resident_municipality,
        t.min_age, t.max_age, bool(t.is_student),
    )


def _audience_sort_key(t) -> tuple:
    # Full price, then age groups, students, residents, passes.
    if t.pass_id:
        rank = 4
    elif _residency(t):
        rank = 3
    elif t.is_student:
        rank = 2
    elif t.min_age is not None or t.max_age is not None:
        rank = 1
    else:
        rank = 0
    return (rank, t.min_age or 0, t.max_age if t.max_age is not None else 999, audience_text(t))


# --- Coverage (what the ticket gives access to) ------------------------------

def _set_title(ids: frozenset, current: list) -> str:
    all_ids = frozenset(e.id for e in current)
    by_id = {e.id: e for e in current}
    if len(ids) == 1:
        return by_id[next(iter(ids))].name
    if ids == all_ids:
        return "All exhibitions"
    permanent = frozenset(e.id for e in current if e.is_permanent)
    temporary = all_ids - permanent
    if ids == temporary:
        return "All temporary exhibitions"
    if ids == permanent:
        return "Permanent exhibitions"
    names = [e.name for e in current if e.id in ids]
    return " + ".join(names)


def _column(ids: frozenset, current: list) -> Column:
    names = [e.name for e in current if e.id in ids]
    return Column(title=_set_title(ids, current), includes=names if len(ids) > 1 else [])


# --- Formatting helpers ------------------------------------------------------

def _money(amount, currency) -> str:
    symbol = CURRENCY_SYMBOLS.get(currency)
    text = f"{amount:.2f}"
    return f"{symbol}{text}" if symbol else f"{text} {currency}"


def _pass_price_text(t) -> str:
    """The pass's own prices ("Adult €30.00 · Young €15.00 · ..."), or "".

    Only when all of the pass's prices share one duration (a one-day combined
    ticket). A pass sold for 24h / 48h / 72h (Lisboa Card) is too long for a
    cell, so it returns "" and the caller falls back to "Included in pass".
    """
    prices = list(t.museum_pass.prices) if t.museum_pass else []
    if len({(p.duration_value, p.duration_unit) for p in prices}) != 1:
        return ""
    prices.sort(key=lambda p: p.price, reverse=True)
    return " · ".join(f"{p.label} {_money(p.price, p.currency)}" for p in prices)


def _price_text(t) -> str:
    if t.price == 0:
        if t.pass_id:
            return _pass_price_text(t) or "Included in pass"
        return "Free"
    return _money(t.price, t.currency)


def _time_window(t) -> str:
    if t.start_time and t.end_time:
        return f"{t.start_time:%H:%M}–{t.end_time:%H:%M}"
    if t.end_time:
        return f"until {t.end_time:%H:%M}"
    if t.start_time:
        return f"from {t.start_time:%H:%M}"
    return ""


def _is_rule(t) -> bool:
    return t.weekday is not None or t.month is not None or bool(t.holidays)


# --- Building the grids ---------------------------------------------------------

def _schedule(period: tuple, items: list, rules: list, current: list, position: dict, today: date) -> Schedule:
    # items: (ticket, exhibition_ids, is_seasonal); rules: (ticket, exhibition_ids)
    year_round = period[0] is None

    cells: dict[tuple, list] = {}
    for t, ids, seasonal in items:
        cells.setdefault((_audience_key(t), ids), []).append((t, seasonal))
    # A seasonal ticket overrides a year-round one for the same cell.
    for key, entries in cells.items():
        if any(s for _, s in entries):
            cells[key] = [(t, s) for t, s in entries if s]

    sets = sorted(
        {ids for _, ids, _ in items} | {ids for _, ids in rules},
        key=lambda s: (-len(s), tuple(sorted(position[i] for i in s))),
    )

    audiences: dict[tuple, object] = {}
    for t, _, _ in items:
        audiences.setdefault(_audience_key(t), t)

    rows = []
    for key, sample in sorted(audiences.items(), key=lambda kv: _audience_sort_key(kv[1])):
        row_cells = []
        for ids in sets:
            entries = cells.get((key, ids))
            row_cells.append(
                [Entry(_price_text(t), t.label) for t, _ in sorted(entries, key=lambda e: e[0].price)]
                if entries else None
            )
        rows.append(TicketRow(audience=audience_text(sample), cells=row_cells))

    rule_rows = []
    for t, ids in rules:
        who = audience_text(t)
        rule_rows.append(RuleRow(
            label=t.label,
            # No period here: the selected button already says it.
            when=" · ".join(p for p in (rule_text(t), _time_window(t)) if p),
            who="" if who == "Full price" else who,
            cells=[[Entry(_price_text(t), t.label)] if s == ids else None for s in sets],
        ))

    return Schedule(
        title="All year" if year_round else period_text(*period),
        is_year_round=year_round,
        columns=[_column(ids, current) for ids in sets],
        rows=rows,
        rule_rows=rule_rows,
    )


def build_tickets(tickets, exhibitions, today: date) -> TicketsView:
    """Sort a museum's Ticket rows into price grids.

    `exhibitions` is the museum's full exhibition list (archived ones are
    filtered out here); `today` is passed in so the function stays pure.
    """
    current = sorted(
        (e for e in exhibitions if not is_archived(e, today)),
        key=exhibition_sort_key,
    )
    position = {e.id: i for i, e in enumerate(current)}

    priced, rule_rows = [], []
    for t in tickets:
        ids = frozenset(e.id for e in t.exhibitions if e.id in position)
        if not ids:
            continue   # no links, or only archived exhibitions: not shown
        (rule_rows if _is_rule(t) else priced).append((t, ids))

    # Group by yearly period. Year-round rows apply in every period.
    seasonal: dict[tuple, list] = {}
    year_round = []
    for t, ids in priced:
        period = period_of(t)
        if period[0] is None:
            year_round.append((t, ids, False))
        else:
            seasonal.setdefault(period, []).append((t, ids, True))

    rules_by_period: dict[tuple, list] = {}
    year_round_rules = []
    for t, ids in rule_rows:
        period = period_of(t)
        if period[0] is None:
            year_round_rules.append((t, ids))
        else:
            rules_by_period.setdefault(period, []).append((t, ids))

    schedules = []
    periods = sorted(set(seasonal) | set(rules_by_period), key=period_sort_key)
    if periods:
        for period in periods:
            schedules.append(_schedule(
                period,
                year_round + seasonal.get(period, []),
                year_round_rules + rules_by_period.get(period, []),
                current, position, today,
            ))
    elif year_round or year_round_rules:
        schedules.append(_schedule(
            (None, None, None, None), year_round, year_round_rules, current, position, today,
        ))

    return TicketsView(schedules=schedules)