"""Helpers for yearly date periods (month/day to month/day, no wrapping).

A period like "1 Apr – 31 Aug" is stored as four columns on the row
(month_from, day_from, month_to, day_to) and repeats every year. A row with all
four empty is "year-round". These helpers are shared by anything that groups
rows by period: opening hours today, ticket prices later.
"""

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def period_of(row) -> tuple:
    """The row's period as a hashable key: (month_from, day_from, month_to, day_to)."""
    return (row.month_from, row.day_from, row.month_to, row.day_to)


def period_text(month_from, day_from, month_to, day_to) -> str:
    """'1 Apr – 31 Aug', 'Feb – Mar', 'Feb', or '' for a year-round row."""
    if month_from is None or month_to is None:
        return ""                                    # year-round
    if day_from is None or day_to is None:
        if month_from == month_to:
            return MONTHS[month_from - 1]            # "Feb"
        return f"{MONTHS[month_from - 1]} – {MONTHS[month_to - 1]}"
    return f"{day_from} {MONTHS[month_from - 1]} – {day_to} {MONTHS[month_to - 1]}"


def period_sort_key(period: tuple):
    """Year-round first, then by start date through the year, then by end date.

    Tuples containing None can't be compared with tuples containing numbers,
    so None is turned into a flag plus zeros.
    """
    month_from, day_from, month_to, day_to = period
    return (
        month_from is not None, # False when the period is all year / True when the period is seasonal 
        month_from or 0,
        day_from or 0,
        month_to or 0,
        day_to or 0)