"""Seed script.

Run with:
    python seed.py            # add seed data (skips anything that already exists)
    python seed.py --reset    # drop and recreate all tables first, then seed
"""
import sys
from datetime import date

from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import Museum, User, Visit, VisitStatus


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
    return instance


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
    museums = [
        {
            "name": "Museu do Aljube – Resistência e Liberdade",
            "city": "Lisbon",
            "country": "Portugal",
            "description": "Situado na antiga prisão do Aljube que, entre 1928 e 1965, funcionou como cárcere político do Estado Novo, tem como missão a preservação da memória do combate à ditadura e daqueles que lutaram pela liberdade e democracia.",
            "website": "https://www.museudoaljube.pt/en/",
            "image_url": "https://europeanmemories.net/wp-content/uploads/sites/19/2016/09/images.png"
        },
        {
            "name": "Museu Nacional dos Coches",
            "city": "Lisbon",
            "country": "Portugal",
            "description": "O Museu Nacional dos Coches reúne uma coleção única no mundo de viaturas de gala e de passeio dos séculos XVI a XIX, na sua maioria provenientes da Casa Real Portuguesa, a que se acrescentaram veículos vindos dos bens da Igreja e de coleções particulares.",
            "website": "https://www.mncoches.gov.pt/en",
            "image_url": "https://media.timeout.com/images/103703334/750/422/image.jpg"
        },
    ]
    result = {}
    for data in museums:
        name = data["name"]
        defaults = {k: v for k, v in data.items() if k != "name"}
        result[name] = get_or_create(Museum, name=name, defaults=defaults)
    return result


def seed_visits(users, museums):
    # Visit has a unique (user_id, museum_id) constraint, so look up by both.
    get_or_create(
        Visit,
        user_id=users["alice"].id,
        museum_id=1,
        defaults={
            "status": VisitStatus.VISITED,
            "visit_date": date(2026, 5, 1),
            "rating": 4,
            "review": "Placeholder review.",
        },
    )
    get_or_create(
        Visit,
        user_id=users["alice"].id,
        museum_id=2,
        defaults={"status": VisitStatus.WANT_TO_VISIT},
    )


def main():
    app = create_app()
    with app.app_context():
        if "--reset" in sys.argv:
            reset_db()

        users = seed_users()
        museums = seed_museums()
        # New rows have no id until they are flushed to the database.
        db.session.flush()
        seed_visits(users, museums)

        db.session.commit()
        print("Seeding done.")


if __name__ == "__main__":
    main()