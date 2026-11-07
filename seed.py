"""Seed the development database from CSV fixtures.

Run from the project root:
    python seed.py            # create missing rows; safe to re-run
    python seed.py --reset    # drop/recreate tables, then seed everything

CSV files live in ./seed_data and use semicolons as delimiters. Dates use DD/MM/YYYY.
An optional users.csv adds extra demo accounts on top of the built-in admin/alice accounts.
The included CSV rows are illustrative development fixtures, not authoritative museum data.
"""

import sys
import csv
from pathlib import Path
from datetime import date, time, datetime
from decimal import Decimal

from werkzeug.security import generate_password_hash

from app.models import (
    Museum, User, Exhibition, MuseumVisit, MuseumReview, MuseumWishlist,
    ExhibitionVisit, ExhibitionReview, ExhibitionWishlist, MuseumPass,
    PassPrice, Ticket, DurationUnit, Weekday, EntryPolicy, Validity,
    OpeningHours, Audioguide, AudioguideType, Language, GuidedVisit,
)
from app import create_app, db


DATA_DIR = Path(__file__).parent / "seed_data"
PERIOD_FIELDS = ("month_from", "day_from", "month_to", "day_to")


def reset_db():
    """Drop and recreate all tables (intended for local development only)."""
    db.drop_all()
    db.create_all()


def get_or_create(model, defaults=None, **lookup):
    """Return an existing row matching lookup or create it and flush its ID."""
    instance = db.session.execute(
        db.select(model).filter_by(**lookup)
    ).scalar_one_or_none()
    if instance is not None:
        return instance

    instance = model(**lookup, **(defaults or {}))
    db.session.add(instance)
    db.session.flush()
    return instance


def read_rows(filename):
    """Yield clean rows from a semicolon-delimited UTF-8 CSV file."""
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Seed CSV not found: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        for line_number, row in enumerate(csv.DictReader(csv_file, delimiter=";"), start=2):
            if not row or all(value is None or not value.strip() for value in row.values()):
                continue
            if None in row:
                raise ValueError(f"Too many values in {filename}, line {line_number}.")
            yield {key.strip(): (value.strip() or None) for key, value in row.items()}


def require(mapping, key, description):
    try:
        return mapping[key]
    except KeyError as exc:
        raise ValueError(f"Unknown {description}: {key!r}. Check the corresponding seed CSV reference.") from exc


def parse_bool(value):
    return value is not None and value.strip().lower() in {"1", "true", "yes", "y"}


def parse_optional_bool(value):
    return None if value is None else parse_bool(value)


def parse_date(value):
    if not value:
        return None
    for date_format in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            pass
    raise ValueError(f"Invalid date {value!r}; use DD/MM/YYYY.")


def parse_int(value):
    return int(value) if value is not None else None


def parse_time(value):
    return time.fromisoformat(value) if value else None


def parse_decimal(value):
    return Decimal(value.replace(",", ".")) if value is not None else None


def parse_enum(enum_type, value):
    if value is None:
        return None
    try:
        return enum_type[value.strip()]
    except KeyError:
        try:
            return enum_type(value.strip())
        except ValueError as exc:
            allowed = ", ".join(member.name for member in enum_type)
            raise ValueError(f"Invalid {enum_type.__name__} value {value!r}; use one of: {allowed}.") from exc


def parse_weekday(value):
    """Convert a weekday label (MONDAY) or integer to the model's 0-6 value."""
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return Weekday[value.strip().upper()].value


def seed_users():
    """Create development accounts; change these credentials before any real use."""
    shared_password_hash = generate_password_hash("change-me")

    admin = get_or_create(
        User,
        username="admin",
        defaults={
            "first_name": "Admin",
            "last_name": "Demo",
            "email": "admin@example.com",
            "password_hash": shared_password_hash,
            "is_admin": True,
            "birth_date": date(1980, 1, 1),
            "is_student": False,
            "resident_country": "Portugal",
            "resident_municipality": "Lisbon",
        },
    )
    alice = get_or_create(
        User,
        username="alice",
        defaults={
            "first_name": "Alice",
            "last_name": "Demo",
            "email": "alice@example.com",
            "password_hash": shared_password_hash,
            "is_admin": False,
            "birth_date": date(1995, 6, 15),
            "is_student": False,
            "resident_country": "Portugal",
            "resident_municipality": "Lisbon",
        },
    )
    users = {"admin": admin, "alice": alice}

    # Optional extra demo accounts from users.csv (same shared password).
    if (DATA_DIR / "users.csv").exists():
        for row in read_rows("users.csv"):
            username = row.pop("username")
            row["is_admin"] = parse_bool(row.get("is_admin"))
            row["is_student"] = parse_bool(row.get("is_student"))
            row["birth_date"] = parse_date(row.get("birth_date"))
            row["password_hash"] = shared_password_hash
            users[username] = get_or_create(User, username=username, defaults=row)

    return users


def seed_museums():
    museums = {}
    for row in read_rows("museums.csv"):
        name = row.pop("name")
        city = row.pop("city")
        row["has_lockers"] = parse_optional_bool(row.get("has_lockers"))
        museums[(name, city)] = get_or_create(
            Museum, name=name, city=city, defaults=row
        )
    return museums


def seed_languages():
    languages = {}
    for row in read_rows("languages.csv"):
        code = row.pop("code")
        languages[code] = get_or_create(Language, code=code, defaults=row)
    return languages


def seed_exhibitions(museums):
    exhibitions = {}
    for row in read_rows("exhibitions.csv"):
        museum_key = (row.pop("museum_name"), row.pop("museum_city"))
        museum = require(museums, museum_key, "museum")
        name = row.pop("exhibition_name")
        row["is_permanent"] = parse_bool(row.get("is_permanent"))
        row["start_date"] = parse_date(row.get("start_date"))
        row["end_date"] = parse_date(row.get("end_date"))
        row["typical_duration_minutes"] = parse_int(row.get("typical_duration_minutes"))

        exhibitions[(museum.id, name)] = get_or_create(
            Exhibition, museum_id=museum.id, name=name, defaults=row
        )
    return exhibitions


def seed_museum_passes():
    passes = {}
    for row in read_rows("museum_passes.csv"):
        name = row.pop("name")
        row["includes_transport"] = parse_bool(row.get("includes_transport"))
        passes[name] = get_or_create(MuseumPass, name=name, defaults=row)
    return passes


def seed_pass_prices(museum_passes):
    for row in read_rows("pass_prices.csv"):
        pass_name = row.pop("pass_name")
        museum_pass = require(museum_passes, pass_name, "museum pass")
        label = row.pop("label")
        duration_unit = parse_enum(DurationUnit, row.pop("duration_unit"))
        duration_value = parse_int(row.pop("duration_value"))

        row["price"] = parse_decimal(row.get("price"))
        row["min_age"] = parse_int(row.get("min_age"))
        row["max_age"] = parse_int(row.get("max_age"))
        row["is_student"] = parse_bool(row.get("is_student"))
        if row.get("currency") is None:
            row.pop("currency", None)  # use the model's EUR default

        get_or_create(
            PassPrice,
            pass_id=museum_pass.id,
            label=label,
            duration_unit=duration_unit,
            duration_value=duration_value,
            defaults=row,
        )


def seed_tickets(museums, museum_passes):
    tickets = {}
    for row in read_rows("tickets.csv"):
        museum_key = (row.pop("museum_name"), row.pop("museum_city"))
        museum = require(museums, museum_key, "museum")
        label = row.pop("label")
        pass_name = row.pop("pass_name", None)
        museum_pass = require(museum_passes, pass_name, "museum pass") if pass_name else None

        row["pass_id"] = museum_pass.id if museum_pass else None
        row["price"] = parse_decimal(row.get("price"))
        row["min_age"] = parse_int(row.get("min_age"))
        row["max_age"] = parse_int(row.get("max_age"))
        row["is_student"] = parse_bool(row.get("is_student"))
        row["entry_policy"] = parse_enum(EntryPolicy, row.get("entry_policy")) or EntryPolicy.anytime
        row["validity"] = parse_enum(Validity, row.get("validity")) or Validity.single_entry
        row["validity_value"] = parse_int(row.get("validity_value"))
        row["validity_unit"] = parse_enum(DurationUnit, row.get("validity_unit"))
        row["weekday"] = parse_weekday(row.get("weekday"))
        row["week_of_month"] = parse_int(row.get("week_of_month"))
        row["start_time"] = parse_time(row.get("start_time"))
        row["end_time"] = parse_time(row.get("end_time"))
        row["month"] = parse_int(row.get("month"))
        row["day"] = parse_int(row.get("day"))
        row["holidays"] = parse_bool(row.get("holidays"))

        period = {field: parse_int(row.pop(field)) for field in PERIOD_FIELDS}
        if row.get("currency") is None:
            row.pop("currency", None)

        ticket = get_or_create(
            Ticket,
            museum_id=museum.id,
            label=label,
            **period,
            defaults=row,
        )
        tickets[(museum.id, label, tuple(period.values()))] = ticket
    return tickets


def seed_ticket_exhibitions(tickets, exhibitions, museums):
    """Link tickets to exhibitions, optionally limiting a link to a ticket's season."""
    tickets_by_label = {}
    for (museum_id, label, period), ticket in tickets.items():
        tickets_by_label.setdefault((museum_id, label), []).append((period, ticket))

    for row in read_rows("ticket_exhibition.csv"):
        museum_key = (row["museum_name"], row["museum_city"])
        museum = require(museums, museum_key, "museum")
        exhibition_key = (museum.id, row["exhibition_name"])
        exhibition = require(exhibitions, exhibition_key, "exhibition")
        wanted_period = tuple(parse_int(row.get(field)) for field in PERIOD_FIELDS)
        candidates = tickets_by_label.get((museum.id, row["ticket_label"]), [])
        linked = 0
        for period, ticket in candidates:
            if wanted_period != (None, None, None, None) and period != wanted_period:
                continue
            if exhibition not in ticket.exhibitions:
                ticket.exhibitions.append(exhibition)
            linked += 1
        if not linked:
            raise ValueError(
                f"No ticket matched {row['ticket_label']!r} for {museum_key!r} "
                f"and period {wanted_period!r}. Check ticket_exhibition.csv."
            )


def seed_opening_hours(museums):
    for row in read_rows("opening_hours.csv"):
        museum_key = (row.pop("museum_name"), row.pop("museum_city"))
        museum = require(museums, museum_key, "museum")
        row["weekday"] = parse_weekday(row.get("weekday"))
        for field in ("week_of_month", "month", "day", *PERIOD_FIELDS):
            row[field] = parse_int(row.get(field))
        for field in ("start_time", "end_time", "last_entry"):
            row[field] = parse_time(row.get(field))
        for field in ("holidays", "is_closed", "is_special"):
            row[field] = parse_bool(row.get(field))

        # OpeningHours has no declared natural-key constraint, so compare all supplied values.
        get_or_create(OpeningHours, museum_id=museum.id, **row)


def link_once(table_name, **values):
    """Insert a many-to-many row only when that exact pair does not exist."""
    table = db.metadata.tables[table_name]
    conditions = [table.c[column] == value for column, value in values.items()]
    existing = db.session.execute(db.select(table).where(*conditions)).first()
    if existing is None:
        db.session.execute(table.insert().values(**values))


def seed_museum_languages(museums, languages):
    for row in read_rows("museum_languages.csv"):
        museum_key = (row["museum_name"], row["museum_city"])
        museum = require(museums, museum_key, "museum")
        language = require(languages, row["language_code"], "language")
        link_once("museum_language", museum_id=museum.id, language_id=language.id)


def seed_audioguides(museums):
    audioguides = {}
    for row in read_rows("audioguides.csv"):
        museum_key = (row.pop("museum_name"), row.pop("museum_city"))
        museum = require(museums, museum_key, "museum")
        audioguide_type = parse_enum(AudioguideType, row.pop("audioguide_type"))
        row["requires_own_headphones"] = parse_bool(row.get("requires_own_headphones"))
        row["deposit_required"] = parse_bool(row.get("deposit_required"))
        row["price"] = parse_decimal(row.get("price"))
        if row.get("currency") is None:
            row.pop("currency", None)

        audioguide = get_or_create(
            Audioguide,
            museum_id=museum.id,
            audioguide_type=audioguide_type,
            defaults=row,
        )
        audioguides[(museum.id, audioguide_type)] = audioguide
    return audioguides


def seed_audioguide_languages(audioguides, museums, languages):
    for row in read_rows("audioguide_languages.csv"):
        museum_key = (row["museum_name"], row["museum_city"])
        museum = require(museums, museum_key, "museum")
        audioguide_type = parse_enum(AudioguideType, row["audioguide_type"])
        audioguide = require(audioguides, (museum.id, audioguide_type), "audioguide")
        language = require(languages, row["language_code"], "language")
        if language not in audioguide.languages:
            audioguide.languages.append(language)


def guided_visit_key(museum_id, name, weekday, week_of_month, month, day, holidays, start_time):
    return (museum_id, name, weekday, week_of_month, month, day, holidays, start_time)


def seed_guided_visits(museums, exhibitions):
    guided_visits = {}
    for row in read_rows("guided_visits.csv"):
        museum_key = (row.pop("museum_name"), row.pop("museum_city"))
        museum = require(museums, museum_key, "museum")
        exhibition_name = row.pop("exhibition_name")
        exhibition = None
        if exhibition_name:
            exhibition = require(exhibitions, (museum.id, exhibition_name), "exhibition")
        name = row.pop("name")

        lookup = {
            "museum_id": museum.id,
            "name": name,
            "weekday": parse_weekday(row.pop("weekday")),
            "week_of_month": parse_int(row.pop("week_of_month")),
            "month": parse_int(row.pop("month")),
            "day": parse_int(row.pop("day")),
            "holidays": parse_bool(row.pop("holidays")),
            "start_time": parse_time(row.pop("start_time")),
        }
        row["exhibition_id"] = exhibition.id if exhibition else None
        row["duration_minutes"] = parse_int(row.get("duration_minutes"))
        row["max_participants"] = parse_int(row.get("max_participants"))
        row["price"] = parse_decimal(row.get("price"))
        row["end_time"] = parse_time(row.get("end_time"))
        for field in PERIOD_FIELDS:
            row[field] = parse_int(row.get(field))
        row["requires_reservation"] = parse_bool(row.get("requires_reservation"))
        if row.get("currency") is None:
            row.pop("currency", None)

        guided_visit = get_or_create(GuidedVisit, defaults=row, **lookup)
        key = guided_visit_key(*lookup.values())
        guided_visits[key] = guided_visit
    return guided_visits


def seed_guided_visit_languages(guided_visits, museums, languages):
    for row in read_rows("guided_visit_languages.csv"):
        museum_key = (row["museum_name"], row["museum_city"])
        museum = require(museums, museum_key, "museum")
        key = guided_visit_key(
            museum.id,
            row["guided_visit_name"],
            parse_weekday(row.get("weekday")),
            parse_int(row.get("week_of_month")),
            parse_int(row.get("month")),
            parse_int(row.get("day")),
            parse_bool(row.get("holidays")),
            parse_time(row.get("start_time")),
        )
        guided_visit = require(guided_visits, key, "guided visit")
        language = require(languages, row["language_code"], "language")
        if language not in guided_visit.languages:
            guided_visit.languages.append(language)


def seed_museum_visits(users, museums):
    for row in read_rows("museum_visits.csv"):
        user = require(users, row["username"], "user")
        museum = require(museums, (row["museum_name"], row["museum_city"]), "museum")
        get_or_create(
            MuseumVisit,
            user_id=user.id,
            museum_id=museum.id,
            visit_date=parse_date(row["visit_date"]),
        )


def seed_museum_wishlists(users, museums):
    for row in read_rows("museum_wishlist.csv"):
        user = require(users, row["username"], "user")
        museum = require(museums, (row["museum_name"], row["museum_city"]), "museum")
        get_or_create(MuseumWishlist, user_id=user.id, museum_id=museum.id)


def seed_museum_reviews(users, museums):
    for row in read_rows("museum_reviews.csv"):
        user = require(users, row["username"], "user")
        museum = require(museums, (row["museum_name"], row["museum_city"]), "museum")
        get_or_create(
            MuseumReview,
            user_id=user.id,
            museum_id=museum.id,
            defaults={"rating": parse_int(row.get("rating")), "review": row.get("review")},
        )


def seed_exhibition_visits(users, museums, exhibitions):
    for row in read_rows("exhibition_visits.csv"):
        user = require(users, row["username"], "user")
        museum = require(museums, (row["museum_name"], row["museum_city"]), "museum")
        exhibition = require(exhibitions, (museum.id, row["exhibition_name"]), "exhibition")
        get_or_create(
            ExhibitionVisit,
            user_id=user.id,
            exhibition_id=exhibition.id,
            visit_date=parse_date(row["visit_date"]),
            defaults={"duration_minutes": parse_int(row.get("duration_minutes"))},
        )


def seed_exhibition_wishlists(users, museums, exhibitions):
    for row in read_rows("exhibition_wishlist.csv"):
        user = require(users, row["username"], "user")
        museum = require(museums, (row["museum_name"], row["museum_city"]), "museum")
        exhibition = require(exhibitions, (museum.id, row["exhibition_name"]), "exhibition")
        get_or_create(ExhibitionWishlist, user_id=user.id, exhibition_id=exhibition.id)


def seed_exhibition_reviews(users, museums, exhibitions):
    for row in read_rows("exhibition_reviews.csv"):
        user = require(users, row["username"], "user")
        museum = require(museums, (row["museum_name"], row["museum_city"]), "museum")
        exhibition = require(exhibitions, (museum.id, row["exhibition_name"]), "exhibition")
        get_or_create(
            ExhibitionReview,
            user_id=user.id,
            exhibition_id=exhibition.id,
            defaults={"rating": parse_int(row.get("rating")), "review": row.get("review")},
        )


def main():
    app = create_app()
    with app.app_context():
        try:
            if "--reset" in sys.argv:
                reset_db()
            else:
                db.create_all()

            # Parent rows first: users, museums, languages, exhibitions and passes.
            users = seed_users()
            museums = seed_museums()
            languages = seed_languages()
            exhibitions = seed_exhibitions(museums)
            museum_passes = seed_museum_passes()

            # Dependent ticket/pass data.
            seed_pass_prices(museum_passes)
            tickets = seed_tickets(museums, museum_passes)
            seed_ticket_exhibitions(tickets, exhibitions, museums)

            # Museum facilities and many-to-many relationships.
            seed_opening_hours(museums)
            seed_museum_languages(museums, languages)
            audioguides = seed_audioguides(museums)
            seed_audioguide_languages(audioguides, museums, languages)
            guided_visits = seed_guided_visits(museums, exhibitions)
            seed_guided_visit_languages(guided_visits, museums, languages)

            # User activity comes last because it references users and catalogue rows.
            seed_museum_visits(users, museums)
            seed_museum_wishlists(users, museums)
            seed_museum_reviews(users, museums)
            seed_exhibition_visits(users, museums, exhibitions)
            seed_exhibition_wishlists(users, museums, exhibitions)
            seed_exhibition_reviews(users, museums, exhibitions)

            db.session.commit()
            print("Seeding done.")
        except Exception:
            db.session.rollback()
            raise


if __name__ == "__main__":
    main()