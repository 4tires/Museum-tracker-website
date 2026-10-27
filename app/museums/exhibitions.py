"""Which exhibitions are current and which belong in the museum's archive.

An exhibition is archived once its end date is before today. Permanent
exhibitions (no end date) and open-ended ones never expire; upcoming ones
(start date in the future) still count as current. The museum page, the
archive page and the ticket grid all use is_archived(), so they cannot
disagree about what is still on.
"""

from dataclasses import dataclass, field
from datetime import date


def is_archived(exhibition, today: date) -> bool:
    return exhibition.end_date is not None and exhibition.end_date < today


def exhibition_sort_key(e):
    # Permanent first, then temporary by start date (undated first), then name.
    return (not e.is_permanent, e.start_date or date.min, e.name)


@dataclass
class ExhibitionSplit:
    permanent: list = field(default_factory=list)
    temporary: list = field(default_factory=list)
    archived: list = field(default_factory=list)

    @property
    def has_current(self) -> bool:
        return bool(self.permanent or self.temporary)


def split_exhibitions(exhibitions, today: date) -> ExhibitionSplit:
    # Sorting happens here (not in Jinja) because many exhibitions have no
    # start_date, and sorting None against dates raises a TypeError.
    result = ExhibitionSplit()
    for e in sorted(exhibitions, key=exhibition_sort_key):
        if is_archived(e, today):
            result.archived.append(e)
        elif e.is_permanent:
            result.permanent.append(e)
        else:
            result.temporary.append(e)
    # Archive: most recently ended first.
    result.archived.sort(key=lambda e: e.end_date, reverse=True)
    return result
