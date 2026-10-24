"""Seed script.

Run with:
    python seed.py            # add seed data (skips anything that already exists)
    python seed.py --reset    # drop and recreate all tables first, then seed
"""
import sys
import csv
from pathlib import Path
from datetime import date, time, datetime
from decimal import Decimal

from werkzeug.security import generate_password_hash

from app.models import (Museum, User, Exhibition, MuseumVisit, MuseumReview, MuseumWishlist, ExhibitionVisit,
                        ExhibitionReview, ExhibitionWishlist, MuseumPass, PassPrice, Ticket, DurationUnit, Weekday,
                        OpeningHours,)
from app import create_app, db

# Database Logic
def reset_db():
    """Wipe all tables. Fine for early development with SQLite.

    Note: create_all() bypasses Alembic, so the alembic_version table is not
    touched. If you want the schema to come from migrations, delete museums.db
    and run `flask db upgrade` instead of using --reset.
    """
    db.drop_all()
    db.create_all()


def get_or_create(model, defaults=None, **lookup):
    """Return an existing row matching `lookup`, or create it.
    Keeps the script safe to run more than once."""
    instance = db.session.execute(
        db.select(model).filter_by(**lookup)
    ).scalar_one_or_none()
    if instance:
        return instance
    instance = model(**lookup, **(defaults or {}))
    db.session.add(instance)
    db.session.flush()
    return instance

# CSV Logic
DATA_DIR = Path(__file__).parent / "seed_data"

def read_rows(filename):
    with open(DATA_DIR / filename, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f, delimiter=";"):
            # Empty cell -> None, so nullable columns stay NULL
            yield {k: (v.strip() or None) for k, v in row.items()}

def parse_bool(v):
    return v is not None and v.lower() in {"1", "true", "yes"}

def parse_date(v):
    return datetime.strptime(v, "%d/%m/%Y").date() if v else None

def parse_int(v):
    return int(v) if v else None

def parse_time(v):
    return time.fromisoformat(v) if v else None

def parse_decimal(v):
    return Decimal(v.replace(",", "."))

# Seed functions
def seed_users():
    # Development-only passwords. Never reuse these anywhere real.
    admin = get_or_create(
        User,
        username="admin",
        defaults={
            "first_name": "admin",
            "last_name": "admin",
            "email": "admin@example.com",
            "password_hash": generate_password_hash("change-me"),
            "is_admin": True,
        },
    )
    alice = get_or_create(
        User,
        username="alice",
        defaults={
            "first_name": "Alice",
            "last_name": "Ficticio",
            "email": "alice@example.com",
            "password_hash": generate_password_hash("change-me"),
        },
    )
    return {"admin": admin, "alice": alice}

def seed_museums():
    result = {}
    for row in read_rows("museums.csv"):
        name, city = row.pop("name"), row.pop("city")
        result[(name, city)] = get_or_create(
            Museum, name=name, city=city, defaults=row
        )
    return result

def seed_museum_visits(users, museums):
    # Visit has a unique (user_id, museum_id, visit_date) constraint, so look up by both.
    museum = museums[("Museu do Aljube – Resistência e Liberdade", "Lisbon")]

    get_or_create(
        MuseumVisit,
        user_id=users["alice"].id,
        museum_id=museum.id,
        visit_date=date(2026, 5, 1)
    )

def seed_museum_wishs(users, museums):
    # Wish has a unique (user_id, museum_id) constraint, so look up by both.
    museum = museums[("Museu Nacional dos Coches", "Lisbon")]

    get_or_create(
        MuseumWishlist,
        user_id=users["alice"].id,
        museum_id=museum.id,
    )

def seed_museum_reviews(users, museums):
    # Review has a unique (user_id, museum_id) constraint, so look up by both.
    museum = museums[("Museu do Aljube – Resistência e Liberdade", "Lisbon")]

    get_or_create(
        MuseumReview,
        user_id=users["alice"].id,
        museum_id=museum.id,
        defaults={
            "rating": 4,
            "review": "Great collection, go early to avoid the crowds."
        }
    )

def seed_exhibitions(museums):
    result = {}
    for row in read_rows("exhibitions.csv"):
        museum = museums[(row["museum_name"], row["museum_city"])]

        row.pop("museum_name")
        row.pop("museum_city")

        name = row.pop("exhibition_name")

        row["is_permanent"] = parse_bool(row["is_permanent"])
        row["start_date"] = parse_date(row["start_date"])
        row["end_date"] = parse_date(row["end_date"])

        result[(museum.id, name)] = get_or_create(
            Exhibition, museum_id=museum.id, name=name, defaults=row
        )
    return result

def seed_exhibition_visits(users, exhibitions):
    # Visit has a unique (user_id, exhibition_id, visit_date) constraint, so look up by both.
    get_or_create(
        ExhibitionVisit,
        user_id=users["alice"].id,
        exhibition_id=1,
        visit_date=date(2026, 5, 1)
    )

def seed_exhibition_wishs(users, exhibitions):
    # Wish has a unique (user_id, exhibition_id) constraint, so look up by both.
    get_or_create(
        ExhibitionWishlist,
        user_id=users["alice"].id,
        exhibition_id=2,
    )

def seed_exhibition_reviews(users, exhibitions):
    # Review has a unique (user_id, exhibition_id) constraint, so look up by both.
    get_or_create(
        ExhibitionReview,
        user_id=users["alice"].id,
        exhibition_id=1,
        defaults={
            "rating": 4,
            "review": "Great collection, go early to avoid the crowds."
        }
    )

def seed_museum_pass():
    result = {}
    for row in read_rows("museum_passes.csv"):
        name = row.pop("name")
        result[name] = get_or_create(
            MuseumPass, name=name, defaults=row
        )
    return result

def seed_pass_prices(museum_passes):
    for row in read_rows("pass_prices.csv"):
        museum_pass = museum_passes[row.pop("pass_name")]
        label = row.pop("label")

        row["duration_unit"] = DurationUnit[row["duration_unit"]]
        row["duration_value"] = int(row["duration_value"])
        row["price"] = parse_decimal(row["price"])
        row["min_age"] = parse_int(row["min_age"])
        row["max_age"] = parse_int(row["max_age"])
        row["is_student"] = parse_bool(row["is_student"])
        if not row["currency"]:
            del row["currency"]   # let the model default ("EUR") apply

        get_or_create(
            PassPrice,
            pass_id=museum_pass.id,
            label=label,
            defaults=row,
        )

def seed_tickets(museums, museum_passes):
    result = {}
    for row in read_rows("tickets.csv"):
        museum = museums[(row["museum_name"], row["museum_city"])]

        row.pop("museum_name")
        row.pop("museum_city")

        label = row.pop("label")

        pass_name = row.pop("pass_name", None)
        row["pass_id"] = museum_passes[pass_name].id if pass_name else None

        row["price"] = parse_decimal(row["price"])
        row["min_age"] = parse_int(row["min_age"])
        row["max_age"] = parse_int(row["max_age"])
        row["is_student"] = parse_bool(row["is_student"])

        row["weekday"] = Weekday[row["weekday"]] if row["weekday"] else None
        row["week_of_month"] = parse_int(row["week_of_month"])
        row["start_time"] = parse_time(row["start_time"])
        row["end_time"] = parse_time(row["end_time"])
        row["month"] = parse_int(row["month"])
        row["day"] = parse_int(row["day"])
        row["holidays"] = parse_bool(row["holidays"])

        row["month_from"] = parse_int(row["month_from"])
        row["day_from"] = parse_int(row["day_from"])
        row["month_to"] = parse_int(row["month_to"])
        row["day_to"] = parse_int(row["day_to"])

        result[(museum.id, label)] = get_or_create(Ticket, museum_id=museum.id, label=label, defaults=row)

    return result

def seed_ticket_exhibition(tickets, exhibitions, museums):
    for row in read_rows("ticket_exhibition.csv"):
        museum = museums[(row["museum_name"], row["museum_city"])]
        ticket = tickets[(museum.id, row["ticket_label"])]
        exhibition = exhibitions[(museum.id, row["exhibition_name"])]

        if exhibition not in ticket.exhibitions:
            ticket.exhibitions.append(exhibition)

def seed_opening_hours(museums):
    result = {}
    for row in read_rows("opening_hours.csv"):
        museum = museums[(row["museum_name"], row["museum_city"])]

        row.pop("museum_name")
        row.pop("museum_city")

        row["is_special"] = parse_bool(row["is_special"])
        row["is_closed"] = parse_bool(row["is_closed"])
        row["weekday"] = Weekday[row["weekday"]] if row["weekday"] else None
        row["start_time"] = parse_time(row["start_time"])
        row["end_time"] = parse_time(row["end_time"])
        row["last_entry"] = parse_time(row["last_entry"])
        row["week_of_month"] = parse_int(row["week_of_month"])
        row["month"] = parse_int(row["month"])
        row["day"] = parse_int(row["day"])
        row["holidays"] = parse_bool(row["holidays"])
        row["month_from"] = parse_int(row["month_from"])
        row["day_from"] = parse_int(row["day_from"])
        row["month_to"] = parse_int(row["month_to"])
        row["day_to"] = parse_int(row["day_to"])

        get_or_create(OpeningHours, museum_id=museum.id, **row)

    return result

def main():
    app = create_app()
    with app.app_context():
        if "--reset" in sys.argv:
            reset_db()

        users = seed_users()
        museums = seed_museums()
        exhibitions = seed_exhibitions(museums)
        museum_passes = seed_museum_pass()
        tickets = seed_tickets(museums, museum_passes)
        seed_museum_visits(users, museums)
        seed_museum_wishs(users, museums)
        seed_museum_reviews(users, museums)
        seed_exhibition_visits(users, exhibitions)
        seed_exhibition_wishs(users, exhibitions)
        seed_exhibition_reviews(users, exhibitions)
        seed_pass_prices(museum_passes)
        seed_ticket_exhibition(tickets, exhibitions, museums)
        seed_opening_hours(museums)

        db.session.commit()
        print("Seeding done.")

if __name__ == "__main__":
    main()