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
              residency, student, age) and how long it is valid for (a day
              ticket and a year ticket are different rows) ...
              ... followed by a "Special access" group: tickets that depend on
              a date or time (first Monday of the month, Sundays until 14:00,
              public holidays). They sit in the same columns, so it is clear
              which exhibitions they cover.

Passes
    A pass-linked ticket is a row named after the pass. Its cell never shows
    the pass's own prices: "Included in pass" when the ticket is free with
    it, or the museum's discounted ticket price.

Badges (only for what differs from the museum's usual ticket)
    Each museum has a baseline: its most common validity ("daily" or
    "period") and its most common entry policy (anytime / recommended /
    timed_slot). The baseline is also written once above the grid
    (TicketsView.norm_validity / norm_entry), so readers know what "usual"
    means.
    Nothing is written for tickets that match the baseline; a
    ticket that deviates gets a badge, shown where it is always the same:
      * validity -> on the row (it is part of what makes the row a row);
      * entry policy -> on the column header if every ticket in that column
        has it, else on the row if every ticket in that row has it, else on
        the price itself.

Visibility rules
    * Only exhibitions that are not archived count (see exhibitions.py).
    * A ticket with no links to a current exhibition is not shown at all:
      either it has no links (a data error to fix) or everything it covered
      has been archived.
    * A year-round ticket applies in every season, so when seasonal prices
      exist it is repeated in each seasonal grid. If a seasonal ticket
      covers the same audience and exhibitions, the seasonal one wins.
"""

from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from .exhibitions import exhibition_sort_key, is_archived
from .hours import rule_text
from .periods import period_of, period_sort_key, period_text

CURRENCY_SYMBOLS = {"EUR": "€"}

# Tickets valid for up to this many hours count as day tickets ("24h pass").
DAILY_MAX_HOURS = 24
UNIT_HOURS = {"hours": 1, "days": 24, "months": 730, "years": 8760}

POLICY_LABELS = {
    "anytime": "🎟️ Anytime",
    "recommended": "📅 Booking recommended",
    "timed_slot": "⏱️ Timed",
}


# --- What the template receives -------------------------------------------

@dataclass
class Entry:
    price: str            # "€15.00", "Free", "Included in pass"
    label: str            # the stored ticket label (shown only if a cell has several)
    notes: str = ""       # ticket notes (+ pass price notes), shown as a "?" tooltip
    policy: str = "anytime"   # entry policy; used to decide where its badge goes
    badge: str = ""       # entry-policy badge, only when it isn't shown on the row/column


@dataclass
class Column:
    title: str                 # "All exhibitions", "Weight-Counter-Weight", ...
    includes: list[str]        # exhibition names, only when the column covers several
    badge: str = ""            # "⏱️ Timed" when every ticket in the column has it


@dataclass
class TicketRow:
    audience: str                         # "Full price", "Ages 65+", "Lisboa Card"
    cells: list[Optional[list[Entry]]]    # one per column; None = not sold
    notes: str = ""                       # the pass's notes, for pass rows
    badge: str = ""                       # "🗓️ 1 year", "⏱️ Timed", or both


@dataclass
class RuleRow:
    label: str                            # "First Monday of the month"
    when: str                             # "First Monday of the month · 10:00–14:00"
    who: str                              # "Municipality residents" or ""
    cells: list[Optional[list[Entry]]]    # one per column; only the covered one is set
    badge: str = ""


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
    norm_validity: str = ""   # the museum's usual validity, shown above the grid ("Single entry")
    norm_entry: str = ""      # the museum's usual way in ("Walk in, no booking needed")

    @property
    def has_norm(self) -> bool:
        return bool(self.norm_validity or self.norm_entry)

    @property
    def is_empty(self) -> bool:
        return not self.schedules


@dataclass(frozen=True)
class Baseline:
    """What counts as 'usual' for one museum."""
    validity: str = "daily"          # "daily" or "period"
    policy: str = "anytime"          # an entry_policy value
    multi_duration: bool = False     # more than one period length is sold
    daily_kind: str = "single_entry" # usual kind of day ticket: single_entry or same_day
    period: Optional[tuple] = None   # the one period length ('period', value, unit), if only one is sold


# --- Validity and entry policy ---------------------------------------------

def _enum_value(x):
    """Enum member -> its value; plain strings (and None) pass through."""
    return getattr(x, "value", x)


def _ticket_policy(t) -> str:
    return _enum_value(t.entry_policy) or "anytime"


def _validity_key(t) -> tuple:
    """('daily', None, None) or ('period', value, unit).

    single_entry and same_day are both 'daily'. A period of 24 hours or less
    (a "24h pass") is also treated as a day ticket.
    """
    if (_enum_value(t.validity) or "single_entry") != "period":
        return ("daily", None, None)
    value = t.validity_value or 1
    unit = _enum_value(t.validity_unit) or "days"
    if value * UNIT_HOURS.get(unit, 24) <= DAILY_MAX_HOURS:
        return ("daily", None, None)
    return ("period", value, unit)


def _duration_hours(key: tuple) -> int:
    if key[0] == "daily":
        return 0
    return key[1] * UNIT_HOURS.get(key[2], 24)


def _duration_text(value: int, unit: str) -> str:
    """(1, 'years') -> '1 year'; (6, 'months') -> '6 months'."""
    unit = unit[:-1] if value == 1 and unit.endswith("s") else unit
    return f"{value} {unit}"


def _validity_badge(t, baseline: Baseline) -> str:
    key = _validity_key(t)
    if key[0] == baseline.validity and not (key[0] == "period" and baseline.multi_duration):
        return ""
    if key[0] == "period":
        return f"🗓️ {_duration_text(key[1], key[2])}"
    validity = _enum_value(t.validity) or "single_entry"
    if validity == "period":     # a 24h pass, shown as a day ticket
        return f"🎟️ {_duration_text(t.validity_value or 1, _enum_value(t.validity_unit) or 'days')}"
    return "🎟️ Same day" if validity == "same_day" else "🎟️ Single entry"


def _policy_label(policy: str) -> str:
    return POLICY_LABELS.get(policy, policy)


def _most_common(counter: Counter, default: str) -> str:
    """Most common value; on a tie, the default wins."""
    if not counter:
        return default
    top = max(counter.values())
    tied = [value for value, count in counter.items() if count == top]
    return default if default in tied else sorted(tied)[0]


def _compute_baseline(priced: list, rules: list) -> Baseline:
    """The museum's usual validity and entry policy.

    Counted over what is actually shown, and each distinct ticket once: a
    ticket repeated for summer and winter is one ticket, not two.
    Rule tickets (free Sundays, ...) only count if nothing else is sold.
    """
    source = priced or rules
    validities, policies, daily_kinds, seen = Counter(), Counter(), Counter(), set()
    for t, ids in source:
        policy = _ticket_policy(t)
        identity = (_audience_key(t), ids, policy)
        if identity in seen:
            continue
        seen.add(identity)
        group = _validity_key(t)[0]
        validities[group] += 1
        policies[policy] += 1
        if group == "daily":
            kind = _enum_value(t.validity) or "single_entry"
            # A 24h pass (period, normalized to daily) is valid for the day.
            daily_kinds["same_day" if kind == "period" else kind] += 1

    period_lengths = {_validity_key(t) for t, _ in priced + rules if _validity_key(t)[0] == "period"}
    return Baseline(
        validity=_most_common(validities, "daily"),
        policy=_most_common(policies, "anytime"),
        multi_duration=len(period_lengths) > 1,
        daily_kind=_most_common(daily_kinds, "single_entry"),
        period=next(iter(period_lengths)) if len(period_lengths) == 1 else None,
    )


NORM_POLICY_TEXT = {
    "anytime": "Walk in, no booking needed",
    "recommended": "Booking recommended",
    "timed_slot": "Book a time slot in advance",
}


def _norm_validity_text(baseline: Baseline) -> str:
    """The usual validity in words: 'Single entry', 'Valid for 1 year', ..."""
    if baseline.validity == "period":
        if baseline.period:
            return f"Valid for {_duration_text(baseline.period[1], baseline.period[2])}"
        return "Valid for a set period"
    if baseline.daily_kind == "same_day":
        return "Valid for one day"
    return "Single entry"


def _norm_entry_text(baseline: Baseline) -> str:
    return NORM_POLICY_TEXT.get(baseline.policy, baseline.policy)


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
    # Validity is part of the key: a day ticket and a year ticket for the same
    # audience are different rows. Entry policy is not: it is shown as a badge.
    return (
        _validity_key(t), t.pass_id, t.resident_country, t.resident_municipality,
        t.min_age, t.max_age, bool(t.is_student),
    )


def _audience_sort_key(t) -> tuple:
    # Day tickets first, then period tickets; inside each group:
    # full price, age groups, students, residents, passes.
    vkey = _validity_key(t)
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
    return (
        0 if vkey[0] == "daily" else 1,
        rank,
        t.min_age or 0,
        t.max_age if t.max_age is not None else 999,
        audience_text(t),
        _duration_hours(vkey),   # same audience: 1 month before 1 year
    )


# --- Coverage (what the ticket gives access to) ------------------------------

def _set_title(ids: frozenset, current: list) -> str:
    all_ids = frozenset(e.id for e in current)
    by_id = {e.id: e for e in current}

    if ids == all_ids:
        return "All exhibitions"
    if len(ids) == 1:
        return by_id[next(iter(ids))].name

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


def _entry_notes(t, include_pass: bool = False) -> str:
    """Ticket notes; include_pass also adds the pass's own notes."""
    parts = [t.notes]
    if include_pass and t.museum_pass:
        parts.append(t.museum_pass.notes)
    return "\n".join(dict.fromkeys(p for p in parts if p))


def _price_text(t) -> str:
    """What the ticket costs at this museum.

    A pass is never priced here (what the pass itself costs belongs to the
    pass): the cell says "Included in pass", or shows the museum's discounted
    ticket price when the pass only gives a reduction.
    """
    if t.price == 0:
        return "Included in pass" if t.pass_id else "Free"
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


def _entry(t, include_pass: bool = False) -> Entry:
    return Entry(
        price=_price_text(t),
        label=t.label,
        notes=_entry_notes(t, include_pass=include_pass),
        policy=_ticket_policy(t),
    )


# --- Placing the entry-policy badges ---------------------------------------------

def _join_badges(*parts: str) -> str:
    return " · ".join(p for p in parts if p)


def _uniform_deviation(entries: list, baseline_policy: str) -> Optional[str]:
    """The policy shared by every entry, if it is the same and not the baseline."""
    policies = {e.policy for e in entries}
    if len(policies) == 1:
        policy = next(iter(policies))
        if policy != baseline_policy:
            return policy
    return None


def _place_policy_badges(columns: list, rows: list, rule_rows: list, baseline_policy: str) -> None:
    """Put each deviating entry policy where it is always the same.

    Column first (if every ticket in the column has it), then the row (if
    every ticket in the row has it and the columns don't already say so),
    and otherwise on the price itself. Changes the objects in place.
    """
    all_rows = [*rows, *rule_rows]

    column_policy = []
    for j, column in enumerate(columns):
        entries = [e for row in all_rows for e in (row.cells[j] or [])]
        policy = _uniform_deviation(entries, baseline_policy)
        column_policy.append(policy)
        if policy:
            column.badge = _policy_label(policy)

    for row in all_rows:
        placed = [(j, e) for j, cell in enumerate(row.cells) for e in (cell or [])]
        row_policy = _uniform_deviation([e for _, e in placed], baseline_policy)
        # Redundant if every one of its tickets already sits under a column badge.
        if row_policy and all(column_policy[j] == row_policy for j, _ in placed):
            row_policy = None
        if row_policy:
            row.badge = _join_badges(row.badge, _policy_label(row_policy))

        for j, entry in placed:
            shown = entry.policy in (baseline_policy, row_policy, column_policy[j])
            if not shown:
                entry.badge = _policy_label(entry.policy)


# --- Building the grids ---------------------------------------------------------

def _schedule(period: tuple, items: list, rules: list, current: list, position: dict, baseline: Baseline) -> Schedule:
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
                [_entry(t) for t, _ in sorted(entries, key=lambda e: e[0].price)]
                if entries else None
            )
        rows.append(TicketRow(
            audience=audience_text(sample),
            cells=row_cells,
            notes=(sample.museum_pass.notes or "") if sample.museum_pass else "",
            badge=_validity_badge(sample, baseline),
        ))

    rule_rows = []
    for t, ids in rules:
        who = audience_text(t)
        rule_rows.append(RuleRow(
            label=t.label,
            # No period here: the selected button already says it.
            when=" · ".join(p for p in (rule_text(t), _time_window(t)) if p),
            who="" if who == "Full price" else who,
            cells=[[_entry(t, include_pass=True)] if s == ids else None for s in sets],
            badge=_validity_badge(t, baseline),
        ))

    columns = [_column(ids, current) for ids in sets]
    _place_policy_badges(columns, rows, rule_rows, baseline.policy)

    return Schedule(
        title="All year" if year_round else period_text(*period),
        is_year_round=year_round,
        columns=columns,
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

    # One baseline per museum, so the badges don't change between seasons.
    baseline = _compute_baseline(priced, rule_rows)

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
                current, position, baseline,
            ))
    elif year_round or year_round_rules:
        schedules.append(_schedule(
            (None, None, None, None), year_round, year_round_rules, current, position, baseline,
        ))

    if not schedules:
        return TicketsView()
    return TicketsView(
        schedules=schedules,
        norm_validity=_norm_validity_text(baseline),
        norm_entry=_norm_entry_text(baseline),
    )